"""translate.py: academic translation used by the linked-reading view.

Kept separate from llm.py because the contract differs: the RAG prompt
forces citation-bound answers, whereas translation must return ONLY the
translated text — no commentary, no repeated source, no hallucinated
terminology. Formulas, variable names and citation markers stay verbatim.
"""
from __future__ import annotations

from app import config
from app.llm import get_client

SYSTEM_PROMPT = (
    "你是学术论文翻译助手。必须遵守以下规则：\n"
    "1. 只输出译文本身，不要解释、不要加注、不要重复原文。\n"
    "2. 术语按各学科通用译法翻译；同一术语在本次翻译中保持一致。\n"
    "3. 公式、数学符号、变量名、引用编号（如 [12]、式 3.2）一律保持原样。\n"
    "4. 保留原文的段落结构、编号与列表层级。\n"
    "5. 无法确定的中文译名保留英文原词，不要臆造译名。"
)

_LANG_NAME = {"zh": "中文", "en": "English"}


def translate_text(text: str, target_lang: str = "zh",
                   context: str = "") -> str:
    """Translate a snippet / paragraph. Returns the译文 only."""
    ctx_line = f"文献上下文（用于术语对齐）：{context}\n\n" if context else ""
    user = (f"{ctx_line}"
            f"请把下面的内容翻译为{_LANG_NAME.get(target_lang, '中文')}：\n\n{text}")
    resp = get_client().chat.completions.create(
        model=config.LLM_CHAT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
        temperature=0.1,
    )
    return (resp.choices[0].message.content or "").strip()
