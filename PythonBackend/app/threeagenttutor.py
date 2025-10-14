import wolframalpha
import re
import math
import requests
import json
from PIL import Image
import base64
from io import BytesIO

class ConversationalSATTutor:
    """
    Unified SAT tutor that handles both text and image inputs.
    Replaces both ConversationalSATTutor and ImageSATTutor.
    """
    
    def __init__(self, llm_wrapper, wolfram_app_id):
        """
        Args:
            llm_wrapper: OpenAIWrapper instance with vision support
            wolfram_app_id: Wolfram Alpha API key
        """
        self.llm = llm_wrapper
        self.computation_tool = SATComputationEngine(wolfram_app_id, llm_wrapper)
        print(f"Wolfram App ID: {wolfram_app_id if wolfram_app_id else 'None'}")
    
    def solve(self, question: str = None, image_base64: str = None):
        """
        Main solve method that handles all input types.
        
        Args:
            question: Text question/prompt (optional)
            image_base64: Base64 encoded image (optional)
            
        Returns:
            Formatted solution with explanations
        
        Usage:
            # Text only (like old ConversationalSATTutor)
            tutor.solve(question="What is 2x + 7 = 15?")
            
            # Image only
            tutor.solve(image_base64="base64_string...")
            
            # Both
            tutor.solve(question="Explain this", image_base64="base64_string...")
        """
        # Validate inputs
        if not question and not image_base64:
            return "Error: Please provide either a question, an image, or both."
        
        # Validate image if provided
        if image_base64 and not self._validate_image(image_base64):
            return "Error: Invalid image format. Please provide a valid base64 encoded image."
        
        # Extract content from image if provided
        image_content = None
        if image_base64:
            image_content = self._extract_image_content(image_base64)
        
        # Generate solution based on what we have
        return self._generate_solution(image_content, question)
    
    def _validate_image(self, image_base64: str) -> bool:
        """Validate that the base64 string represents a valid image"""
        try:
            if ',' in image_base64:
                image_base64 = image_base64.split(',')[1]
            
            image_data = base64.b64decode(image_base64)
            Image.open(BytesIO(image_data))
            return True
        except Exception as e:
            print(f"Image validation failed: {e}")
            return False
    
    def _extract_image_content(self, image_base64: str) -> dict:
        """Use vision LLM to extract content from the image"""
        prompt = """
        Analyze this image and extract the following information:
        
        1. **Question Text**: If there is any question text visible in the image, extract it word-for-word.
        2. **Diagram/Visual Elements**: Describe any diagrams, graphs, charts, tables, or visual elements present.
        3. **Mathematical Notation**: Identify any mathematical expressions, equations, or formulas.
        4. **Answer Choices**: If there are answer choices visible (like A, B, C, D or multiple choice options), extract them EXACTLY as they appear. Include the letter/number labels.
        
        Format your response as:
        QUESTION_TEXT: [the exact question text, or "NONE" if no question is visible]
        HAS_DIAGRAM: [YES or NO]
        DIAGRAM_DESCRIPTION: [detailed description of visual elements, or "NONE" if no diagram]
        MATH_ELEMENTS: [list any mathematical notation present, or "NONE"]
        ANSWER_CHOICES: [list each answer choice with its label exactly as shown, or "NONE"]
        
        Example for answer choices:
        ANSWER_CHOICES: A) 5, B) 10, C) 15, D) 20
        """
        
        response = self.llm.predict_with_image(prompt, image_base64)
        
        # Parse the response
        extracted = {
            'question_text': self._extract_field(response, 'QUESTION_TEXT'),
            'has_diagram': self._extract_field(response, 'HAS_DIAGRAM') == 'YES',
            'diagram_description': self._extract_field(response, 'DIAGRAM_DESCRIPTION'),
            'math_elements': self._extract_field(response, 'MATH_ELEMENTS'),
            'answer_choices': self._extract_field(response, 'ANSWER_CHOICES')
        }
        
        print(f"Extracted answer choices: {extracted['answer_choices']}")  # Debug log
        
        return extracted
    
    def _extract_field(self, text: str, field_name: str) -> str:
        """Helper to extract a field from the structured response"""
        pattern = f"{field_name}:\\s*(.+?)(?=\\n[A-Z_]+:|$)"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            value = match.group(1).strip()
            return value if value != "NONE" else None
        return None
    
    def _generate_solution(self, image_content: dict, question_prompt: str):
        """Generate a solution based on extracted image content and/or user prompt"""
        
        # Case 1: Only image provided (no text prompt)
        if image_content and not question_prompt:
            if image_content['question_text']:
                # Image contains the question - solve it
                return self._solve_question(
                    question_text=image_content['question_text'],
                    diagram_info=image_content['diagram_description'],
                    has_diagram=image_content['has_diagram'],
                    answer_choices=image_content['answer_choices']  # FIX: Added this parameter
                )
            elif image_content['has_diagram']:
                # Image only has a diagram - explain it
                return self._explain_diagram(image_content['diagram_description'])
            else:
                return "I can see the image, but it doesn't contain a clear question or diagram. Could you provide more context about what you'd like help with?"
        
        # Case 2: Both image and text prompt provided
        elif image_content and question_prompt:
            return self._solve_with_context(
                question_prompt=question_prompt,
                diagram_info=image_content['diagram_description'],
                extracted_text=image_content['question_text'],
                answer_choices=image_content['answer_choices']
            )
        
        # Case 3: Only text prompt (no image) - same as old ConversationalSATTutor
        else:
            return self._solve_question(question_text=question_prompt)
    
    def _solve_question(self, question_text: str, diagram_info: str = None, has_diagram: bool = False, answer_choices: str = None):
        """Solve a question with optional diagram context and answer choices"""
        context = ""
        if has_diagram and diagram_info:
            context = f"\n\nDiagram Description: {diagram_info}\n"
        
        # Add answer choices to context if available
        answer_choice_instruction = ""
        if answer_choices:
            context += f"\nAnswer Choices: {answer_choices}\n"
            answer_choice_instruction = f"""
        
        IMPORTANT - ANSWER CHOICES:
        The question has multiple choice answers: {answer_choices}
        
        You MUST:
        1. Work through the problem step-by-step as usual
        2. Calculate the correct answer
        3. In your final "Answer" section, identify which answer choice (A, B, C, D, etc.) matches your calculated result
        4. State your final answer in the EXACT format of the answer choices
        5. If your calculated answer doesn't exactly match any choice, pick the closest one and explain why
        
        Format your final answer like this:
        ## Answer
        The correct answer is **[Letter]**: [exact answer choice text]
        """
        
        prompt = f"""
        You are a friendly SAT math tutor. Solve this step-by-step with conversational explanations.
        
        When you need to calculate something, write COMPUTE[expression or description] and I'll handle the math.

        Make sure to include step by step explanations, especially for complex problems and make sure that the student doesn't have any other questions.
        
        Examples of COMPUTE usage:
        - COMPUTE[3 + 5] for basic arithmetic
        - COMPUTE[solve 2x + 7 = 15] for equations
        - COMPUTE[sqrt(25)] for square roots
        - COMPUTE[area of circle with radius 5] for geometry
        {context}
        Question: {question_text}
        {answer_choice_instruction}
        
        Show your thinking process, explain why you're taking each step, and be encouraging.
        Format your response using Markdown:
        - Use ## for section headers
        - Use **bold** for key numbers and concepts  
        - Use bullet points for given information
        - Use numbered lists for solution steps
        - Use code blocks for formulas: ```formula here```
        - Add a clear "Answer" section at the end

        Also format your math using LaTeX:
        - Wrap inline math with single dollar signs: $\\frac{{2}}{{3}}$
        - Use double dollar signs for display math: $$x = \\frac{{-b \\pm \\sqrt{{b^2-4ac}}}}{{2a}}$$
        - Always escape backslashes in LaTeX: \\frac{{a}}{{b}} not \frac{{a}}{{b}}
        """
        
        response = self.llm.predict(prompt)
        return self._process_compute_tags(response)
    
    def _explain_diagram(self, diagram_description: str):
        """Explain what a diagram shows when no question is provided"""
        prompt = f"""
        You are a helpful SAT tutor. A student has shown you a diagram without a specific question.
        
        Diagram Description: {diagram_description}
        
        Please:
        1. Explain what the diagram shows
        2. Identify key mathematical concepts or relationships visible in the diagram
        3. Suggest what types of questions might be asked about this diagram
        4. Point out any important features or patterns
        
        Format your response using Markdown with clear sections.
        Use LaTeX for any mathematical expressions.
        """
        
        return self.llm.predict(prompt)
    
    def _solve_with_context(self, question_prompt: str, diagram_info: str, extracted_text: str = None, answer_choices: str = None):
        """Solve a user's question using the diagram/image as supporting context"""
        context_parts = []
        
        if extracted_text:
            context_parts.append(f"Text from image: {extracted_text}")
        
        if diagram_info:
            context_parts.append(f"Visual elements from image: {diagram_info}")

        if answer_choices:
            context_parts.append(f"Answer choices from image: {answer_choices}")
        
        context = "\n\n".join(context_parts)
        
        # Add strong answer choice instruction
        answer_choice_instruction = ""
        if answer_choices:
            answer_choice_instruction = f"""
        
        CRITICAL - ANSWER CHOICES:
        The image contains these answer choices: {answer_choices}
        
        You MUST:
        1. Solve the problem completely with full explanations
        2. In your final answer, select the letter (A, B, C, D, etc.) that matches your solution
        3. State the answer in the EXACT format shown in the answer choices
        4. Do NOT give an answer that is not one of the provided choices
        
        Format your final answer section like:
        ## Answer
        The correct answer is **[Letter]**: [exact answer choice text]
        """
        
        prompt = f"""
        You are a friendly SAT math tutor. A student has provided both an image and a question.
        
        Context from the image:
        {context}
        
        Student's question: {question_prompt}
        
        When you need to calculate something, write COMPUTE[expression or description] and I'll handle the math.
        
        Solve this step-by-step with conversational explanations, making use of the information from the image.
        {answer_choice_instruction}
        
        Format your response using Markdown:
        - Use ## for section headers
        - Use **bold** for key numbers and concepts  
        - Use bullet points for given information
        - Use numbered lists for solution steps
        - Add a clear "Answer" section at the end

        Use LaTeX for mathematical expressions:
        - Inline math: $\\frac{{2}}{{3}}$
        - Display math: $$x = \\frac{{-b \\pm \\sqrt{{b^2-4ac}}}}{{2a}}$$
        """
        
        response = self.llm.predict(prompt)
        return self._process_compute_tags(response)
    
    def _process_compute_tags(self, text):
        """Process COMPUTE tags in the response"""
        if not self.computation_tool:
            return text
        
        def compute(match):
            request = match.group(1)
            result = self.computation_tool.compute(request)
            print(f"Result for compute '{request}': {result}")
            return str(result)
        
        return re.sub(r'COMPUTE\[(.*?)\]', compute, text)

