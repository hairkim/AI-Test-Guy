from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser
from langchain.tools import BaseTool
from langchain.pydantic_v1 import Field, BaseModel
from langchain.chat_models import ChatOpenAI
from typing import Optional, Dict, Any
import re, json
from langchain.llms.base import LLM
from typing import Type
import sympy as sp
from sympy import symbols, Eq, solve, simplify, latex

class OpenAIWrapper:
    """Wrapper to make OpenAI client compatible with LangChain tools"""
    
    def __init__(self, client):
        self.client = client
    
    def predict(self, prompt_text: str, model: str = "gpt-4o-mini", temperature: float = 0) -> str:
        """Make OpenAI call compatible with LangChain interface"""
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt_text}],
                max_tokens=1000,
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error calling OpenAI: {str(e)}"

class OpenAICompatibleLLM(LLM):
    openai_wrapper: OpenAIWrapper

    def _call(self, prompt: str, stop=None):
        return self.openai_wrapper.predict(prompt)

    @property
    def _llm_type(self):
        return "openai-wrapper"

class MathExtractionOutput(BaseModel):
    """Output schema for math extraction"""
    equation: str = Field(description="SymPy-compatible equation format")
    target_expression: str = Field(description="Expression or variable to evaluate")
    has_equation: bool = Field(description="Whether a solvable equation was found")


class MathExtractionParser(BaseOutputParser[MathExtractionOutput]):
    """Parser for math extraction output"""
    
    def parse(self, text: str) -> MathExtractionOutput:
        try:
            raw = text.strip()

            # Remove any markdown code fences like ```json ... ```
            raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
            raw = re.sub(r"```$", "", raw).strip()

            # Now try parsing as JSON
            if raw.startswith("{"):
                data = json.loads(raw)
                return MathExtractionOutput(**data)

            # Fallback: parse from text format
            equation = "NO_EQUATION"
            target_expression = "NONE"
            for line in raw.splitlines():
                if line.lower().startswith("equation:"):
                    equation = line.split(":", 1)[1].strip()
                elif line.lower().startswith("target:"):
                    target_expression = line.split(":", 1)[1].strip()

            return MathExtractionOutput(
                equation=equation,
                target_expression=target_expression,
                has_equation=equation != "NO_EQUATION",
            )

        except Exception:
            return MathExtractionOutput(
                equation="NO_EQUATION",
                target_expression="NONE",
                has_equation=False
            )
    
    def get_format_instructions(self) -> str:
        return """Return the result in JSON format with the following structure:
        {
            "equation": "SymPy-compatible equation (e.g., 'Eq(2*x + 3, 13)') or 'NO_EQUATION' if none found",
            "target_expression": "Expression to evaluate (e.g., '3/x', 'x', 'p') or 'NONE' if not specified",
            "has_equation": true/false
        }"""


class MathResponseParser(BaseOutputParser):
    """Parser for structured math responses (not equation extraction!)"""
    
    def parse(self, text: str) -> Dict[str, Any]:
        solution = ""
        explanation_steps = []
        
        if "SOLUTION:" in text and "EXPLANATION:" in text:
            parts = text.split("EXPLANATION:")
            solution = parts[0].replace("SOLUTION:", "").strip()
            
            explanation_text = parts[1].strip()
            # Split by numbered steps
            steps = re.split(r'\n(?=\d+\.)', explanation_text)
            explanation_steps = [step.strip() for step in steps if step.strip()]
        else:
            # Try to extract solution from math solver output
            lines = text.split('\n')
            for line in lines:
                if line.startswith("Solution:") or line.startswith("The value of"):
                    solution = line
                    break
            
            # If no structured format, use the whole text
            if not solution:
                solution = text
                explanation_steps = [text]
            else:
                explanation_steps = lines
        
        return {
            "solution": solution,
            "explanation_steps": explanation_steps,
            "full_response": text
        }


