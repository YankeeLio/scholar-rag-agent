"""llm.py: DeepSeek chat client with evidence-grounded RAG prompt.

The QA flow retrieves top-k chunks first (indexer), then this module
builds a prompt that forces the model to answer ONLY from the supplied
evidence and to cite each claim with [n] markers. This is the core
anti-hallucination layer (Source Tracing).
"""
from __future__ import annotations

from typing import Any, Iterator

from app import config

_client: Any = None


def get_client():
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(api_key=config.LLM_API_KEY,
                         base_url=config.LLM_BASE_URL)
    return _client


SYSTEM_PROMPT = (
    "你是一个面向科研场景的 AI 助手。必须遵守以下规则：\n"
    "1. 只依据用户消息中提供的“证据片段”回答，严禁编造证据中不存在的内容。\n"
    "2. 引用证据时，在对应句子末尾标注编号，如 [1]、[2]，编号必须与证据片段编号一致。\n"
    "3. 证据不足以回答时，明确回答“证据不足，无法确定”，不要猜测或补全。\n"
    "4. 数字、超参数、硬件配置、引用信息必须与证据完全一致，不得改写。\n"
    "5. 使用提问者使用的语言回答（中文问题用中文，英文问题用英文）。"
)


def build_messages(question: str, hits: list[dict]) -> list[dict]:
    """Assemble system + user messages with numbered evidence blocks."""
    evidences: list[str] = []
    for i, h in enumerate(hits, 1):
        m = h["metadata"]
        loc = (f"{m.get('title', '')} | §{m.get('section', '')} | "
               f"p.{m.get('pages', '')} | 行 {m.get('start_line')}-{m.get('end_line')}")
        evidences.append(f"[{i}] 出处：{loc}\n{h['text'][:1500]}")
    user = ("证据片段：\n\n" + "\n\n".join(evidences) +
            f"\n\n问题：{question}\n\n"
            "请严格基于以上证据回答，并在句末标注引用编号 [n]。")
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def chat_complete(question: str, hits: list[dict],
                  model: str | None = None) -> str:
    """Non-streaming completion."""
    messages = build_messages(question, hits)
    resp = get_client().chat.completions.create(
        model=model or config.LLM_CHAT_MODEL,
        messages=messages,
        temperature=0.2,
    )
    return resp.choices[0].message.content or ""


def chat_stream(question: str, hits: list[dict],
                model: str | None = None) -> Iterator[str]:
    """Streaming completion; yields text deltas."""
    messages = build_messages(question, hits)
    stream = get_client().chat.completions.create(
        model=model or config.LLM_CHAT_MODEL,
        messages=messages,
        temperature=0.2,
        stream=True,
    )
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content