class CustomWolframClient:
    def __init__(self, app_id):
        self.app_id = app_id
        self.base_url = "http://api.wolframalpha.com/v2/query"
    
    def query(self, query_string):
        """
        Query Wolfram Alpha and return a result object similar to the original library
        """
        params = {
            'input': query_string,
            'appid': self.app_id,
            'format': 'plaintext',
            'output': 'JSON'
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            
            if response.status_code != 200:
                raise Exception(f"API request failed with status {response.status_code}")
            
            data = response.json()
            return WolframResult(data)
            
        except Exception as e:
            raise Exception(f"Wolfram query failed: {e}")


class WolframResult:
    """
    Mock the structure that the original wolframalpha library returns
    """
    def __init__(self, json_data):
        self.raw_data = json_data
        self.success = json_data.get('queryresult', {}).get('success', False)
        self.pods = []
        
        if self.success:
            pods_data = json_data.get('queryresult', {}).get('pods', [])
            for pod_data in pods_data:
                self.pods.append(WolframPod(pod_data))


class WolframPod:
    """
    Mock the Pod structure from the original library
    """
    def __init__(self, pod_data):
        self.title = pod_data.get('title', '')
        self.text = self._extract_text(pod_data)
    
    def _extract_text(self, pod_data):
        """
        Extract text from subpods
        """
        subpods = pod_data.get('subpods', [])
        if not subpods:
            return ''
        
        # Get text from the first subpod
        first_subpod = subpods[0]
        return first_subpod.get('plaintext', '')


# Updated SATComputationEngine to use the custom client
class SATComputationEngine:
    def __init__(self, app_id, llm_wrapper):
        self.wolfram_client = CustomWolframClient(app_id) if app_id else None
        self.llm = llm_wrapper
    
    def compute(self, compute_request: str):
        """
        Main compute method that tries Wolfram Alpha first, then falls back to Python
        """
        print(f"Computing: {compute_request}")
        
        # Try Wolfram Alpha first
        if self.wolfram_client:
            try:
                wolfram_result = self.try_wolfram(compute_request)
                if wolfram_result and wolfram_result != "Could not extract answer":
                    return wolfram_result
            except Exception as e:
                print(f"Wolfram Alpha failed: {e}")
        
        # Fall back to Python computation
        return self.fallback_compute(compute_request)
    
    def try_wolfram(self, request: str):
        """
        Try to compute using Wolfram Alpha
        """
        try:
            # Clean and prepare the query
            wolfram_query = self.prepare_wolfram_query(request)
            print(f"Wolfram query: '{wolfram_query}'")
            
            result = self.wolfram_client.query(wolfram_query)
            
            if not result.success:
                print("Wolfram query was not successful")
                return None
                
            answer = self.extract_wolfram_answer(result)
            print(f"Wolfram result: {answer}")
            return answer
            
        except Exception as e:
            print(f"Wolfram Alpha error: {e}")
            return None
    
    def prepare_wolfram_query(self, request: str):
        """
        Prepare the request for Wolfram Alpha
        """
        request = request.strip()
        
        # If it's already a simple mathematical expression, use it directly
        if self.is_simple_math(request):
            return request
        
        # Otherwise, let the LLM help convert it
        return self.convert_to_wolfram_query(request)
    
    def is_simple_math(self, expression: str):
        """
        Check if this looks like a simple mathematical expression
        """
        # Remove spaces and check if it contains only numbers and basic operators
        cleaned = expression.replace(' ', '')
        allowed_chars = set('0123456789+-*/().^')
        return all(c in allowed_chars for c in cleaned) and any(c in '+-*/' for c in cleaned)
    
    def convert_to_wolfram_query(self, request: str):
        """
        Use LLM to convert complex requests to Wolfram queries
        """
        prompt = f"""
        Convert this computation request to a Wolfram Alpha query.
        
        Request: {request}
        
        Examples:
        "solve 2x + 7 = 15" → "solve 2x + 7 = 15"
        "area of circle with radius 5" → "area of circle radius 5"
        "expand (x + 3)^2" → "expand (x + 3)^2"
        "square root of 25" → "sqrt(25)"
        "3 + 5" → "3 + 5"
        
        Return only the Wolfram query (no quotes or extra text):
        """
        
        result = self.llm.predict(prompt).strip()
        # Remove quotes if the LLM added them
        result = result.strip('"\'')
        return result
    
    def extract_wolfram_answer(self, result):
        """
        Extract the answer from Wolfram Alpha results
        """
        try:
            # Look for pods with answers in order of preference
            preferred_titles = ["Result", "Solution", "Decimal form", "Exact result", "Value"]
            
            for title in preferred_titles:
                for pod in result.pods:
                    if pod.title == title and pod.text:
                        return pod.text.split('\n')[0]  # Take first line
            
            # If no preferred pod found, take the second pod (first is usually the input)
            if len(result.pods) > 1 and result.pods[1].text:
                return result.pods[1].text.split('\n')[0]
                
            return "Could not extract answer"
            
        except Exception as e:
            print(f"Error extracting Wolfram answer: {e}")
            return "Could not extract answer"
    
    def fallback_compute(self, request: str):
        """
        Python-based computation fallback
        """
        try:
            # Handle simple arithmetic expressions
            if self.is_simple_math(request):
                # Use eval for simple math (be careful with this in production!)
                result = eval(request.replace('^', '**'))  # Handle exponents
                return str(result)
            
            # Handle some common functions
            request_lower = request.lower()
            
            if 'sqrt' in request_lower:
                # Extract number from sqrt expression
                import re, math
                match = re.search(r'sqrt\((\d+(?:\.\d+)?)\)', request_lower)
                if match:
                    number = float(match.group(1))
                    return str(math.sqrt(number))
            
            if 'square root of' in request_lower:
                # Extract number after "square root of"
                import re, math
                match = re.search(r'square root of (\d+(?:\.\d+)?)', request_lower)
                if match:
                    number = float(match.group(1))
                    return str(math.sqrt(number))
            
            return f"Cannot compute: {request}"
            
        except Exception as e:
            print(f"Fallback computation error: {e}")
            return f"Error computing: {request}"