class MathSolverTool(BaseTool):
    """LangChain tool for solving mathematical equations using SymPy"""
    
    name: str = "math_solver"
    description: str = """
    Solves mathematical equations and evaluates expressions from natural language questions.
    Useful for SAT math problems, algebra, and equation solving.
    Input should be a mathematical question in natural language.
    """
    
    llm: OpenAIWrapper = Field(description="Language model for equation extraction")
    # llm: ChatOpenAI = Field(description="Language model for equation extraction")
    
    def __init__(self, llm: OpenAIWrapper, **kwargs):
        super().__init__(llm=llm, **kwargs)
    
    def _run(self, question_text: str) -> str:
        """Execute the math solving process"""
        try:
            result = self.solve_equation_with_sympy(question_text)
            if result:
                return self._format_result(result)
            else:
                return "Could not solve the mathematical equation from the given question."
        except Exception as e:
            return f"Error solving math problem: {str(e)}"
    
    async def _arun(self, question_text: str) -> str:
        """Async version - just calls the sync version"""
        return self._run(question_text)
    
    def solve_equation_with_sympy(self, question_text: str) -> Optional[Dict[str, Any]]:
        """
        Attempts to extract and solve mathematical equations from the question text using SymPy.
        Also evaluates any target expressions mentioned in the question.
        Returns the solution if found, otherwise returns None.
        """
        try:
            # Create the combined extraction prompt
            extraction_prompt = PromptTemplate(
                input_variables=["question"],
                template="""
                Analyze the following mathematical question and extract:
                1. The mathematical equation in SymPy-compatible format
                2. What the question is asking you to find/evaluate

                Rules for equation extraction:
                - Convert to SymPy format (e.g., "Eq(2*x + 3, 13)")
                - Use standard variable names (x, y, z, p, etc.)
                - For fractions like 3/(13p), write as: 3/(13*p)
                - For fractions like (17x)/(5y), write as: (17*x)/(5*y)
                - Pay careful attention to parentheses and multiplication
                - If no solvable equation exists, use "NO_EQUATION"

                Rules for target expression:
                - If asking "What is the value of [expression]?", return that expression in SymPy format
                - If asking to "solve for X" or "find X", return just the variable (e.g., "x", "p")
                - If asking to find/calculate/determine a variable, return that variable
                - Use the same variable names as in the equation
                - If no clear target, use "NONE"

                Examples:
                - "3/(13p) = (17x)/(5y)" → equation: "Eq(3/(13*p), (17*x)/(5*y))"
                - "What is the value of 3/x?" → target: "3/x"
                - "Solve for x" → target: "x"
                - "Find the p-value" → target: "p"

                Question: {question}

                {format_instructions}
                """,
                partial_variables={"format_instructions": MathExtractionParser().get_format_instructions()}
            )
            
            # Get extraction using your OpenAI client
            parser = MathExtractionParser()
            prompt_text = extraction_prompt.format(question=question_text)
            
            llm_response = self.llm.predict(prompt_text)
            print("Extraction raw:", llm_response)
            extraction_result = parser.parse(llm_response)
            
            print(f"Extracted equation: {extraction_result.equation}")
            print(f"Target expression: {extraction_result.target_expression}")
            
            if not extraction_result.has_equation:
                return None
                
            # Create symbol dictionary dynamically based on equation content
            # First, create common symbols
            common_vars = 'x y z p q r s t a b c d e f g h i j k l m n o u v w'
            symbol_dict = {var: symbols(var) for var in common_vars.split()}
            symbol_dict.update({"Eq": Eq, "sp": sp})
            
            # Extract any additional variables from the equation string
            import string
            equation_vars = set()
            for char in extraction_result.equation:
                if char in string.ascii_lowercase and char not in symbol_dict:
                    equation_vars.add(char)
            
            # Add any new variables found in the equation
            for var in equation_vars:
                symbol_dict[var] = symbols(var)
            
            # Try to parse and solve the equation
            try:
                # Handle different equation formats
                if "Eq(" in extraction_result.equation:
                    equation = eval(extraction_result.equation, symbol_dict)
                else:
                    expr = eval(extraction_result.equation, symbol_dict)
                    equation = Eq(expr, 0)
                
                # Get all free symbols in the equation
                free_symbols = equation.free_symbols
                print(f"Free symbols: {free_symbols}")
                
                if len(free_symbols) == 1:
                    # Single variable - solve directly
                    variable = list(free_symbols)[0]
                    solutions = solve(equation, variable)
                    
                    if solutions:
                        return self._process_solution(solutions[0], variable, extraction_result.target_expression, symbol_dict)
                
                elif len(free_symbols) > 1:
                    # Multiple variables - identify target variable
                    target_variable = self._identify_target_variable(question_text, free_symbols)
                    
                    if target_variable and target_variable in free_symbols:
                        try:
                            solutions = solve(equation, target_variable)
                            if solutions:
                                return self._process_solution(solutions[0], target_variable, extraction_result.target_expression, symbol_dict)
                        except Exception as e:
                            print(f"Error solving for target variable {target_variable}: {e}")
                    
                    # Fallback: try common variables in order
                    for var_name in ['p', 'x', 'y', 'z', 'q']:
                        var_symbol = symbols(var_name)
                        if var_symbol in free_symbols:
                            try:
                                solutions = solve(equation, var_symbol)
                                if solutions:
                                    return self._process_solution(solutions[0], var_symbol, extraction_result.target_expression, symbol_dict)
                            except Exception as e:
                                print(f"Error solving for {var_symbol}: {e}")
                                continue
                
                return None
                
            except Exception as parse_error:
                print(f"Error parsing equation: {parse_error}")
                return None
                
        except Exception as e:
            print(f"Error in solve_equation_with_sympy: {e}")
            return None
    
    def _identify_target_variable(self, question_text: str, free_symbols):
        """Identify which variable to solve for based on question context"""
        question_lower = question_text.lower()
        
        if "solve for" in question_lower:
            match = re.search(r'solve for ([a-z])', question_lower)
            if match:
                return symbols(match.group(1))
        elif "find" in question_lower and any(var in question_lower for var in ['p-value', 'p value', 'value of p']):
            return symbols('p')
        elif "find" in question_lower:
            match = re.search(r'find.*?([a-z])(?:-value|\s|$)', question_lower)
            if match:
                return symbols(match.group(1))
        
        return None
    
    def _process_solution(self, solution, variable, target_expression_str, symbol_dict):
        """Process and format the solution"""
        simplified_solution = simplify(solution)
        latex_solution = latex(simplified_solution)
        
        result = {
            "variable": str(variable),
            "solution": str(simplified_solution),
            "latex_solution": f"${variable} = {latex_solution}$",
            "numeric_value": float(simplified_solution.evalf()) if simplified_solution.is_real and simplified_solution.free_symbols == set() else None
        }
        
        # Evaluate target expression if specified
        if target_expression_str and target_expression_str != "NONE":
            try:
                target_expr = eval(target_expression_str, symbol_dict)
                evaluated_expr = target_expr.subs(variable, simplified_solution)
                simplified_expr = simplify(evaluated_expr)
                latex_expr = latex(simplified_expr)
                
                result["target_expression"] = target_expression_str
                result["target_value"] = str(simplified_expr)
                result["target_latex"] = f"${target_expression_str} = {latex_expr}$"
                result["target_numeric"] = float(simplified_expr.evalf()) if simplified_expr.is_real and simplified_expr.free_symbols == set() else None
                
                print(f"Evaluated target expression: {target_expression_str} = {simplified_expr}")
            except Exception as e:
                print(f"Error evaluating target expression: {e}")
        
        return result
    
    def _format_result(self, result: Dict[str, Any]) -> str:
        """Format the result for display"""
        output = []
        
        if "target_expression" in result and result["target_expression"] != "NONE":
            print("Target expression found")
            # Question asked for a specific expression
            output.append(f"The value of {result['target_expression']} is: {result['target_value']}")
            if result.get("target_numeric") is not None:
                output.append(f"Numeric value: {result['target_numeric']}")
            if result.get("target_latex"):
                output.append(f"LaTeX: {result['target_latex']}")
        else:
            print("No target expression found")
            # Standard variable solution
            output.append(f"Solution: {result['variable']} = {result['solution']}")
            if result.get("numeric_value") is not None:
                output.append(f"Numeric value: {result['numeric_value']}")
            if result.get("latex_solution"):
                output.append(f"LaTeX: {result['latex_solution']}")
        
        return "\n".join(output)


