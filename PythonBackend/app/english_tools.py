from app.tools import OpenAIWrapper
from langchain.tools import BaseTool
from pydantic import Field, BaseModel, TypeAdapter
from typing import Optional, Literal, Type, ClassVar, List, Dict, Union, Annotated


class EnglishTutorInput(BaseModel):
    question: str = Field(..., description="The SAT English question text as seen by the user.")
    passage: Optional[str] = Field(None, description="Optional passage text if provided.")

class BaseResp(BaseModel):
    kind: Literal["reading","grammar","vocabulary","clarifying", "other"]
    answer: str
    why: Optional[str] = None

class ReadingResp(BaseResp):
    kind: Literal["reading"]
    evidenceLines: Optional[List[str]]  # e.g., ["12–14", "19–20"]

class GrammarResp(BaseResp):
    kind: Literal["grammar"]
    rule: str                 # e.g., "Subject–verb agreement"

class VocabResp(BaseResp):
    kind: Literal["vocabulary"]
    contextClue: str

class ClarifyResp(BaseResp):
    kind: Literal["clarifying"]
    guidance: str
    tips: List[str] = []


TutorResponse = Annotated[
    Union[ReadingResp, GrammarResp, VocabResp, ClarifyResp],
    Field(discriminator="kind") 
]

TutorResponseAdapter = TypeAdapter(TutorResponse)

