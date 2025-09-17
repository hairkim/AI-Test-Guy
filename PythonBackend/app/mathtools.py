from typing import Dict, List, Optional, Union
import json
import re
import sympy as sp
from sympy import symbols, solve, simplify, expand, factor, diff, integrate
import wolframalpha
from pydantic import BaseModel

class MathSolution(BaseModel):
    answer: str
    steps: List[str]
    explanation: str
    confidence: float
    method_used: str

class SATMathTutorAgent:
    """
    Intelligent SAT Math tutor that combines LLM reasoning with symbolic computation
    """
    
    def __init__(self, llm_wrapper, wolfram_app_id: Optional[str] = None):
        self.llm = llm_wrapper
        self.wolfram_client = wolframalpha.Client(wolfram_app_id) if wolfram_app_id else None
        
        # SAT Math topic patterns for classification
        self.topic_patterns = {
            "algebra": [
                "solve for", "equation", "inequality", "function", "polynomial", 
                "quadratic", "linear", "system of equations", "substitution"
            ],
            "geometry": [
                "area", "perimeter", "volume", "angle", "triangle", "circle", 
                "rectangle", "coordinate", "distance", "slope", "parallel", "perpendicular"
            ],
            "trigonometry": [
                "sin", "cos", "tan", "sine", "cosine", "tangent", "radians", 
                "degrees", "unit circle", "amplitude", "period"
            ],
            "statistics": [
                "mean", "median", "mode", "standard deviation", "probability",
                "data", "histogram", "correlation", "regression", "sample"
            ],
            "advanced_math": [
                "exponential", "logarithm", "derivative", "polynomial function",
                "rational function", "radical", "complex number"
            ]
        }
    
    def solve(self, question: str, image_context: str = None) -> MathSolution:
        """Main entry point for solving SAT math questions"""
        
        # Step 1: Classify the question type
        topic = self.classify_question(question)
        print(f"Classified as: {topic}")
        
        # Step 2: Choose solving strategy based on topic
        if topic in ["algebra", "advanced_math"]:
            return self.solve_algebraic(question, image_context)
        elif topic == "geometry":
            return self.solve_geometric(question, image_context)
        elif topic == "trigonometry":
            return self.solve_trigonometric(question, image_context)
        elif topic == "statistics":
            return self.solve_statistical(question, image_context)
        else:
            return self.solve_general(question, image_context)
    
    def classify_question(self, question: str) -> str:
        """Classify question into SAT math topics"""
        question_lower = question.lower()
        
        topic_scores = {}
        for topic, keywords in self.topic_patterns.items():
            score = sum(1 for keyword in keywords if keyword in question_lower)
            if score > 0:
                topic_scores[topic] = score
        
        if not topic_scores:
            return "general"
        
        return max(topic_scores.items(), key=lambda x: x[1])[0]
    
    def solve_algebraic(self, question: str, image_context: str = None) -> MathSolution:
        """Solve algebraic questions using hybrid approach"""
        
        # First, let LLM analyze and set up the problem
        setup_prompt = f"""
        Analyze this SAT algebra question and extract the mathematical setup:
        
        Question: {question}
        {f"Image context: {image_context}" if image_context else ""}
        
        Your task:
        1. Identify what needs to be solved
        2. Set up equations/expressions
        3. Write SymPy code to solve it
        
        Respond in JSON format:
        {{
            "goal": "what we're solving for",
            "given_info": ["list of given information"],
            "setup": "mathematical setup in words",
            "sympy_code": "executable SymPy code",
            "expected_form": "format of final answer"
        }}
        """
        
        try:
            setup_response = self.llm.predict(setup_prompt)
            setup_data = json.loads(self.clean_json(setup_response))
            
            # Execute SymPy code
            symbolic_result = self.execute_sympy_safely(setup_data["sympy_code"])
            
            # Generate step-by-step explanation
            explanation = self.generate_explanation(question, setup_data, symbolic_result)
            
            return MathSolution(
                answer=str(symbolic_result.get("final_answer", "Unable to compute")),
                steps=explanation.get("steps", []),
                explanation=explanation.get("reasoning", ""),
                confidence=0.9 if symbolic_result.get("success") else 0.6,
                method_used="symbolic_algebra"
            )
            
        except Exception as e:
            print(f"Algebraic solving failed: {e}")
            return self.solve_with_llm_reasoning(question, image_context)
    
    def solve_geometric(self, question: str, image_context: str = None) -> MathSolution:
        """Solve geometry questions with visual reasoning"""
        
        geometry_prompt = f"""
        Solve this SAT geometry question step by step:
        
        Question: {question}
        {f"Image context: {image_context}" if image_context else ""}
        
        Approach:
        1. Identify the geometric shapes and relationships
        2. List known measurements and properties
        3. Apply relevant formulas (area, volume, Pythagorean theorem, etc.)
        4. Show calculations clearly
        5. State the final answer
        
        For calculations, use this format: CALC[expression] so I can verify.
        
        Provide your solution with clear geometric reasoning.
        """
        
        response = self.llm.predict(geometry_prompt)
        processed_response = self.process_calculations(response)
        
        return MathSolution(
            answer=self.extract_final_answer(processed_response),
            steps=self.extract_steps(processed_response),
            explanation=processed_response,
            confidence=0.85,
            method_used="geometric_reasoning"
        )
    
    def solve_trigonometric(self, question: str, image_context: str = None) -> MathSolution:
        """Solve trigonometry questions"""
        
        trig_prompt = f"""
        Solve this SAT trigonometry question:
        
        Question: {question}
        {f"Image context: {image_context}" if image_context else ""}
        
        Remember:
        - Convert between degrees and radians as needed
        - Use unit circle values for common angles
        - Apply trigonometric identities when helpful
        - Show work for inverse trig functions
        
        Use CALC[expression] for numerical computations.
        """
        
        response = self.llm.predict(trig_prompt)
        processed_response = self.process_calculations(response)
        
        return MathSolution(
            answer=self.extract_final_answer(processed_response),
            steps=self.extract_steps(processed_response),
            explanation=processed_response,
            confidence=0.8,
            method_used="trigonometric"
        )
    
    def solve_statistical(self, question: str, image_context: str = None) -> MathSolution:
        """Solve statistics and probability questions"""
        
        stats_prompt = f"""
        Solve this SAT statistics/probability question:
        
        Question: {question}
        {f"Image context: {image_context}" if image_context else ""}
        
        Consider:
        - Sample vs. population
        - Appropriate measures of center and spread
        - Probability rules and conditional probability
        - Data interpretation from graphs/tables
        
        Use CALC[expression] for computations.
        """
        
        response = self.llm.predict(stats_prompt)
        processed_response = self.process_calculations(response)
        
        return MathSolution(
            answer=self.extract_final_answer(processed_response),
            steps=self.extract_steps(processed_response),
            explanation=processed_response,
            confidence=0.85,
            method_used="statistical"
        )
    
    def solve_with_llm_reasoning(self, question: str, image_context: str = None) -> MathSolution:
        """Fallback: Pure LLM reasoning with computation verification"""
        
        reasoning_prompt = f"""
        Solve this SAT math question step by step:
        
        Question: {question}
        {f"Image context: {image_context}" if image_context else ""}
        
        Show your work clearly:
        1. Understand what's being asked
        2. Identify given information
        3. Choose appropriate method/formula
        4. Perform calculations (use CALC[expression] format)
        5. Check your answer makes sense
        
        Be thorough but concise.
        """
        
        response = self.llm.predict(reasoning_prompt)
        processed_response = self.process_calculations(response)
        
        return MathSolution(
            answer=self.extract_final_answer(processed_response),
            steps=self.extract_steps(processed_response),
            explanation=processed_response,
            confidence=0.75,
            method_used="llm_reasoning"
        )
    
    def execute_sympy_safely(self, sympy_code: str) -> Dict:
        """Safely execute SymPy code and return results"""
        try:
            # Create safe execution environment
            safe_globals = {
                '__builtins__': {},
                'sympy': sp,
                'symbols': symbols,
                'solve': solve,
                'simplify': simplify,
                'expand': expand,
                'factor': factor,
                'diff': diff,
                'integrate': integrate,
                'Eq': sp.Eq,
                'pi': sp.pi,
                'E': sp.E,
                'sqrt': sp.sqrt,
                'sin': sp.sin,
                'cos': sp.cos,
                'tan': sp.tan,
                'log': sp.log,
                'exp': sp.exp
            }
            
            local_vars = {}
            exec(sympy_code, safe_globals, local_vars)
            
            # Try to find the result
            possible_results = ['solution', 'result', 'answer', 'sol']
            final_answer = None
            
            for var_name in possible_results:
                if var_name in local_vars:
                    final_answer = local_vars[var_name]
                    break
            
            if final_answer is None:
                # Look for the last assigned variable
                if local_vars:
                    final_answer = list(local_vars.values())[-1]
            
            return {
                "success": True,
                "final_answer": final_answer,
                "variables": local_vars
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "final_answer": None
            }
    
    def process_calculations(self, text: str) -> str:
        """Process CALC[expression] blocks and replace with results"""
        def calculate(match):
            expr = match.group(1)
            try:
                # Safe evaluation with math functions
                import math
                safe_dict = {
                    '__builtins__': {},
                    'abs': abs, 'round': round, 'min': min, 'max': max,
                    'sum': sum, 'pow': pow,
                    'sqrt': math.sqrt, 'sin': math.sin, 'cos': math.cos,
                    'tan': math.tan, 'pi': math.pi, 'e': math.e,
                    'log': math.log, 'exp': math.exp, 'degrees': math.degrees,
                    'radians': math.radians
                }
                result = eval(expr, safe_dict)
                return f"{expr} = {result}"
            except Exception as e:
                return f"[Error calculating {expr}: {e}]"
        
        return re.sub(r'CALC\[(.*?)\]', calculate, text)
    
    def generate_explanation(self, question: str, setup_data: Dict, symbolic_result: Dict) -> Dict:
        """Generate step-by-step explanation"""
        
        explanation_prompt = f"""
        Create a clear, step-by-step explanation for this solution:
        
        Original Question: {question}
        Goal: {setup_data.get('goal', 'Unknown')}
        Setup: {setup_data.get('setup', 'Unknown')}
        Result: {symbolic_result.get('final_answer', 'Unable to compute')}
        
        Create an explanation that:
        1. States what we need to find
        2. Lists the given information
        3. Explains the approach/method
        4. Shows key calculation steps
        5. States the final answer clearly
        
        Make it educational and easy to follow for SAT students.
        """
        
        explanation = self.llm.predict(explanation_prompt)
        
        return {
            "reasoning": explanation,
            "steps": self.extract_steps(explanation)
        }
    
    def extract_steps(self, text: str) -> List[str]:
        """Extract numbered steps from explanation"""
        steps = []
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if re.match(r'^\d+\.', line) or line.startswith('Step'):
                steps.append(line)
        return steps
    
    def extract_final_answer(self, text: str) -> str:
        """Extract final answer from solution text"""
        # Look for common answer patterns
        patterns = [
            r'(?:final answer|answer|solution|result).*?(?:is|=)\s*([^\n\.\,]+)',
            r'therefore[,\s]+([^\n\.\,]+)',
            r'answer:\s*([^\n\.\,]+)',
            r'=\s*([^\n\.\,]+)$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                answer = match.group(1).strip()
                if answer and len(answer) < 50:  # Reasonable answer length
                    return answer
        
        return "Answer not clearly identified"
    
    def clean_json(self, text: str) -> str:
        """Clean JSON response from LLM"""
        # Remove markdown code blocks if present
        text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE)
        return text.strip()
    
    def solve_general(self, question: str, image_context: str = None) -> MathSolution:
        """Solve general math questions that don't fit specific categories"""
        
        general_prompt = f"""
        Solve this SAT math question step by step:
        
        Question: {question}
        {f"Image context: {image_context}" if image_context else ""}
        
        Since this doesn't fit a specific category, approach it systematically:
        1. Read carefully and identify what's being asked
        2. List all given information
        3. Determine what mathematical concepts apply
        4. Choose the most appropriate method
        5. Show your work step by step
        6. Use CALC[expression] for any calculations
        7. State your final answer clearly
        
        Be thorough in your reasoning and check that your answer makes sense.
        """
        
        response = self.llm.predict(general_prompt)
        processed_response = self.process_calculations(response)
        
        return MathSolution(
            answer=self.extract_final_answer(processed_response),
            steps=self.extract_steps(processed_response),
            explanation=processed_response,
            confidence=0.7,  # Lower confidence for unclassified questions
            method_used="general_reasoning"
        )


def create_math_tutor(llm_wrapper, wolfram_app_id: Optional[str] = None):
    """Factory function to create the math tutor agent"""
    return SATMathTutorAgent(llm_wrapper, wolfram_app_id)