class MathTutorInput(BaseModel):
    question: str = Field(..., description="A math question in natural language (LaTeX allowed).")
    context: Optional[str] = Field("", description="Optional supporting context retrieved from embeddings.")
    reference_answer: Optional[str] = Field("", description="Optional target answer to anchor explanation.")


class MathTutorTool(BaseTool):
    """Tool for providing step-by-step math explanations"""
    
    name: str = "math_tutor"
    description: str = """
    Provides detailed step-by-step explanations for math problems.
    Input should be a math question with optional context and reference answer.
    """
    args_schema: Type[MathTutorInput] = MathTutorInput
    
    llm: OpenAIWrapper = Field(description="Language model for tutoring")
    
    def __init__(self, llm: OpenAIWrapper, **kwargs):
        super().__init__(llm=llm, **kwargs)
    
    def _run(self, question: str, context: str = "", reference_answer: str = "") -> str:
        prompt = PromptTemplate.from_template(
            """You are a helpful math tutor. Provide a clear, step-by-step solution.

            IMPORTANT: Structure your response EXACTLY as follows:
            SOLUTION: [final answer in LaTeX format]

            EXPLANATION:
            1. [first step with clear reasoning]
            2. [second step with clear reasoning]
            3. [continue until solution is reached]

            {reference_info}

            {context_info}

            Question: {question}

            Response:""")
        
        reference_info = ""
        if reference_answer:
            reference_info = f"REFERENCE: The correct answer is {reference_answer}. Show the steps that lead to this result."
        
        context_info = ""
        if context:
            context_info = f"Context: {context}\n"
        
        try:
            response = self.llm.predict(prompt.format(
                question=question,
                reference_info=reference_info,
                context_info=context_info
            ))
            return response.strip()
        except Exception as e:
            return f"Error generating explanation: {str(e)}"
    
    async def _arun(self, question: str, context: str = "", reference_answer: str = "") -> str:
        return self._run(question, context, reference_answer)