class EnglishTutorTool(BaseTool):
    """Tool for tutoring English (SAT Reading & Writing)."""
    name: str = "english_tutor"
    description: str = (
        "Answer SAT English questions. Accepts a question and an optional passage. "
        "Classifies question type (reading/grammar/vocabulary/clarifying) and returns an answer "
        "with short explanation and, if applicable, cited line spans."
    )

    model_config = {"arbitrary_types_allowed": True}

    # Your LLM wrapper (must expose .predict(prompt: str)->str and .apredict(prompt: str)->str)
    llm: OpenAIWrapper = Field(description="Language model for tutoring")
    args_schema: Type[EnglishTutorInput] = EnglishTutorInput

    def __init__(self, llm: OpenAIWrapper, **kwargs):
        super().__init__(llm=llm, **kwargs)

    # ---------- 3) Public entrypoints ----------
    def _run(self, question: str = "", passage: Optional[str] = None) -> str:
        return self._handle(question=question, passage=passage)

    # async def _arun(self, question: str = "", passage: Optional[str] = None) -> str:
    #     return await self._ahandle(question=question, passage=passage)

    # ---------- 4) Core orchestration ----------
    def _handle(self, question: str, passage: Optional[str]) -> str:
        qtype = self._classify(question, passage)
        if qtype == "reading":
            return self._answer_reading(question, passage)
        elif qtype == "grammar":
            return self._answer_grammar(question, passage)
        elif qtype == "vocabulary":
            return self._answer_vocabulary(question, passage)
        elif qtype == "clarifying":
            return self._answer_clarifying(question, passage)
        else:
            return self._answer_general(question, passage)

    async def _ahandle(self, question: str, passage: Optional[str]) -> str:
        qtype = await self._aclassify(question, passage)
        if qtype == "reading":
            return await self._aanswer_reading(question, passage)
        elif qtype == "grammar":
            return await self._aanswer_grammar(question, passage)
        elif qtype == "vocabulary":
            return await self._aanswer_vocabulary(question, passage)
        elif qtype == "clarifying":
            return await self._aanswer_clarifying(question, passage)
        else:
            return await self._aanswer_general(question, passage)

    # ---------- 5) Classification ----------
    CLASSIFY_SYS: ClassVar[str] = """You are an SAT English task router.
Decide the single best label for the user's question:
- "reading": passage-based reading comprehension (inference, detail, function, tone, evidence, main idea, purpose).
- "grammar": sentence-level errors, concision, punctuation, agreement, verb tense/aspect, modifier, parallelism, pronouns, transitions.
- "vocabulary": word-in-context or best replacement word/phrase; meaning depends on context.
- "clarifying": user is asking for help understanding instructions, strategy, or needs clarification (not asking for an answer).
- "other": anything else.

Return ONLY one of: reading | grammar | vocabulary | clarifying | other"""

    CLASSIFY_FEWSHOTS: ClassVar[List[Dict[str, Optional[str]]]] = [
        {
            "q": "Which choice best states the main purpose of the passage?",
            "p": "Passage about honeybees ...",
            "label": "reading"
        },
        {
            "q": "Choose the best version: The committee have finished their report.",
            "p": None,
            "label": "grammar"
        },
        {
            "q": "As used in line 23, 'temper' most nearly means:",
            "p": "Lines around 23 ...",
            "label": "vocabulary"
        },
        {
            "q": "What does 'best evidence' mean on the SAT?",
            "p": None,
            "label": "clarifying"
        }
    ]

    def _classify(self, question: str, passage: Optional[str]) -> Literal["reading","grammar","vocabulary","clarifying","other"]:
        user = self._render_classify_prompt(question, passage)
        prompt = self._chat(self.CLASSIFY_SYS, user)
        raw = self.llm.predict(prompt).strip().lower()
        if "reading" in raw: return "reading"
        if "grammar" in raw: return "grammar"
        if "vocabulary" in raw or "vocab" in raw: return "vocabulary"
        if "clarifying" in raw or "clarification" in raw: return "clarifying"
        return "other"

    async def _aclassify(self, question: str, passage: Optional[str]) -> str:
        user = self._render_classify_prompt(question, passage)
        prompt = self._chat(self.CLASSIFY_SYS, user)
        raw = (await self.llm.apredict(prompt)).strip().lower()
        if "reading" in raw: return "reading"
        if "grammar" in raw: return "grammar"
        if "vocabulary" in raw or "vocab" in raw: return "vocabulary"
        if "clarifying" in raw or "clarification" in raw: return "clarifying"
        return "other"

    def _render_classify_prompt(self, question: str, passage: Optional[str]) -> str:
        fewshot_block = "\n".join(
            f"Q: {fs['q']}\nP: {fs['p'] or '(no passage)'}\nLabel: {fs['label']}"
            for fs in self.CLASSIFY_FEWSHOTS
        )
        p_snippet = self._truncate_passage(passage)
        return f"""You will see a user question Q and an optional passage P.
Choose the best label. Respond with a single word label only.

Examples:
{fewshot_block}

Now classify:
Q: {question}
P: {p_snippet or '(no passage)'}"""

    # ---------- 6) Answering prompts ----------
    READ_SYS: ClassVar[str] = """You are an SAT Reading tutor. Answer concisely, cite exact line ranges, and explain why each distractor is wrong only if asked.
Format (JSON, No extra text or ``` marks):
- answer: <choice or short answer>
- evidenceLines: <line numbers or text span>
- why: <3-5 sentence rationale> (very easy to follow reasoning)
- kind: reading"""

    GRAMMAR_SYS: ClassVar[str] = """You are an SAT Writing/Grammar tutor. Explain the rule briefly, then apply it.
Format (JSON, No extra text or ``` marks):
- answer: <corrected text or choice>
- rule: <named rule, e.g., subject-verb agreement, parallelism, comma splice, modifier placement>
- why: <1-3 sentence rationale>
- kind: grammar"""

    VOCAB_SYS: ClassVar[str] = """You are an SAT Word-in-Context tutor. Prefer the meaning that fits local context.
Format (JSON, No extra text or ``` marks):
- answer: <word/choice>
- contextClue: <the phrase/surrounding text that drives meaning>
- why: <1-2 sentences>
- kind: vocabulary"""

    CLARIFY_SYS: ClassVar[str] = """You are an SAT strategy tutor. Provide a brief, practical explanation with 1-2 actionable tips.
Format (JSON, No extra text or ``` marks):
- guidance: <short explanation>
- tips: <2 bullets>
- kind: clarifying"""

    GENERAL_SYS: ClassVar[str] = """You are an SAT English tutor. Provide a helpful, concise answer with a short rationale.
Format (JSON, No extra text or ``` marks):
- answer: <...>
- why: <1-2 sentences>
- kind: other"""

    # ---- reading
    def _answer_reading(self, question: str, passage: Optional[str]) -> str:
        user = self._render_reading_prompt(question, passage)
        result = self.llm.predict(self._chat(self.READ_SYS, user)).strip()
        return result

    async def _aanswer_reading(self, question: str, passage: Optional[str]) -> str:
        user = self._render_reading_prompt(question, passage)
        result = (await self.llm.apredict(self._chat(self.READ_SYS, user))).strip()
        return result

    def _render_reading_prompt(self, question: str, passage: Optional[str]) -> str:
        p = self._prepare_passage(passage)
        return f"""Passage:
{p}

Question:
{question}

Instructions:
1) Identify the minimal lines needed to answer and ONLY use the provided passage to answer the question.
    Steps:
        1) Extract the key premise(s) from the passage.
        2) For each answer choice, check: does it FOLLOW from the premise(s) without adding new topics?
            - Reject any option that introduces new, unmentioned contrasts (e.g., “wild vs artificial,” other species, or uses of the study).
        3) Choose the single best option.
2) Provide 'answer', 'evidenceLines', 'why', and 'kind' as specified.
If choices are present, return the chosen letter and quote the exact support.
If evidenceLines is not present, return [] for evidenceLines"""

    # ---- grammar
    def _answer_grammar(self, question: str, passage: Optional[str]) -> str:
        user = self._render_grammar_prompt(question, passage)
        result = self.llm.predict(self._chat(self.GRAMMAR_SYS, user)).strip()
        return result

    async def _aanswer_grammar(self, question: str, passage: Optional[str]) -> str:
        user = self._render_grammar_prompt(question, passage)
        result = (await self.llm.apredict(self._chat(self.GRAMMAR_SYS, user))).strip()
        return result

    def _render_grammar_prompt(self, question: str, passage: Optional[str]) -> str:
        # For grammar, users often paste the sentence with options.
        p = (passage or "").strip()
        return f"""Text (may include choices or underlined portions):
{p if p else '(no extra text provided)'}

Question:
{question}

Return 'answer', 'rule', 'why', and 'kind' as JSON, no extra text or ``` marks. Prefer concise rule naming and a concrete fix."""

    # ---- vocabulary
    def _answer_vocabulary(self, question: str, passage: Optional[str]) -> str:
        user = self._render_vocab_prompt(question, passage)
        result = self.llm.predict(self._chat(self.VOCAB_SYS, user)).strip()
        return result

    async def _aanswer_vocabulary(self, question: str, passage: Optional[str]) -> str:
        user = self._render_vocab_prompt(question, passage)
        result = (await self.llm.apredict(self._chat(self.VOCAB_SYS, user))).strip()
        return result

    def _render_vocab_prompt(self, question: str, passage: Optional[str]) -> str:
        p = self._prepare_passage(passage)
        return f"""Passage:
{p}

Question:
{question}

If the question references a line number, quote the immediate context around that line as the 'contextClue'."""

    # ---- clarifying
    def _answer_clarifying(self, question: str, passage: Optional[str]) -> str:
        user = f"Question: {question}\n(If relevant) Passage snippet: {self._truncate_passage(passage)}"
        result = self.llm.predict(self._chat(self.CLARIFY_SYS, user)).strip()
        return result

    async def _aanswer_clarifying(self, question: str, passage: Optional[str]) -> str:
        user = f"Question: {question}\n(If relevant) Passage snippet: {self._truncate_passage(passage)}"
        result = (await self.llm.apredict(self._chat(self.CLARIFY_SYS, user))).strip()
        return result

    # ---- general fallback
    def _answer_general(self, question: str, passage: Optional[str]) -> str:
        user = f"Question: {question}\nPassage (optional): {self._truncate_passage(passage)}"
        result = self.llm.predict(self._chat(self.GENERAL_SYS, user)).strip()
        return result

    async def _aanswer_general(self, question: str, passage: Optional[str]) -> str:
        user = f"Question: {question}\nPassage (optional): {self._truncate_passage(passage)}"
        result = (await self.llm.apredict(self._chat(self.GENERAL_SYS, user))).strip()
        return result

    # ---------- 7) Utilities ----------
    def _chat(self, system: str, user: str) -> str:
        """Simple helper to emulate a system+user chat in a single prompt for wrappers that take one string."""
        return f"<SYSTEM>\n{system}\n</SYSTEM>\n<USER>\n{user}\n</USER>"

    def _truncate_passage(self, passage: Optional[str], max_chars: int = 3000) -> Optional[str]:
        if not passage:
            return None
        p = passage.strip()
        return (p[:max_chars] + " …") if len(p) > max_chars else p

    def _prepare_passage(self, passage: Optional[str]) -> str:
        """Add lightweight line numbers to help models cite evidence lines."""
        if not passage:
            return "(no passage provided)"
        lines = [ln.strip() for ln in passage.strip().splitlines() if ln.strip() != ""]
        numbered = [f"{i+1:>3}: {ln}" for i, ln in enumerate(lines)]
        return "\n".join(numbered)