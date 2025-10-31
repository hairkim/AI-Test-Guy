from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser
from langchain.tools import BaseTool
from pydantic import Field, BaseModel
import re, json
from langchain.llms.base import LLM
from typing import Optional, Dict, Any, Type, List
import sympy as sp
from sympy import symbols, Eq, solve, simplify, latex, sqrt, pi, cos, sin, tan, asin, acos, atan
from sympy.geometry import Point, Line, Circle, Triangle, Polygon, Ray, Segment
from sympy.geometry.util import intersection
import textwrap
import string
from pydantic import ConfigDict
import math
import requests
import os


from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
)
TRANSFORMS = standard_transformations + (implicit_multiplication_application,)

WOLFRAM_APPID = os.getenv("WOLFRAM_APPID")


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
                max_tokens=1500,
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error calling OpenAI: {str(e)}"

    def predict_with_image(self, prompt: str, image_base64: str, model: str = "gpt-4o", temperature: float = 0) -> str:
        """
        Make prediction with image input using OpenAI's vision capabilities.
        
        Args:
            prompt: Text prompt/question
            image_base64: Base64 encoded image (with or without data URL prefix)
            model: Vision-capable model (gpt-4o, gpt-4o-mini, or gpt-4-vision-preview)
            temperature: Sampling temperature
            
        Returns:
            Model's response text
        """
        try:
            # Clean the base64 string if it has a data URL prefix
            if ',' in image_base64:
                image_base64 = image_base64.split(',', 1)[1]
            
            # Create the message with both text and image
            response = self.client.chat.completions.create(
                model=model,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "high"  # Can be "low", "high", or "auto"
                            }
                        }
                    ]
                }],
                max_tokens=1500,
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error calling OpenAI vision: {str(e)}"

class OpenAICompatibleLLM(LLM):
    openai_wrapper: OpenAIWrapper

    def _call(self, prompt: str, stop=None):
        return self.openai_wrapper.predict(prompt)

    @property
    def _llm_type(self):
        return "openai-wrapper"

class MathExtractionOutput(BaseModel):
    """Output schema for math extraction"""
    problem_type: str = Field(description="Type of math problem (algebra/geometry/trigonometry)")
    equations: List[str] = Field(description="List of equations/constraints")
    target_variable: str = Field(description="Variable or expression to solve for")
    given_values: Dict[str, Any] = Field(description="Known values and constraints")
    problem_context: str = Field(description="Additional context about the problem")

class MathExtractionParser(BaseOutputParser[MathExtractionOutput]):
    """Parser for enhanced math extraction output"""
    
    def parse(self, text: str) -> MathExtractionOutput:
        try:
            if isinstance(text, dict):
                text = str(text)
            
            raw = text.strip()
            raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
            raw = re.sub(r"```$", "", raw).strip()

            if raw.startswith("{"):
                data = json.loads(raw)
                return MathExtractionOutput(**data)

            # Fallback parsing
            return MathExtractionOutput(
                problem_type="unknown",
                equations=[],
                target_variable="x",
                given_values={},
                problem_context=""
            )

        except Exception:
            return MathExtractionOutput(
                problem_type="unknown",
                equations=[],
                target_variable="x",
                given_values={},
                problem_context=""
            )
    
    def get_format_instructions(self) -> str:
        return """Return the result in JSON format with the following structure:
        {
            "problem_type": "algebra|geometry|trigonometry",
            "equations": ["list of equations in SymPy format"],
            "target_variable": "variable or expression to solve for",
            "given_values": {"variable": "value", ...},
            "problem_context": "additional context about the problem"
        }"""

class MathResponseParser(BaseOutputParser):
    """Parser for JSON-structured math responses"""

    def parse(self, text: str) -> Dict[str, Any]:
        print("reached parse function")
        # Ensure text is a string
        if isinstance(text, dict):
            # text is already structured; serialize properly
            text = json.dumps(text, ensure_ascii=False)
        
        try:
            # Clean up any markdown code fences
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE|re.MULTILINE)
            
            # Parse JSON
            result = json.loads(cleaned)
            print("Result:", result)
        
            # Ensure required fields exist
            if "solution" not in result:
                result["solution"] = "No solution found"
                if "explanation_steps" not in result:
                    result["explanation_steps"] = []
                if "full_response" not in result:
                    result["full_response"] = text
                
            return result
        
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "solution": "Parse error - invalid JSON format",
                "explanation_steps": ["Failed to parse response"],
                "full_response": text,
                "parse_error": True
            }

