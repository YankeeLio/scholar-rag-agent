"""agent.py: lightweight Task-Planning Agent over the local research library.

The agent receives a natural-language request and may call a small set of
tools (function calling) before producing the final answer:

  - search_library   : hybrid retrieval over the local document library
  - list_documents   : list documents currently in the library
  - get_citation_graph: citation graph nodes/edges

Events are yielded as dicts so the HTTP layer can stream them as SSE:
  plan / tool_call / tool_result / delta / done / error
"""
from __future__ import annotations

import json
from typing import Any, Iterator

from app import llm, config

SYSTEM_PROMPT = (
    "你是一个科研助手 Agent，可以调用工具来完成用户的请求。规则：\n"
    "1. 回答基于工具返回的证据，禁止编造；证据不足时明确说明。\n"
    "2. 一次请求最多调用 3 次工具；拿到足够信息后直接组织答案。\n"
    "3. 引用证据时标注来源标题与章节，格式如《标题》§章节。\n"
    "4. 用与用户相同的语言回答。"
)

TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "search_library",
            "description": "在本地文献库中做语义+关键词混合检索，返回最相关的文本片段（含出处）。"
                           "当用户询问库内论文/教材中的具体事实、方法、超参数、结论时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "检索问题或关键词"},
                    "top_k": {"type": "integer", "description": "返回片段数，默认 5", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_documents",
            "description": "列出当前文献库中的所有文档（标题、块数）。当用户问“我库里有哪些文献”时使用。",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_citation_graph",
            "description": "获取库内文档之间的引用关系图谱（节点与边）。当用户问“谁引用谁、引用关系、基石论文”时使用。",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_docs",
            "description": "跨论文对比：对同一问题在每篇文档中分别检索证据，按来源分组返回。"
                           "当用户问“这几篇论文在某个点上有什么异同/对比”时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "要对比的问题或主题"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_arxiv",
            "description": "从 arXiv 公开 API 检索相关论文（标题、摘要、作者、链接）。"
                           "当用户问“推荐相关文献、最近有什么进展、这个方向还有哪些论文”时使用。"
                           "用于外部文献推荐，不依赖本地库。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "检索关键词或主题，建议用英文术语"},
                    "max_results": {"type": "integer", "description": "返回条数，默认 5", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
]


def _exec_tool(name: str, args: dict, ctx: dict) -> dict:
    """Dispatch one tool call. ctx carries shared singletons (retriever, idx)."""
    if name == "search_library":
        hits = ctx["retriever"].search(args.get("query", ""),
                                       top_k=int(args.get("top_k", 5)))
        out = []
        for h in hits:
            m = h["metadata"]
            out.append({
                "source": m.get("title", ""),
                "section": m.get("section", ""),
                "page": m.get("pages", ""),
                "text": h["text"][:1200],
            })
        return {"hits": out, "count": len(out)}

    if name == "list_documents":
        res = ctx["idx"].collection.get(include=["metadatas"])
        docs: dict[str, dict] = {}
        for m in res["metadatas"]:
            e = docs.setdefault(m["doc_id"], {"title": m["title"], "chunks": 0})
            e["chunks"] += 1
        return {"documents": list(docs.values())}

    if name == "get_citation_graph":
        from app.graph import build_graph
        g = build_graph(ctx["idx"])
        return {"nodes": g["nodes"], "edges": g["edges"], "summary": g.get("summary", {})}

    if name == "compare_docs":
        # broad retrieval, then group by doc_id so the LLM sees per-source evidence
        query = args.get("query", "")
        hits = ctx["retriever"].search(query, top_k=10)
        grouped: dict[str, dict] = {}
        for h in hits:
            m = h["metadata"]
            did = m.get("doc_id", "?")
            slot = grouped.setdefault(did, {"title": m.get("title", ""), "evidence": []})
            slot["evidence"].append({
                "section": m.get("section", ""),
                "page": m.get("pages", ""),
                "text": h["text"][:800],
            })
        return {"query": query, "by_doc": list(grouped.values())}

    if name == "fetch_arxiv":
        import urllib.request
        import urllib.parse
        import xml.etree.ElementTree as ET
        query = args.get("query", "")
        max_r = int(args.get("max_results", 5))
        url = ("http://export.arxiv.org/api/query?"
               + urllib.parse.urlencode({
                   "search_query": f"all:{query}",
                   "start": 0,
                   "max_results": max_r,
                   "sortBy": "relevance",
               }))
        req = urllib.request.Request(url, headers={"User-Agent": "ScholarRAG/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml_text = resp.read().decode("utf-8")
        ns = {"a": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(xml_text)
        papers = []
        for entry in root.findall("a:entry", ns):
            title = (entry.find("a:title", ns).text or "").strip().replace("\n", " ")
            summary = (entry.find("a:summary", ns).text or "").strip().replace("\n", " ")
            authors = [a.find("a:name", ns).text for a in entry.findall("a:author", ns)]
            link = entry.find("a:id", ns).text.strip()
            published = (entry.find("a:published", ns).text or "")[:10]
            papers.append({
                "title": title,
                "authors": authors[:3],
                "published": published,
                "summary": summary[:500],
                "url": link,
            })
        return {"query": query, "papers": papers, "count": len(papers)}

    return {"error": f"unknown tool: {name}"}


def run_agent(question: str, ctx: dict) -> Iterator[dict]:
    """Run the agent loop; yields event dicts."""
    if not config.LLM_API_KEY:
        yield {"type": "error", "text": "DEEPSEEK_API_KEY 未配置"}
        return

    client = llm.get_client()
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    yield {"type": "plan", "text": "正在分析你的问题，决定需要调用哪些工具…"}

    max_loops = 5
    for loop in range(max_loops):
        resp = client.chat.completions.create(
            model=config.LLM_CHAT_MODEL,
            messages=messages,
            tools=TOOLS,
            temperature=0.2,
        )
        msg = resp.choices[0].message
        tcs = msg.tool_calls or []

        if not tcs:
            # final answer streamed (single completion; SSE deltas below)
            text = msg.content or ""
            # chunk the answer into ~40-char deltas for a streaming feel
            for i in range(0, len(text), 40):
                yield {"type": "delta", "text": text[i:i + 40]}
            yield {"type": "done", "loops": loop + 1}
            return

        # append the assistant message that requested tools
        messages.append(msg.model_dump(exclude_none=True))
        for tc in tcs:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            yield {"type": "tool_call", "name": tc.function.name, "args": args}
            result = _exec_tool(tc.function.name, args, ctx)
            summary = (f"返回 {result.get('count', len(result.get('documents', result.get('nodes', []))))} 项"
                       if tc.function.name != "get_citation_graph"
                       else f"节点 {len(result.get('nodes', []))}，边 {len(result.get('edges', []))}")
            yield {"type": "tool_result", "name": tc.function.name, "summary": summary}
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False)[:6000],
            })

    # ran out of loops: one final forced completion
    resp = client.chat.completions.create(
        model=config.LLM_CHAT_MODEL,
        messages=messages + [{"role": "user", "content": "请基于已获取的工具结果直接回答。"}],
        temperature=0.2,
    )
    text = resp.choices[0].message.content or ""
    for i in range(0, len(text), 40):
        yield {"type": "delta", "text": text[i:i + 40]}
    yield {"type": "done", "loops": max_loops}
