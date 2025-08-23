from app.tools import OpenAIWrapper
from langchain.tools import BaseTool
from pydantic import Field, BaseModel, TypeAdapter
from typing import Optional, Literal, Type, ClassVar, List, Dict, Union, Annotated
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import re
import json
from app.english_pipeline import split_sentences

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


class EnhancedEnglishTutorTool(EnglishTutorTool):
    """
    Complete enhanced SAT English tutor that extends your existing tool
    with ML-powered question analysis and evidence retrieval
    """

    enable_ml_features: bool = Field(default=True, description="Enable ML-powered features")
    fallback_on_error: bool = Field(default=True, description="Fallback to basic methods on error")
    
    def __init__(self, llm: OpenAIWrapper, enable_ml_features: bool = True, fallback_on_error: bool = True, **kwargs):
        # Pass the new fields to parent constructor
        super().__init__(
            llm=llm, 
            enable_ml_features=enable_ml_features,
            fallback_on_error=fallback_on_error,
            **kwargs
        )
        
        # ML models (lazy loaded)
        self._sentence_model = None
        self._qa_model = None
        
        print("Enhanced SAT English Tutor initialized")
    
    # =============================================================================
    # LAZY LOADING PROPERTIES
    # =============================================================================
    
    @property
    def sentence_model(self):
        if self._sentence_model is None and self.enable_ml_features:
            try:
                #lazy loading
                from sentence_transformers import SentenceTransformer
                self._sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
                print("✓ Sentence transformer loaded")
            except Exception as e:
                print(f"✗ Failed to load sentence model: {e}")
                if not self.fallback_on_error:
                    raise
        return self._sentence_model
    
    @property
    def qa_pipeline(self):
        if self._qa_model is None and self.enable_ml_features:
            try:
                #lazy loading
                from transformers import pipeline
                self._qa_model = pipeline(
                    "question-answering",
                    model="deepset/roberta-base-squad2",
                    tokenizer="deepset/roberta-base-squad2"
                )
                print("✓ QA pipeline loaded")
            except Exception as e:
                print(f"✗ Failed to load QA model: {e}")
                if not self.fallback_on_error:
                    raise
        return self._qa_model
    
    # =============================================================================
    # MAIN OVERRIDE METHODS
    # =============================================================================
    
    def _run(self, question: str, passage: Optional[str] = None) -> str:
        """Enhanced main entry point"""
        if self.enable_ml_features:
            try:
                return self._handle_enhanced(question, passage)
            except Exception as e:
                print(f"Enhanced processing failed: {e}")
                if self.fallback_on_error:
                    print("Falling back to basic processing")
                    return super()._run(question, passage)
                raise
        else:
            return super()._run(question, passage)
    
    def _handle_enhanced(self, question: str, passage: Optional[str]) -> str:
        """Enhanced orchestration logic"""
        print("classifying question/passage")
        print(question)
        if passage:
            print(passage)
        else:
            print("no passage")
        qtype = self._classify(question, passage)
        
        if qtype == "reading":
            return self._answer_reading_enhanced(question, passage)
        elif qtype == "grammar":
            return self._answer_grammar_enhanced(question, passage)
        elif qtype == "vocabulary" and passage:
            return self._answer_vocab_enhanced(question, passage)
        elif qtype == "clarifying":
            return self._answer_clarifying(question, passage)
        else:
            return self._answer_with_context(question, passage)
    
    # =============================================================================
    # QUESTION ANALYSIS
    # =============================================================================
    
    def _analyze_question(self, question: str) -> Dict:
        """Analyze question type and requirements"""
        prompt = f"""Analyze this SAT question and respond with JSON only:

Question: {question}

Determine:
1. question_type: main_idea|detail|inference|function|tone|evidence|vocabulary_in_context
2. info_needed: brief description of what to find
3. scope: local|broad (local = 1-3 sentences, broad = multiple paragraphs)
4. requires_reasoning: true|false

{{
    "question_type": "...",
    "info_needed": "...",
    "scope": "...",
    "requires_reasoning": ...
}}
Make sure to not add any unneccessary text or ``` marks.
"""
        
        try:
            response = self.llm.predict(prompt).strip()
            # Clean markdown if present
            if response.startswith('```'):
                response = '\n'.join(response.split('\n')[1:-1])
            return json.loads(response)
        except:
            return self._fallback_analysis(question)
    
    def _fallback_analysis(self, question: str) -> Dict:
        """Simple keyword-based analysis fallback"""
        q_lower = question.lower()
        
        if any(word in q_lower for word in ['main purpose', 'central', 'overall']):
            return {"question_type": "main_idea", "info_needed": "main theme", "scope": "broad", "requires_reasoning": True}
        elif any(word in q_lower for word in ['infer', 'suggests', 'implies']):
            return {"question_type": "inference", "info_needed": "implied meaning", "scope": "broad", "requires_reasoning": True}
        elif any(word in q_lower for word in ['function', 'serves to', 'purpose']):
            return {"question_type": "function", "info_needed": "purpose", "scope": "local", "requires_reasoning": True}
        elif any(word in q_lower for word in ['evidence', 'support']):
            return {"question_type": "evidence", "info_needed": "supporting text", "scope": "local", "requires_reasoning": False}
        elif any(word in q_lower for word in ['means', 'refers to']):
            return {"question_type": "vocabulary_in_context", "info_needed": "word meaning", "scope": "local", "requires_reasoning": False}
        else:
            return {"question_type": "detail", "info_needed": "specific info", "scope": "local", "requires_reasoning": False}
    
    # =============================================================================
    # EVIDENCE RETRIEVAL
    # =============================================================================
    
    def _retrieve_evidence(self, question: str, passage: str, analysis: Dict) -> Dict:
        """Smart evidence retrieval"""
        if analysis["scope"] == "local" and not analysis["requires_reasoning"]:
            return self._qa_retrieval(question, passage)
        else:
            return self._semantic_retrieval(question, passage, analysis)
    
    def _qa_retrieval(self, question: str, passage: str) -> Dict:
        """QA model-based retrieval for factual questions"""
        try:
            if self.qa_pipeline:
                result = self.qa_pipeline(question=question, context=passage)
                sentences = split_sentences(passage)
                
                # Find sentences containing the answer
                answer_text = result['answer']
                relevant_sentences = []
                
                for sent in sentences:
                    if answer_text.lower() in sent['text'].lower():
                        relevant_sentences.append(sent)
                
                return {
                    "sentences": relevant_sentences[:3],
                    "method": "qa_model",
                    "confidence": result['score']
                }
        except Exception as e:
            print(f"QA retrieval failed: {e}")
        
        return self._keyword_retrieval(question, passage)
    
    def _semantic_retrieval(self, question: str, passage: str, analysis: Dict) -> Dict:
        """Enhanced semantic retrieval with multiple query strategies"""
        sentences = split_sentences(passage)
        if not sentences:
            return {"sentences": [], "method": "semantic", "confidence": 0}
        
        try:
            if self.sentence_model:
                # Multiple query approaches
                queries = [
                    question,  # Original question
                    f"{question} {analysis.get('info_needed', '')}",  # Enhanced with analysis
                    self._extract_key_concepts(question),  # Key concepts only
                    self._create_contrast_query(question)  # Look for contrasts/contradictions
                ]
                
                all_scored_sentences = []
                sent_texts = [s["text"] for s in sentences]
                sent_embs = self.sentence_model.encode(sent_texts)
                
                for query in queries:
                    if query:
                        query_emb = self.sentence_model.encode([query])[0].reshape(1, -1)
                        similarities = cosine_similarity(query_emb, sent_embs)[0]
                        
                        for i, (sent, sim) in enumerate(zip(sentences, similarities)):
                            all_scored_sentences.append((sent, sim, query))
                
                # Combine and deduplicate, keeping highest scores
                sentence_scores = {}
                for sent, sim, query in all_scored_sentences:
                    sent_id = sent["id"]
                    if sent_id not in sentence_scores or sim > sentence_scores[sent_id][1]:
                        sentence_scores[sent_id] = (sent, sim)
                
                # Filter and sort
                threshold = 0.2  # Lower threshold to catch more nuance
                scored_sents = [(sent, sim) for sent, sim in sentence_scores.values() if sim > threshold]
                scored_sents.sort(key=lambda x: x[1], reverse=True)
                
                # Take more sentences to give better context
                top_sentences = [sent for sent, _ in scored_sents[:8]]  # Increased from 5
                
                return {
                    "sentences": top_sentences,
                    "method": "semantic_enhanced",
                    "confidence": float(np.mean([sim for _, sim in scored_sents[:5]]) if scored_sents else 0)
                }
        except Exception as e:
            print(f"Semantic retrieval failed: {e}")
        
        return self._keyword_retrieval(question, passage)

    def _extract_key_concepts(self, question: str) -> str:
        """Extract key concepts for focused search"""
        # Remove question words and focus on key nouns/verbs
        key_words = re.findall(r'\b(?!how|does|the|to|a|an|and|or|but|what|which|when|where|why)\w{3,}\b', 
                            question.lower())
        return " ".join(key_words[:5])

    def _create_contrast_query(self, question: str) -> str:
        """Create queries that look for contrasts - crucial for irony questions"""
        if any(word in question.lower() for word in ['even though', 'although', 'despite', 'however']):
            return "contrast contradiction although despite however even though but"
        return ""
    
    def _keyword_retrieval(self, question: str, passage: str) -> Dict:
        """Fallback keyword-based retrieval"""
        sentences = split_sentences(passage)
        q_words = set(question.lower().split()) - {'the', 'a', 'an', 'and', 'or', 'but', 'what', 'which', 'how'}
        
        scored_sentences = []
        for sent in sentences:
            sent_words = set(sent['text'].lower().split())
            overlap = len(q_words & sent_words)
            if overlap > 0:
                scored_sentences.append((sent, overlap))
        
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        sentences = [sent for sent, _ in scored_sentences[:3]]
        print("AHHHHHHH SENTENCES THEY SCARY")
        print(sentences)
        return {
            "sentences": sentences,
            "method": "keyword",
            "confidence": 0.5
        }
    
    # =============================================================================
    # ENHANCED ANSWER METHODS
    # =============================================================================
    
    def _answer_reading_enhanced(self, question: str, passage: str) -> str:
        """Enhanced reading comprehension with better prompting"""
        analysis = self._analyze_question(question)
        evidence = self._retrieve_evidence(question, passage, analysis)
        context = self._build_context(evidence["sentences"], passage, analysis["scope"])
        evidence_lines = [str(sent["id"]) for sent in evidence["sentences"]]
        
        # Get type-specific guidance
        analysis_instructions = self._get_analysis_instructions(analysis['question_type'])
        print("question type: " + analysis['question_type'])
        print("info needed: " + analysis['info_needed'])
        
        # Enhanced prompt that works for all question types
        prompt = f"""You are analyzing a reading comprehension question. Read carefully and think critically.

    QUESTION TYPE: {analysis['question_type']}
    WHAT TO FIND: {analysis['info_needed']}
    SCOPE: {analysis['scope']} (focus on {"specific details" if analysis['scope'] == 'local' else "broader themes"})

    PASSAGE CONTEXT:
    {context}

    QUESTION: {question}

    ANALYSIS STRATEGY:
    {analysis_instructions}

    CRITICAL THINKING GUIDELINES:
    - Look for subtle contrasts, contradictions, or ironic situations
    - Pay attention to qualifying words like "even though", "although", "despite", "however"
    - Distinguish between what characters say/think vs. what actually happens
    - Consider the author's tone and purpose
    - Look for cause-and-effect relationships
    - Notice shifts in perspective or time

    EVIDENCE SELECTION:
    Use these evidence lines to support your answer: {evidence_lines}
    Choose the lines that most directly support your chosen answer.

    Respond with JSON (no extra text or ``` marks):
    {{"answer": "...", "evidenceLines": [...], "why": "...", "kind": "reading"}}"""
        
        response = self.llm.predict(prompt, temperature=0).strip()
        parsed_response = self._clean_json_response(response)
        return json.loads(parsed_response)

    def _get_analysis_instructions(self, question_type: str) -> str:
        """Get specific analysis instructions based on question type"""
        instructions = {
            "main_idea": """
    - Identify the central theme or primary purpose of the passage
    - Look for topic sentences and concluding statements  
    - Consider what the author spends the most time discussing
    - Avoid answers that are too specific or too broad""",
            
            "detail": """
    - Find explicit information directly stated in the passage
    - Look for specific facts, dates, names, or descriptions
    - The answer should be clearly supported by the text
    - Avoid making inferences - stick to what's directly stated""",
            
            "inference": """
    - Look for implied meanings and logical conclusions
    - Connect evidence to reach reasonable conclusions
    - Consider what the author suggests but doesn't explicitly state
    - Look for patterns, cause-and-effect relationships, or logical next steps
    - Use context clues to understand the author's intent/claims""",
            
            "function": """
    - Analyze the purpose or role of specific elements (words, phrases, paragraphs)
    - Consider how the element contributes to the author's overall purpose
    - Think about rhetorical effects: does it emphasize, contrast, introduce, or conclude?
    - Examine the element's relationship to surrounding text""",
            
            "tone": """
    - Identify the author's attitude toward the subject
    - Look for descriptive words, imagery, and word choice (diction)
    - Consider the emotional undertone of the passage
    - Pay attention to formal vs. informal language, positive vs. negative connotations""",
            
            "evidence": """
    - Find the most specific and relevant text that supports a claim
    - Look for direct quotes or clear examples
    - Choose evidence that most strongly supports the point being made
    - Avoid vague or tangentially related information
    - Pay close attention to detail and only use context from the passage to support your claim""",
            
            "vocabulary_in_context": """
    - Use context clues from surrounding sentences
    - Consider how the word functions in this specific passage
    - Look for definition clues, examples, or contrasts nearby
    - Choose the meaning that best fits this particular usage"""
        }
        
        return instructions.get(question_type, """
    - Read the passage carefully and identify relevant information
    - Use the context provided to understand the question's focus
    - Look for textual evidence that directly addresses what's being asked
    - Apply critical thinking to distinguish between similar answer choices""")
    
    def _answer_grammar_enhanced(self, question: str, passage: Optional[str]) -> str:
        """Enhanced grammar handling"""
        grammar_type = self._detect_grammar_type(question)
        
        prompt = f"""Grammar focus: {grammar_type}
Question: {question}
{f"Context: {passage}" if passage else ""}

Apply the {grammar_type} rule and explain.
Respond with JSON(no extra text or ``` marks): {{"answer": "...", "rule": "{grammar_type}", "why": "...", "kind": "grammar"}}"""
        
        return self.llm.predict(prompt).strip()
    
    def _answer_vocab_enhanced(self, question: str, passage: str) -> str:
        """Enhanced vocabulary handling"""
        target_word = self._extract_target_word(question)
        context_sentences = self._get_word_context(passage, target_word)
        
        context = "\n".join([f"Line {s['id']}: {s['text']}" for s in context_sentences])
        
        prompt = f"""Find the contextual meaning of "{target_word}" in this passage.

Context:
{context}

Question: {question}

Focus on local context clues.
Respond with JSON(no extra text or ``` marks): {{"answer": "...", "contextClue": "...", "why": "...", "kind": "vocabulary"}}"""
        
        return self.llm.predict(prompt).strip()
    
    # =============================================================================
    # UTILITY METHODS
    # =============================================================================
    
    def _build_context(self, sentences: List[Dict], passage: str, scope: str) -> str:
        """Build richer context that shows relationships"""
        all_sentences = split_sentences(passage)
        sentence_ids = {s['id'] for s in sentences}
        
        # Always expand context for better understanding
        expanded_ids = set()
        for sid in sentence_ids:
            for offset in range(-2, 3):  # Wider window
                neighbor_id = sid + offset
                if 1 <= neighbor_id <= len(all_sentences):
                    expanded_ids.add(neighbor_id)
        
        relevant = [s for s in all_sentences if s['id'] in expanded_ids]
        relevant.sort(key=lambda x: x['id'])
        
        lines = []
        for s in relevant:
            if s['id'] in sentence_ids:
                lines.append(f">>> Line {s['id']}: {s['text']} <<<")  # Highlight key evidence
            else:
                lines.append(f"    Line {s['id']}: {s['text']}")
        
        return "\n".join(lines)
    
    def _get_instructions(self, question_type: str) -> str:
        """Get type-specific instructions"""
        instructions = {
            "main_idea": "Focus on the central theme. Look for topic sentences and overall purpose.",
            "inference": "Find implied meaning. Connect evidence to reach logical conclusions.",
            "function": "Analyze the purpose or role of the specified element.",
            "tone": "Identify the author's attitude through word choice and style.",
            "detail": "Find explicit information that directly answers the question.",
            "evidence": "Choose the most specific and relevant supporting text."
        }
        return instructions.get(question_type, "Answer based on the passage content.")
    
    def _detect_grammar_type(self, question: str) -> str:
        """Detect grammar rule being tested"""
        q_lower = question.lower()
        
        if any(word in q_lower for word in ['subject', 'verb', 'agreement']):
            return "subject_verb_agreement"
        elif any(word in q_lower for word in ['comma', 'punctuation']):
            return "comma_usage"
        elif any(word in q_lower for word in ['pronoun', 'it', 'they', 'who', 'whom']):
            return "pronoun_reference"
        elif any(word in q_lower for word in ['parallel', 'series']):
            return "parallelism"
        elif any(word in q_lower for word in ['modifier', 'modifying']):
            return "modifier_placement"
        elif any(word in q_lower for word in ['tense', 'past', 'present']):
            return "verb_tense"
        elif any(word in q_lower for word in ['transition', 'however', 'therefore']):
            return "transitions"
        elif any(word in q_lower for word in ['concise', 'redundant', 'delete']):
            return "concision"
        else:
            return "general_grammar"
    
    def _extract_target_word(self, question: str) -> str:
        """Extract target word from vocabulary question"""
        patterns = [
            r'"([^"]+)"',
            r"'([^']+)'",
            r'line \d+,?\s*["\']([^"\']+)["\']',
            r'["\']([^"\']+)["\'].*most nearly means'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""
    
    def _get_word_context(self, passage: str, target_word: str, window: int = 2) -> List[Dict]:
        """Get sentences containing target word with context window"""
        sentences = split_sentences(passage)
        target_sentences = []
        
        for i, sent in enumerate(sentences):
            if target_word.lower() in sent["text"].lower():
                start_idx = max(0, i - window)
                end_idx = min(len(sentences), i + window + 1)
                target_sentences.extend(sentences[start_idx:end_idx])
        
        # Remove duplicates
        seen_ids = set()
        unique = []
        for sent in target_sentences:
            if sent["id"] not in seen_ids:
                unique.append(sent)
                seen_ids.add(sent["id"])
        
        return unique
    
    def _answer_with_context(self, question: str, passage: Optional[str]) -> str:
        """Handle general questions with full context"""
        if passage:
            context = self._prepare_passage(passage)
            prompt = f"""Use this passage to answer the question thoroughly.

Passage:
{context}

Question: {question}

Provide a complete answer with evidence.
Respond with JSON(no extra text or ``` marks): {{"answer": "...", "why": "...", "kind": "other"}}"""
        else:
            prompt = f"""Answer this question:

Question: {question}

Respond with JSON(no extra text or ``` marks): {{"answer": "...", "why": "...", "kind": "other"}}"""
        
        return self.llm.predict(prompt).strip()

    def _clean_json_response(self, response: str) -> str:
        """Clean JSON response to ensure evidenceLines are strings"""
        try:
            # Parse the JSON first
            data = json.loads(response)
            
            # Convert evidenceLines integers to strings
            if 'evidenceLines' in data and isinstance(data['evidenceLines'], list):
                data['evidenceLines'] = [str(item) for item in data['evidenceLines']]
        
            # Return clean JSON
            return json.dumps(data)
        except json.JSONDecodeError:
            # Fallback: regex replacement if JSON parsing fails
            response = re.sub(r'"evidenceLines":\s*\[([^\]]*)\]', 
                             lambda m: f'"evidenceLines": [{self._fix_array_quotes(m.group(1))}]', 
                             response)
            return response

    def _fix_array_quotes(self, array_content: str) -> str:
        """Convert array of integers to array of strings"""
        # Find all numbers and wrap them in quotes
        return re.sub(r'\b(\d+)\b', r'"\1"', array_content)


#factory function
def create_enhanced_tutor(llm_wrapper: OpenAIWrapper, enable_ml: bool = True) -> EnhancedEnglishTutorTool:
    """Factory function with proper Pydantic field handling"""
    
    # Pass enable_ml as constructor parameter instead of setting after creation
    tutor = EnhancedEnglishTutorTool(
        llm=llm_wrapper,
        enable_ml_features=enable_ml,
        fallback_on_error=True
    )
    
    if enable_ml:
        print("Initializing ML models...")
        try:
            _ = tutor.sentence_model
            _ = tutor.qa_pipeline
            print("✓ All ML models loaded successfully")
        except Exception as e:
            print(f"⚠ ML model loading failed: {e}")
            print("Tutor will run in basic mode with fallbacks")
    
    return tutor


def cosine_similarity_np(a, B):
    a = np.asarray(a, dtype=float)
    B = np.asarray(B, dtype=float)
    a = a / (np.linalg.norm(a) + 1e-12)
    B = B / (np.linalg.norm(B, axis=1, keepdims=True) + 1e-12)
    return B @ a  # shape: (len(B),)

    