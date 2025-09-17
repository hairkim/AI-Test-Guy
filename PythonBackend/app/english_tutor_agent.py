
import re
import json

class ConversationalEnglishSATTutor:
    def __init__(self, llm_wrapper):
        self.llm = llm_wrapper
        self.analysis_tool = EnglishAnalysisEngine(llm_wrapper)
        print("English SAT Tutor initialized")
    
    def solve(self, question: str, passage: str = None):
        # Determine what type of English question this is
        question_type = self.classify_question_type(question)
        
        prompt = f"""
        You are a friendly SAT English tutor specializing in Reading and Writing. Help students with:
        - Reading comprehension and analysis
        - Grammar and usage
        - Rhetorical analysis
        - Writing techniques and style
        - Vocabulary in context
        
        When you need to analyze text deeply, write ANALYZE[type: description] and I'll provide detailed analysis.
        
        Examples of ANALYZE usage:
        - ANALYZE[grammar: check subject-verb agreement in this sentence]
        - ANALYZE[rhetoric: identify the author's persuasive techniques]
        - ANALYZE[tone: analyze the author's attitude toward the subject]
        - ANALYZE[structure: examine how this paragraph develops the argument]
        - ANALYZE[vocabulary: determine meaning from context]
        
        Question Type: {question_type}
        Question: {question}
        {f"Passage: {passage}" if passage else ""}
        
        Provide step-by-step explanations and teach the underlying concepts.
        Format your response using Markdown:
        - Use ## for section headers
        - Use **bold** for key concepts and important terms
        - Use bullet points for multiple choice elimination strategies
        - Use numbered lists for analysis steps
        - Use > blockquotes for citing text from passages
        - Add a clear "Answer" section at the end
        
        Be encouraging and explain not just what the answer is, but WHY it's correct and how to approach similar questions.
        """
        
        # Get response with ANALYZE tags
        response = self.llm.predict(prompt)
        print(f"Response: {response}")
        
        # Process ANALYZE tags using the tool
        final_response = self.process_analyze_tags(response, passage)
        print(f"Final response: {final_response}")
        
        return final_response
    
    def classify_question_type(self, question: str):
        """Determine what type of SAT English question this is"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ["grammar", "subject", "verb", "pronoun", "tense", "comma", "semicolon"]):
            return "Grammar and Usage"
        elif any(word in question_lower for word in ["main idea", "central claim", "purpose", "summarize"]):
            return "Reading Comprehension - Main Idea"
        elif any(word in question_lower for word in ["tone", "attitude", "mood", "author's perspective"]):
            return "Reading Comprehension - Tone/Attitude"
        elif any(word in question_lower for word in ["evidence", "support", "best supports", "which lines"]):
            return "Reading Comprehension - Evidence"
        elif any(word in question_lower for word in ["word choice", "meaning", "context", "most nearly means"]):
            return "Vocabulary in Context"
        elif any(word in question_lower for word in ["rhetorical", "persuasive", "argument", "appeal"]):
            return "Rhetorical Analysis"
        elif any(word in question_lower for word in ["structure", "organization", "transition", "paragraph"]):
            return "Structure and Organization"
        else:
            return "General English/Reading"
    
    def process_analyze_tags(self, text, passage=None):
        def analyze(match):
            request = match.group(1)
            result = self.analysis_tool.analyze(request, passage)
            print(f"Result for analysis '{request}': {result}")
            return str(result)
        
        return re.sub(r'ANALYZE\[(.*?)\]', analyze, text)


class EnglishAnalysisEngine:
    def __init__(self, llm_wrapper):
        self.llm = llm_wrapper
    
    def analyze(self, analysis_request: str, passage: str = None):
        """
        Main analysis method for English content
        """
        print(f"Analyzing: {analysis_request}")
        
        # Parse the analysis type and description
        analysis_type, description = self.parse_analysis_request(analysis_request)
        
        # Route to appropriate analysis method
        if analysis_type == "grammar":
            return self.analyze_grammar(description, passage)
        elif analysis_type == "rhetoric":
            return self.analyze_rhetoric(description, passage)
        elif analysis_type == "tone":
            return self.analyze_tone(description, passage)
        elif analysis_type == "structure":
            return self.analyze_structure(description, passage)
        elif analysis_type == "vocabulary":
            return self.analyze_vocabulary(description, passage)
        else:
            return self.general_analysis(analysis_request, passage)
    
    def parse_analysis_request(self, request: str):
        """Parse analysis type and description from request"""
        if ":" in request:
            parts = request.split(":", 1)
            return parts[0].strip().lower(), parts[1].strip()
        else:
            return "general", request.strip()
    
    def analyze_grammar(self, description: str, passage: str = None):
        """Analyze grammar and usage issues"""
        prompt = f"""
        As an expert grammar tutor, analyze this grammar issue:
        
        Description: {description}
        {f"Text/Passage: {passage}" if passage else ""}
        
        Provide:
        1. Identification of the specific grammar rule or concept
        2. Explanation of what's correct/incorrect and why
        3. The corrected version if applicable
        4. A brief rule to remember for similar cases
        
        Be concise but thorough.
        """
        
        return self.llm.predict(prompt)
    
    def analyze_rhetoric(self, description: str, passage: str = None):
        """Analyze rhetorical techniques and persuasive strategies"""
        prompt = f"""
        As a rhetorical analysis expert, examine this text for persuasive techniques:
        
        Analysis Focus: {description}
        {f"Text/Passage: {passage}" if passage else ""}
        
        Identify and explain:
        1. Specific rhetorical devices used (ethos, pathos, logos, etc.)
        2. Persuasive techniques and their effectiveness
        3. How these techniques support the author's argument
        4. The intended effect on the audience
        
        Be specific and cite examples from the text.
        """
        
        return self.llm.predict(prompt)
    
    def analyze_tone(self, description: str, passage: str = None):
        """Analyze tone, mood, and author's attitude"""
        prompt = f"""
        As a literary analysis expert, analyze the tone and attitude in this text:
        
        Analysis Focus: {description}
        {f"Text/Passage: {passage}" if passage else ""}
        
        Determine:
        1. The author's tone/attitude (objective, critical, admiring, etc.)
        2. Specific word choices that reveal this tone
        3. How the tone supports the author's purpose
        4. Evidence from the text that supports your analysis
        
        Provide specific examples and explain your reasoning.
        """
        
        return self.llm.predict(prompt)
    
    def analyze_structure(self, description: str, passage: str = None):
        """Analyze text structure and organization"""
        prompt = f"""
        As a writing structure expert, analyze the organization and flow of this text:
        
        Analysis Focus: {description}
        {f"Text/Passage: {passage}" if passage else ""}
        
        Examine:
        1. How the text is organized (chronological, compare/contrast, cause/effect, etc.)
        2. Transition words and phrases that connect ideas
        3. How each paragraph develops the main argument
        4. The effectiveness of the overall structure
        
        Explain how the structure serves the author's purpose.
        """
        
        return self.llm.predict(prompt)
    
    def analyze_vocabulary(self, description: str, passage: str = None):
        """Analyze vocabulary in context"""
        prompt = f"""
        As a vocabulary expert, analyze word meaning and usage in context:
        
        Analysis Focus: {description}
        {f"Text/Passage: {passage}" if passage else ""}
        
        Determine:
        1. The meaning of the word/phrase in this specific context
        2. Context clues that help determine the meaning
        3. Why other potential meanings don't fit
        4. The connotation and effect of this word choice
        
        Explain your reasoning step by step.
        """
        
        return self.llm.predict(prompt)
    
    def general_analysis(self, description: str, passage: str = None):
        """General text analysis for other types of questions"""
        prompt = f"""
        As an English analysis expert, provide insight on this text analysis request:
        
        Request: {description}
        {f"Text/Passage: {passage}" if passage else ""}
        
        Provide a thorough analysis addressing the specific request.
        Include relevant examples from the text and explain your reasoning.
        """
        
        return self.llm.predict(prompt)