class MathSolverTool(BaseTool):
    """LangChain tool for solving all types of SAT math problems"""

    model_config = ConfigDict(extra='allow')
    
    name: str = "math_solver"
    description: str = """
    Solves comprehensive SAT math problems including algebra, geometry, and trigonometry.
    Handles linear/quadratic equations, systems, inequalities, geometric calculations, and trig problems.
    Input should be a mathematical question in natural language.
    """
    
    llm: OpenAIWrapper = Field(description="Language model for problem analysis")
    
    def __init__(self, llm: OpenAIWrapper, **kwargs):
        super().__init__(llm=llm, **kwargs)

        self.functions = {
            "algebra": self.solve_algebra_problem,
            "geometry": self.solve_geometry_problem,
            "trigonometry": self.solve_trigonometry_problem,
        }
        
    def _run(self, question_text: str) -> str:
        """Execute with multiple Wolfram query attempts"""
        try:
            if isinstance(question_text, dict):
                question_text = str(question_text)

            extraction_result = self.extract_problem_structure(question_text)
            print(f"Extraction result: {extraction_result}")

            query = ", ".join(extraction_result.equations)
            print("Checking with equations: " + query)
            recognizer_data = self.wolfram_fast_query(query)
            if recognizer_data.get("success"):
                print("Wolfram recognized the question")
                
                # Try short answer first
                short_ans = self.wolfram_short_answer(query)
                print(f"Short answer: '{short_ans}'")
                
                # Check if short answer is good
                if self.is_good_short_answer(short_ans):
                    return json.dumps({
                        "question": question_text,
                        "answer": short_ans,
                        "numeric_value": self._try_parse_number(short_ans),
                        "latex_solution": f"${short_ans}$",
                        "target_variable": extraction_result.target_variable
                    })
                
                # Try full results
                full_results = self.wolfram_full_results(query)
                pods = full_results.get("queryresult", {}).get("pods", [])
                
                parsed_answer = self.parse_wolfram_result(pods)
                if parsed_answer and self.is_good_answer(parsed_answer):
                    return json.dumps({
                        "question": question_text,
                        "answer": parsed_answer,
                        "numeric_value": self._try_parse_number(parsed_answer),
                        "latex_solution": f"${parsed_answer}$",
                        "target_variable": extraction_result.target_variable
                    })
        
        except Exception as e:
            return json.dumps({
                "question": question_text,
                "answer": f"Error: {str(e)}",
                "numeric_value": None,
                "latex_solution": "Error occurred",
                "target_variable": None
            })
        
        # try:
        #     if isinstance(question_text, dict):
        #         question_text = str(question_text)

        #     extraction_result = self.extract_problem_structure(question_text)
        #     print(f"Extraction result: {extraction_result}")

        #     # 1. Check Wolfram recognition
        #     wolfram_query = ", ".join(extraction_result.equations)
        #     print("Checking with equations: " + wolfram_query)
        #     recognizer_data = self.wolfram_fast_query(wolfram_query)
        #     if recognizer_data.get("success"):
        #         print("Wolfram recognized the question")
        #         # 2. Try Short Answer first
        #         short_ans = self.wolfram_short_answer(wolfram_query)
        #         print("Short answer:", short_ans)
                
        #         # Simple heuristics for "bad" short answers
        #         bad_short = (
        #             not short_ans or
        #             "Assuming" in short_ans or
        #             "Wolfram" in short_ans or
        #             len(short_ans.split()) > 8  # short answers should be short
        #         )


        #         if not bad_short:
        #             print("Returning short answer")
        #             return json.dumps({
        #                 "question": question_text,
        #                 "answer": short_ans,
        #                 "numeric_value": self._try_parse_number(short_ans),
        #                 "latex_solution": short_ans,  # or wrap in $...$ if needed
        #                 "target_variable": None
        #             })
                
        #         # 3. Fallback to Full Results
        #         print("Returning full results")
        #         full_results = self.wolfram_full_results(wolfram_query)
        #         print(f"Full results: {full_results}")
        #         pods = full_results.get("queryresult", {}).get("pods", [])
        #         # Get first non-empty plaintext result
        #         for pod in pods:
        #             for subpod in pod.get("subpods", []):
        #                 ans_text = subpod.get("plaintext", "")
        #                 if ans_text:
        #                     return json.dumps({
        #                         "question": question_text,
        #                         "answer": ans_text,
        #                         "numeric_value": self._try_parse_number(ans_text),
        #                         "latex_solution": ans_text,
        #                         "target_variable": None
        #                     })

        
        #     # Extract problem structure
        #     #this is sympy approach
            
        # #     if extraction_result.problem_type == "unknown":
        # #         return json.dumps({
        # #             "question": question_text,
        # #             "answer": "Could not determine problem type",
        # #             "numeric_value": None,
        # #             "latex_solution": "Unknown problem type",
        # #             "target_variable": None
        # #         })
            
        # #     # Route to appropriate solver
        # #     solver_func = self.functions.get(extraction_result.problem_type)
        # #     if solver_func:
        # #         result = solver_func(question_text, extraction_result)
        # #         if result:
        # #             return json.dumps(result)
            
        # #     return json.dumps({
        # #         "question": question_text,
        # #         "answer": "Could not solve the problem",
        # #         "numeric_value": None,
        # #         "latex_solution": "No solution found",
        # #         "target_variable": extraction_result.target_variable
        # #     })
            
        # except Exception as e:
        #     return json.dumps({
        #         "question": question_text,
        #         "answer": f"Error: {str(e)}",
        #         "numeric_value": None,
        #         "latex_solution": "Error occurred",
        #         "target_variable": None
        #     })
    
    async def _arun(self, question_text: str) -> str:
        """Async version - just calls the sync version"""
        return self._run(question_text)

    def extract_problem_structure(self, question_text: str) -> MathExtractionOutput:
        """Extract problem structure and classify problem type"""
        try:
            if isinstance(question_text, dict):
                question_text = str(question_text)

            extraction_prompt = PromptTemplate(
                input_variables=["question"],
                template="""
Analyze this SAT math problem and return one JSON object with the following keys:

problem_type - one of "algebra", "geometry", or "trigonometry".

equations - a list containing exactly one string that is a Wolfram|Alpha-ready query.

CRITICAL SYNTAX RULES FOR WOLFRAM ALPHA:

FOR RATIO PROBLEMS:
- If the target expression contains the inverse ratio of the given one (e.g., given a/b but need to solve for b/a), first find the inverse. For `a/b = 2`, the inverse is `b/a = 1/2`.
- Then, rewrite the target expression and substitute the value. For "4b/a", this becomes "4 * (1/2)".

FOR SOLVING EQUATIONS:
- "solve 2x + 3 = 7 for x"
- "solve system y = 2x, y = x + 10 for x"

FOR GEOMETRY:
- "area of triangle base 10 height 5"
- "distance between (1,2) and (4,6)"

Choose the FIRST method that fits the pattern. For ratio problems like a/b = 2, prefer Method 1 or Method 5.

target_variable - the specific variable or expression to output.

given_values - a JSON object of known values/relations.

problem_context - a brief description.

Examples:
- "If a/b = 2, what is 4b/a?" → ["4b/a with a = 2b"]
- "If x = 3, what is x^2 + 1?" → ["x^2 + 1 with x = 3"]
- "Find x if 2x + 3 = 7" → ["solve 2x + 3 = 7 for x"]
- "If sin(θ) = 0.6, find cos(θ)" → ["cos(theta) with sin(theta) = 0.6"]

Return only the JSON object.
Question: {question}

{format_instructions}
                """,
                partial_variables={"format_instructions": MathExtractionParser().get_format_instructions()}
            )
            
            parser = MathExtractionParser()
            prompt_text = extraction_prompt.format(question=question_text)
            
            llm_response = self.llm.predict(prompt_text)
            response = parser.parse(llm_response)
            print(f"the response........: {response}")
            return response
            
        except Exception as e:
            print(f"Error in extraction: {e}")
            return MathExtractionOutput(
                problem_type="unknown",
                equations=[],
                target_variable="x",
                given_values={},
                problem_context=""
            )

    #######################
    #Wolfram tools
    #######################
    def wolfram_fast_query(self, query: str) -> dict:
        """Check if Wolfram can interpret the query."""
        url = f"http://api.wolframalpha.com/v2/query"
        params = {
            "input": query,
            "appid": WOLFRAM_APPID,
            "output": "JSON",
            "format": "plaintext",
            "reinterpret": "true",  # try to help with interpretation
            "includepodid": "Input", # minimal
        }
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        # Wolfram JSON structure: queryresult.success indicates recognition
        return data.get("queryresult", {})

    def wolfram_short_answer(self,query: str) -> str:
        """Get short plain-text answer."""
        url = "https://api.wolframalpha.com/v1/result"
        params = {"i": query, "appid": WOLFRAM_APPID}
        resp = requests.get(url, params=params)
        if resp.status_code == 200:
            return resp.text.strip()
        return ""

    def wolfram_full_results(self,query: str) -> dict:
        """Get full JSON results (pods, subpods)."""
        url = "http://api.wolframalpha.com/v2/query"
        params = {"input": query, "appid": WOLFRAM_APPID, "output": "JSON", "format": "plaintext"}
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    def _try_parse_number(self, s):
        try:
            return float(s)
        except:
            return None

    def is_good_short_answer(self, answer: str) -> bool:
        """Check if a short answer is actually useful"""
        if not answer:
            return False
        
        bad_indicators = [
            "Assuming", "Wolfram", "undefined", "error", "No",
            len(answer.split()) > 10,  # Too long
            answer.startswith("{"),    # Set notation
            answer.startswith("(") and answer.count("(") > 2,  # Complex expression
        ]
        
        return not any(bad_indicators)

    def is_good_answer(self, answer: str) -> bool:
        """Check if a parsed answer is actually useful"""
        if not answer:
            return False
        
        # Good answers are typically short and numerical
        good_indicators = [
            answer.replace(".", "").replace("-", "").isdigit(),  # Pure number
            len(answer.split()) <= 3,  # Short
            not answer.startswith("{"),  # Not set notation
            not "undefined" in answer.lower(),
        ]
        
        return any(good_indicators)

    def parse_wolfram_result(self, pods):
        """Enhanced parsing specifically for mathematical results"""
        
        # Look for specific pod types in priority order
        priority_titles = ["Result", "Exact result", "Decimal approximation", "Value", "Solution"]
        
        for title in priority_titles:
            for pod in pods:
                if pod.get("title", "").lower().startswith(title.lower()):
                    for subpod in pod.get("subpods", []):
                        text = subpod.get("plaintext", "").strip()
                        if text and len(text) < 20:  # Keep it short
                            return self.clean_wolfram_answer(text)
        
        # Fallback: look for any short numerical result
        for pod in pods:
            if pod.get("title", "").lower() in ["input", "plot", "3d plot", "contour plot"]:
                continue
                
            for subpod in pod.get("subpods", []):
                text = subpod.get("plaintext", "").strip()
                # Look for short, potentially numerical answers
                if text and len(text) < 15 and not text.startswith("{"):
                    cleaned = self.clean_wolfram_answer(text)
                    if cleaned.replace(".", "").replace("-", "").replace(" ", "").replace("/", "").isalnum():
                        return cleaned
        
        return None

    def clean_wolfram_answer(self, text: str) -> str:
        """Clean Wolfram answer with better logic"""
        # Remove common artifacts
        text = text.replace("×", "*").replace("≈", "").strip()
        
        # Handle fractions and simple expressions
        if "/" in text and len(text.split()) <= 2:
            return text
        
        # Handle equations like "expression = value"
        if " = " in text:
            parts = text.split(" = ")
            # Return the simpler part (usually the right side)
            if len(parts) == 2:
                right = parts[1].strip()
                left = parts[0].strip()
                # Prefer numbers over expressions
                if right.replace(".", "").replace("-", "").isdigit():
                    return right
                elif left.replace(".", "").replace("-", "").isdigit():
                    return left
        
        # Remove parentheses around simple expressions
        if text.startswith("(") and text.endswith(")") and text.count("(") == 1:
            inner = text[1:-1]
            if len(inner.split()) <= 3:
                return inner
        
        return text

    #######################
    #######################


    #this is the sympy approach
    def solve_algebra_problem(self, question_text: str, extraction: MathExtractionOutput) -> Optional[Dict[str, Any]]:
        """Solve algebraic problems including linear, quadratic, systems, and inequalities"""
        try:
            # Create comprehensive symbol dictionary
            symbol_names = 'x y z p q r s t a b c d e f g h i j k l m n o u v w'
            symbol_dict = {var: symbols(var) for var in symbol_names.split()}
            symbol_dict.update({"Eq": Eq, "sp": sp, "sqrt": sqrt, "pi": pi})
            
            equations = []
            for eq_str in extraction.equations:
                try:
                    if "Eq(" in eq_str:
                        eq = eval(eq_str, symbol_dict)
                        equations.append(eq)
                    elif "=" in eq_str:
                        left, right = eq_str.split("=", 1)
                        left_expr = parse_expr(left.strip(), transformations=TRANSFORMS)
                        right_expr = parse_expr(right.strip(), transformations=TRANSFORMS)
                        equations.append(Eq(left_expr, right_expr))
                    elif "<" in eq_str or ">" in eq_str or "<=" in eq_str or ">=" in eq_str:
                        # Handle inequalities
                        for op in ["<=", ">=", "<", ">"]:
                            if op in eq_str:
                                left, right = eq_str.split(op, 1)
                                left_expr = parse_expr(left.strip(), transformations=TRANSFORMS)
                                right_expr = parse_expr(right.strip(), transformations=TRANSFORMS)
                                # Store as equation for now, handle inequality logic separately
                                equations.append((left_expr, op, right_expr))
                                break
                    else:
                        # Treat as expression equal to zero
                        expr = parse_expr(eq_str, transformations=TRANSFORMS)
                        equations.append(Eq(expr, 0))
                except Exception as e:
                    print(f"Error parsing equation {eq_str}: {e}")
                    continue
            
            if not equations:
                return None
            
            # Determine target variable
            target_var = symbols(extraction.target_variable.strip()) if extraction.target_variable else symbols('x')
            
            # Handle different algebraic problem types
            if len(equations) == 1:
                eq = equations[0]
                
                # Handle inequality
                if isinstance(eq, tuple):
                    left_expr, op, right_expr = eq
                    # Solve inequality
                    from sympy import solve_univariate_inequality
                    try:
                        if op == "<":
                            inequality = left_expr < right_expr
                        elif op == ">":
                            inequality = left_expr > right_expr
                        elif op == "<=":
                            inequality = left_expr <= right_expr
                        elif op == ">=":
                            inequality = left_expr >= right_expr
                        
                        solution = solve_univariate_inequality(inequality, target_var, relational=False)
                        return self._format_algebra_result(question_text, solution, target_var, f"inequality_{op}")
                    except:
                        # Fallback to regular equation solving
                        eq = Eq(left_expr, right_expr)
                
                # Regular equation solving
                print(f"DEBUG: About to solve equation: {eq}")
                print(f"DEBUG: Target variable: {target_var}")
                print(f"DEBUG: Equation type: {type(eq)}")
                solutions = solve(eq, target_var)
                if solutions:
                    return self._format_algebra_result(question_text, solutions[0], target_var, "equation")
            
            elif len(equations) > 1:
                # System of equations
                # Get all free symbols to solve for multiple variables if needed
                all_symbols = set()
                for eq in equations:
                    if hasattr(eq, 'free_symbols'):
                        all_symbols.update(eq.free_symbols)
                
                if len(all_symbols) <= len(equations):
                    try:
                        solution = solve(equations, list(all_symbols))
                        if solution and target_var in solution:
                            return self._format_algebra_result(question_text, solution[target_var], target_var, "system")
                        elif solution:
                            # Return first solution if target not specifically found
                            first_var = list(solution.keys())[0]
                            return self._format_algebra_result(question_text, solution[first_var], first_var, "system")
                    except Exception as e:
                        print(f"System solving error: {e}")
            
            return None
            
        except Exception as e:
            print(f"Error in solve_algebra_problem: {e}")
            return None

    def solve_geometry_problem(self, question_text: str, extraction: MathExtractionOutput) -> Optional[Dict[str, Any]]:
        """Solve geometric problems including area, perimeter, volume, coordinate geometry"""
        try:
            # Parse geometric problem using LLM to identify specific calculation needed
            geometry_prompt = f"""
            Analyze this geometry problem and determine what calculation is needed:
            
            Problem: {question_text}
            Context: {extraction.problem_context}
            Target: {extraction.target_variable}
            
            Common calculations:
            - Area of triangle: (1/2) * base * height or using coordinates
            - Area of circle: π * r²
            - Area of rectangle: length * width
            - Perimeter calculations
            - Volume calculations
            - Distance formula: √[(x2-x1)² + (y2-y1)²]
            - Coordinate geometry
            
            Return the specific formula and values needed as JSON:
            {{
                "calculation_type": "area_triangle|area_circle|area_rectangle|perimeter|volume|distance|other",
                "formula": "mathematical formula",
                "values": {{"parameter": "value"}},
                "steps": ["step1", "step2", ...]
            }}
            """
            
            llm_response = self.llm.predict(geometry_prompt)
            
            try:
                # Clean and parse response
                cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", llm_response.strip(), flags=re.IGNORECASE)
                calc_data = json.loads(cleaned)
                
                calc_type = calc_data.get("calculation_type", "other")
                formula = calc_data.get("formula", "")
                values = calc_data.get("values", {})
                
                # Perform the calculation based on type
                result = self._perform_geometry_calculation(calc_type, formula, values)
                
                if result is not None:
                    return {
                        "question": question_text,
                        "answer": str(result),
                        "numeric_value": float(result) if isinstance(result, (int, float)) else None,
                        "latex_solution": f"${extraction.target_variable} = {latex(result) if hasattr(result, '__str__') else result}$",
                        "target_variable": extraction.target_variable
                    }
                    
            except Exception as e:
                print(f"Geometry calculation error: {e}")
            
            return None
            
        except Exception as e:
            print(f"Error in solve_geometry_problem: {e}")
            return None

    def solve_trigonometry_problem(self, question_text: str, extraction: MathExtractionOutput) -> Optional[Dict[str, Any]]:
        """Solve trigonometry problems including basic trig functions and identities"""
        try:
            # Parse trigonometric problem
            trig_prompt = f"""
            Analyze this trigonometry problem:
            
            Problem: {question_text}
            Target: {extraction.target_variable}
            
            Common patterns:
            - Given sin(θ), find cos(θ) or tan(θ)
            - Given sides of right triangle, find angles
            - Given angle, find trig ratios
            - Pythagorean identity: sin²(θ) + cos²(θ) = 1
            - SOH-CAH-TOA relationships
            
            Return calculation details as JSON:
            {{
                "trig_function": "sin|cos|tan|arcsin|arccos|arctan",
                "given_info": {{"parameter": "value"}},
                "relationship": "pythagorean|sohcahtoa|given_ratio|other",
                "calculation_steps": ["step1", "step2", ...]
            }}
            """
            
            llm_response = self.llm.predict(trig_prompt)
            
            try:
                cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", llm_response.strip(), flags=re.IGNORECASE)
                trig_data = json.loads(cleaned)
                
                # Perform trigonometric calculation
                result = self._perform_trig_calculation(trig_data, extraction)
                
                if result is not None:
                    return {
                        "question": question_text,
                        "answer": str(result),
                        "numeric_value": float(result) if isinstance(result, (int, float)) else None,
                        "latex_solution": f"${extraction.target_variable} = {latex(result) if hasattr(result, '__str__') else result}$",
                        "target_variable": extraction.target_variable
                    }
                    
            except Exception as e:
                print(f"Trig calculation error: {e}")
            
            return None
            
        except Exception as e:
            print(f"Error in solve_trigonometry_problem: {e}")
            return None

    def _perform_geometry_calculation(self, calc_type: str, formula: str, values: Dict) -> Any:
        """Perform specific geometry calculations"""
        try:
            if calc_type == "area_triangle":
                if "base" in values and "height" in values:
                    base = float(values["base"])
                    height = float(values["height"])
                    return 0.5 * base * height
                elif "side1" in values and "side2" in values and "side3" in values:
                    # Heron's formula
                    a, b, c = float(values["side1"]), float(values["side2"]), float(values["side3"])
                    s = (a + b + c) / 2
                    return sqrt(s * (s - a) * (s - b) * (s - c))
            
            elif calc_type == "area_circle":
                if "radius" in values:
                    r = float(values["radius"])
                    return pi * r * r
                elif "diameter" in values:
                    d = float(values["diameter"])
                    return pi * (d/2) * (d/2)
            
            elif calc_type == "area_rectangle":
                if "length" in values and "width" in values:
                    length = float(values["length"])
                    width = float(values["width"])
                    return length * width
            
            elif calc_type == "distance":
                if "x1" in values and "y1" in values and "x2" in values and "y2" in values:
                    x1, y1 = float(values["x1"]), float(values["y1"])
                    x2, y2 = float(values["x2"]), float(values["y2"])
                    return sqrt((x2 - x1)**2 + (y2 - y1)**2)
            
            elif calc_type == "volume":
                if "sphere" in formula.lower() and "radius" in values:
                    r = float(values["radius"])
                    return (4/3) * pi * r**3
                elif "cylinder" in formula.lower() and "radius" in values and "height" in values:
                    r = float(values["radius"])
                    h = float(values["height"])
                    return pi * r**2 * h
            
            # Try to evaluate formula directly if provided
            if formula and values:
                # Replace variables in formula with values
                eval_formula = formula
                for var, val in values.items():
                    eval_formula = eval_formula.replace(var, str(val))
                
                # Safe evaluation with sympy
                symbol_dict = {"pi": pi, "sqrt": sqrt, "**": "**"}
                try:
                    result = eval(eval_formula, symbol_dict)
                    return simplify(result)
                except:
                    pass
            
            return None
            
        except Exception as e:
            print(f"Geometry calculation error: {e}")
            return None

    def _perform_trig_calculation(self, trig_data: Dict, extraction: MathExtractionOutput) -> Any:
        """Perform trigonometric calculations"""
        try:
            given_info = trig_data.get("given_info", {})
            relationship = trig_data.get("relationship", "")
            
            # Handle Pythagorean identity cases
            if relationship == "pythagorean":
                if "sin" in given_info:
                    sin_val = float(given_info["sin"])
                    if "cos" in extraction.target_variable.lower():
                        cos_val = sqrt(1 - sin_val**2)
                        return cos_val
                    elif "tan" in extraction.target_variable.lower():
                        cos_val = sqrt(1 - sin_val**2)
                        return sin_val / cos_val
                
                elif "cos" in given_info:
                    cos_val = float(given_info["cos"])
                    if "sin" in extraction.target_variable.lower():
                        sin_val = sqrt(1 - cos_val**2)
                        return sin_val
                    elif "tan" in extraction.target_variable.lower():
                        sin_val = sqrt(1 - cos_val**2)
                        return sin_val / cos_val
            
            # Handle SOH-CAH-TOA cases
            elif relationship == "sohcahtoa":
                if "opposite" in given_info and "hypotenuse" in given_info:
                    opp = float(given_info["opposite"])
                    hyp = float(given_info["hypotenuse"])
                    if "sin" in extraction.target_variable.lower():
                        return opp / hyp
                
                elif "adjacent" in given_info and "hypotenuse" in given_info:
                    adj = float(given_info["adjacent"])
                    hyp = float(given_info["hypotenuse"])
                    if "cos" in extraction.target_variable.lower():
                        return adj / hyp
                
                elif "opposite" in given_info and "adjacent" in given_info:
                    opp = float(given_info["opposite"])
                    adj = float(given_info["adjacent"])
                    if "tan" in extraction.target_variable.lower():
                        return opp / adj
            
            # Handle inverse trig functions
            if "arcsin" in extraction.target_variable.lower() or "asin" in extraction.target_variable.lower():
                if "sin" in given_info:
                    return asin(float(given_info["sin"]))
            elif "arccos" in extraction.target_variable.lower() or "acos" in extraction.target_variable.lower():
                if "cos" in given_info:
                    return acos(float(given_info["cos"]))
            elif "arctan" in extraction.target_variable.lower() or "atan" in extraction.target_variable.lower():
                if "tan" in given_info:
                    return atan(float(given_info["tan"]))
            
            return None
            
        except Exception as e:
            print(f"Trig calculation error: {e}")
            return None

    def _format_algebra_result(self, question: str, solution: Any, target_var: Any, problem_type: str) -> Dict[str, Any]:
        """Format algebraic solution results"""
        try:
            simplified_solution = simplify(solution)
            latex_solution = latex(simplified_solution)
            
            # Try to get numeric value
            numeric_value = None
            try:
                if simplified_solution.is_real and simplified_solution.free_symbols == set():
                    numeric_value = float(simplified_solution.evalf())
                elif hasattr(simplified_solution, 'evalf'):
                    # Try to evaluate even if it has symbols (might be a constant)
                    eval_result = simplified_solution.evalf()
                    if eval_result.is_real and eval_result.free_symbols == set():
                        numeric_value = float(eval_result)
            except:
                pass
            
            return {
                "question": question,
                "answer": str(simplified_solution),
                "numeric_value": numeric_value,
                "latex_solution": f"${target_var} = {latex_solution}$",
                "target_variable": str(target_var)
            }
            
        except Exception as e:
            return {
                "question": question,
                "answer": str(solution),
                "numeric_value": None,
                "latex_solution": f"${target_var} = {solution}$",
                "target_variable": str(target_var)
            }