class LaTeXFormatterTool(BaseTool):
    """Tool for formatting math expressions in LaTeX"""
    
    name: str = "latex_formatter"
    description: str = """
    Formats mathematical expressions using proper LaTeX syntax.
    Input should be text containing math expressions that need LaTeX formatting.
    Only wraps math expressions in $...$ tags, keeps other text unchanged.
    """
    
    llm: OpenAIWrapper = Field(description="Language model for LaTeX formatting")
    # llm: ChatOpenAI = Field(description="Language model for LaTeX formatting")
    
    def __init__(self, llm: OpenAIWrapper, **kwargs):
        super().__init__(llm=llm, **kwargs)
    
    def _run(self, text: str) -> str:
        prompt = PromptTemplate.from_template(
            """Format ONLY the math expressions using LaTeX delimiters. 

            STRICT RULES:
            - Do NOT change any words, numbers, variables, or math content.
            - Wrap inline math with $...$ only. Do NOT use \\[...\\] or $$...$$.
            - Do NOT add any commentary or preface. Output ONLY the formatted text.
            - No code fences/backticks.

            Text: {text}

            Formatted version:"""
        )
        try:
            raw = self.llm.predict(prompt.format(text=text))
            cleaned = self._clean_katex_output(raw)
            normalized = self._normalize_latex_delimiters(cleaned)
            return normalized
        except Exception as e:
            return f"Error formatting LaTeX: {str(e)}"
        
    def _clean_katex_output(self, s: str) -> str:
        # strip code fences
        s = re.sub(r"^```(?:latex|tex)?\s*|\s*```$", "", s, flags=re.IGNORECASE | re.MULTILINE)
        # strip a leading "Here is..." boilerplate
        s = re.sub(r"^\s*Here is .*?:\s*", "", s, flags=re.IGNORECASE)
        return s.strip()

    def _normalize_latex_delimiters(self, s: str) -> str:
        # Convert display math to inline to match your renderer
        s = re.sub(r"\\\[(.*?)\\\]", r"$\1$", s, flags=re.S)
        s = re.sub(r"\$\$(.*?)\$\$", r"$\1$", s, flags=re.S)
        # Normalize \( ... \) to $ ... $
        s = re.sub(r"\\\((.*?)\\\)", r"$\1$", s, flags=re.S)
        return s