class MathTutorInput(BaseModel):
    question: str = Field(..., description="A math question in natural language (LaTeX allowed).")
    context: Optional[str] = Field("", description="Optional supporting context retrieved from embeddings.")
    reference_answer: Optional[str] = Field("", description="Optional target answer to anchor explanation.")


class MathTutorTool(BaseTool):
    """Tool for providing step-by-step math explanations with JSON output"""
    
    name: str = "math_tutor"
    description: str = """
    Provides detailed step-by-step explanations for math problems.
    Input should be a math question with optional context and reference answer.
    Returns structured JSON response.
    """
    args_schema: Type[MathTutorInput] = MathTutorInput
    
    llm: OpenAIWrapper = Field(description="Language model for tutoring")
    
    def __init__(self, llm: OpenAIWrapper, **kwargs):
        super().__init__(llm=llm, **kwargs)
    
    def _run(self, question: str, context: str = "", reference_answer: str = "") -> str:
        # Ensure all inputs are strings
        if isinstance(question, dict):
            question = str(question)
        if isinstance(context, dict):
            context = str(context)
        if isinstance(reference_answer, dict):
            reference_answer = str(reference_answer)
        
        prompt = PromptTemplate.from_template(
            """You are a helpful math tutor. Solve the problem step-by-step and return your response in JSON format.

            CRITICAL: Return ONLY a JSON object with this exact structure (NO ADDITIONAL TEXT, NO MARKDOWN FENCES, NO \n NEWLINES OR SPACES):
{{
"solution": "Final answer in LaTeX format with $ delimiters (e.g., '$p = \\\\frac{{15y}}{{221x}}$')",
"explanation_steps": [
{{
"step": "Step 1: Clear description of first step with reasoning",
"method": "Mathematical technique used (e.g., 'Substitution', 'Cross-multiplication', 'Factoring') (MAKE SURE TO NOT ADD ANY MORE COMMENTARY ON THIS ROW)"
}},
{{
"step": "Step 2: Clear description of second step with reasoning",
"method": "Mathematical technique used (e.g., 'Algebraic manipulation', 'Simplification')"
}},
{{
"step": "Step 3: Continue until solution is reached",
"method": "Mathematical technique used (e.g., 'Solving for variable', 'Final calculation')"
}}
],
"latex_solution": "LaTeX only without $ delimiters (e.g., 'p = \\\\frac{{15y}}{{221x}}')",
"method": "Brief description of the overall method used (e.g., 'cross-multiplication and algebraic manipulation')"
}}

            Rules:
            - Use double backslashes (\\\\) for LaTeX commands in JSON strings
            - Each explanation step should be a complete sentence with its corresponding method
            - Using the context_info, provide the explanations for each step
            - Each step's method should be a concise mathematical technique name
            - The solution should include $ delimiters for proper rendering
            - Do NOT include any text before or after the JSON object
            - Do NOT use markdown code fences like ```json
            - Do NOT add spaces before or after the JSON data

            {reference_info}

            {context_info}

            Question: {question}""")
        
        reference_info = ""
        if reference_answer:
            reference_info = f"REFERENCE: The correct final answer MUST be {reference_answer}. Ensure your solution field shows exactly this value."
        
        context_info = ""
        if context:
            context_info = f"Context: {context}"
        
        try:
            response = self.llm.predict(prompt.format(
                question=question,
                reference_info=reference_info,
                context_info=context_info
            ))
            return response.strip()
        except Exception as e:
            # Return error in JSON format
            error_response = {
                "solution": f"Error: {str(e)}",
                "explanation_steps": ["An error occurred while generating the explanation"],
                "latex_solution": "Error",
                "method": "Error"
            }
            return json.dumps(error_response)
    
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
    
    def __init__(self, llm: OpenAIWrapper, **kwargs):
        super().__init__(llm=llm, **kwargs)
    
    def _run(self, text: str) -> str:
        # Ensure text is a string
        if isinstance(text, dict):
            text = str(text)
        
        prompt = PromptTemplate.from_template(
            """Format ONLY the math expressions using LaTeX delimiters. 

            STRICT RULES:
            - Do NOT change any words, numbers, variables, or math content.
            - Wrap inline math with $...$ only. Do NOT use \\[...\\] or $$...$$.
            - Do NOT add any commentary or preface. Output ONLY the formatted text.
            - No code fences/backticks.
            - Make sure that if the math expression is a string, keep it in string format.

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
        # Ensure s is a string
        if isinstance(s, dict):
            s = str(s)
        # strip code fences
        s = re.sub(r"^```(?:latex|tex)?\s*|\s*```$", "", s, flags=re.IGNORECASE | re.MULTILINE)
        # strip a leading "Here is..." boilerplate
        s = re.sub(r"^\s*Here is .*?:\s*", "", s, flags=re.IGNORECASE)
        return s.strip()

    def _normalize_latex_delimiters(self, s: str) -> str:
        # Ensure s is a string
        if isinstance(s, dict):
            s = str(s)
        # Convert display math to inline to match your renderer
        s = re.sub(r"\\\[(.*?)\\\]", r"$\1$", s, flags=re.S)
        s = re.sub(r"\$\$(.*?)\$\$", r"$\1$", s, flags=re.S)
        # Normalize \( ... \) to $ ... $
        s = re.sub(r"\\\((.*?)\\\)", r"$\1$", s, flags=re.S)
        return s


class ExtractMathInput(BaseModel):
    question: str = Field(..., description="Raw user question in natural language (may include LaTeX).")

class ExtractMathOutput(BaseModel):
    plain_question: str
    latex_question: str
    sympy_equation: str        # e.g. "Eq(3/(13*p), 17*x/(5*y))" or "NO_EQUATION"
    target_expression: str     # e.g. "p" or "3/x" or "NONE"

class ExtractMathTool(BaseTool):
    name: str = "extract_math"
    description: str = (
        "Extracts the mathematical structure from a question. "
        "Returns JSON with: plain_question, latex_question, sympy_equation, target_expression."
    )
    args_schema: Type[ExtractMathInput] = ExtractMathInput
    llm: OpenAIWrapper = Field(description="LLM used to extract equation/target.")

    def __init__(self, llm: OpenAIWrapper, **kwargs):
        super().__init__(llm=llm, **kwargs)

    def _run(self, question: str) -> str:
        # Ensure question is a string
        if isinstance(question, dict):
            question = str(question)
        
        # Strict prompt: JSON only, no fences
        prompt = PromptTemplate.from_template(textwrap.dedent("""
            Analyze the question and output ONLY one JSON object (no prose, no backticks) with keys:
            - "plain_question": same question, plain English
            - "latex_question": question with inline math wrapped in $...$
            - "sympy_equation": SymPy-compatible equation like "Eq(3/(13*p), 17*x/(5*y))" or "NO_EQUATION"
            - "target_expression": expression/variable to evaluate (e.g., "p", "3/x") or "NONE"

            Rules:
            - Use '*' for multiplication, e.g., 13*p
            - If the question says "write p in terms of ..." or "solve for p", set target_expression="p"
            - Do not include code fences/backticks.
            - Only output valid JSON.

            Question: {question}
        """))
        raw = self.llm.predict(prompt.format(question=question), model="gpt-4o-mini", temperature=0)

        # Defensive cleaning: strip any accidental fences
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.IGNORECASE|re.MULTILINE)

        # Validate JSON
        try:
            data = json.loads(cleaned)
        except Exception:
            # Fallback minimal extraction if model failed JSON
            data = {
                "plain_question": question,
                "latex_question": question,
                "sympy_equation": "NO_EQUATION",
                "target_expression": "NONE",
            }
        # Return as string (agents exchange strings)
        return json.dumps(data)

    async def _arun(self, question: str) -> str:
        return self._run(question)


class SympySolveInput(BaseModel):
    sympy_equation: str = Field(..., description='e.g. "Eq(3/(13*p), 17*x/(5*y))"')
    target_expression: str = Field(..., description='variable/expression to evaluate, e.g. "p" or "NONE"')

class SympySolveTool(BaseTool):
    name: str = "sympy_solver"
    description: str = (
        "Solves a SymPy equation and (optionally) evaluates a target expression. "
        "Input must include sympy_equation and target_expression."
    )
    args_schema: Type[SympySolveInput] = SympySolveInput

    def _run(self, sympy_equation: str, target_expression: str) -> str:
        # Ensure inputs are strings
        if isinstance(sympy_equation, dict):
            sympy_equation = str(sympy_equation)
        if isinstance(target_expression, dict):
            target_expression = str(target_expression)
        
        # Build symbol environment
        common_vars = 'x y z p q r s t a b c d e f g h i j k l m n o u v w'
        symbol_dict = {v: symbols(v) for v in common_vars.split()}
        symbol_dict.update({"Eq": Eq, "sp": sp})

        out: Dict[str, Any] = {
            "status": "ok",
            "solution_symbol": None,
            "solution_expr": None,
            "solution_latex": None,
            "target_expression": target_expression,
            "target_value": None,
            "target_latex": None,
        }

        try:
            if sympy_equation == "NO_EQUATION":
                out["status"] = "no_equation"
                return json.dumps(out)

            # Parse Eq(...) or expression
            if "Eq(" in sympy_equation:
                eq = eval(sympy_equation, symbol_dict)
            else:
                expr = eval(sympy_equation, symbol_dict)
                eq = Eq(expr, 0)

            free = list(eq.free_symbols)
            # Determine variable to solve from target_expression if single symbol
            solve_var = None
            if target_expression and target_expression != "NONE":
                # if target looks like a single symbol, solve for it
                if re.fullmatch(r"[a-z]", target_expression.strip()):
                    solve_var = symbols(target_expression.strip())

            # fallback: single var equation or pick p/x/y
            if solve_var is None:
                if len(free) == 1:
                    solve_var = free[0]
                else:
                    for name in ["p", "x", "y", "z", "q"]:
                        s = symbols(name)
                        if s in free:
                            solve_var = s
                            break

            if solve_var is None:
                out["status"] = "no_solve_var"
                return json.dumps(out)

            sols = solve(eq, solve_var)
            if not sols:
                out["status"] = "no_solution"
                return json.dumps(out)

            sol = simplify(sols[0])
            out["solution_symbol"] = str(solve_var)
            out["solution_expr"] = str(sol)
            out["solution_latex"] = f"${solve_var} = {latex(sol)}$"

            # Evaluate target expression if provided and not a single symbol same as solve_var
            if target_expression and target_expression != "NONE":
                try:
                    target_expr = eval(target_expression, symbol_dict)
                    evaluated = simplify(target_expr.subs(solve_var, sol))
                    out["target_value"] = str(evaluated)
                    out["target_latex"] = f"${target_expression} = {latex(evaluated)}$"
                except Exception:
                    # ignore eval errors
                    pass

            return json.dumps(out)

        except Exception as e:
            out["status"] = "error"
            out["error"] = str(e)
            return json.dumps(out)

    async def _arun(self, sympy_equation: str, target_expression: str) -> str:
        return self._run(sympy_equation, target_expression)


class RetrieveContextInput(BaseModel):
    query: str = Field(..., description="Natural language query to retrieve context for.")
    k: int = Field(2, description="Top-k documents to concatenate.")
    max_chars: int = Field(1800, description="Soft cap on returned context length.")

class RetrieveContextTool(BaseTool):
    name: str = "retrieve_context"
    description: str = "Retrieves top-k text snippets from the vector DB for grounding the explanation."
    args_schema: Type[RetrieveContextInput] = RetrieveContextInput

    def __init__(self, retriever, **kwargs):
        super().__init__(**kwargs)
        self._retriever = retriever

    def _run(self, query: str, k: int = 2, max_chars: int = 1800) -> str:
        try:
            # Ensure query is a string
            if isinstance(query, dict):
                query = str(query)
            
            docs = self._retriever.invoke(query)  # new Runnable API
            docs = docs[:k]
            
            # Handle cases where docs might be dicts or have different structures
            ctx_parts = []
            for d in docs:
                if hasattr(d, 'page_content'):
                    ctx_parts.append(d.page_content)
                elif isinstance(d, dict) and 'page_content' in d:
                    ctx_parts.append(d['page_content'])
                elif isinstance(d, dict) and 'content' in d:
                    ctx_parts.append(d['content'])
                elif isinstance(d, str):
                    ctx_parts.append(d)
                else:
                    ctx_parts.append(str(d))
            
            ctx = "\n\n".join(ctx_parts)
            print("Context length:", len(ctx))
            return ctx[:max_chars]
        except Exception as e:
            print("Error retrieving context:", e)
            return ""

    async def _arun(self, query: str, k: int = 2, max_chars: int = 1800) -> str:
        return self._run(query, k, max_chars)