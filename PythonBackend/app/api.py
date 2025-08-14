from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.models import EnhancedQuery, EnglishQuery
from app.chain import get_retriever_for_collection
from openai import OpenAI
import os
from app.pipeline import process_pdf, classify_question_to_collection, process_image_query_with_gpt
from app.tools import (
    OpenAIWrapper, MathTutorTool, LaTeXFormatterTool, MathResponseParser,
    MathSolverTool, ExtractMathTool, RetrieveContextTool, SympySolveTool, HuggingFaceWrapper, ModelManager
)
from app.english_tools import EnglishTutorTool, TutorResponseAdapter
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI
from langchain.schema import OutputParserException
import json
from typing import Optional

router = APIRouter()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# model_manager = ModelManager()
# model, tokenizer = model_manager.get_model_and_tokenizer()

llm_wrapper = OpenAIWrapper(client)
# llm = OpenAICompatibleLLM(openai_wrapper=llm_wrapper)
# huggingface_wrapper = HuggingFaceWrapper(model, tokenizer)

# Create tools
math_solver = MathSolverTool(llm=llm_wrapper)
latex_formatter = LaTeXFormatterTool(llm=llm_wrapper)
# math_tutor = MathTutorTool(llm=huggingface_wrapper)
parser = MathResponseParser()
english_tutor = EnglishTutorTool(llm=llm_wrapper)

#this is the old ask question function
@router.post("/ask")
def ask_question(query: EnhancedQuery):
    """Simplified route - no agent, direct tool usage"""
    
    try:
        # print(f"The query: {query.model_dump()}")
        # Step 1: Process image and get question
        image_result = process_image_query_with_gpt(query)
        original_question = image_result["question"]
        print("Question: " + original_question)
        
        # Step 2: Classify and get retriever
        collection = classify_question_to_collection(original_question)
        print("Collection name used:", collection)
        retriever = get_retriever_for_collection(collection)
        
        
        # Step 4: Get SymPy solution first
        sympy_solution = None
        reference_answer = ""
        try:
            sympy_result = math_solver.run(original_question)
            print(f"SymPy result: {sympy_result}")
            
            if "Could not solve" not in sympy_result and "Error" not in sympy_result:
                # Parse the JSON string into a Python dictionary
                try:
                    sympy_data = json.loads(sympy_result)
                    # Access the 'answer' key directly
                    reference_answer = sympy_data.get("answer")
                    
                    # You can also get other values
                    # numeric_value = sympy_data.get("numeric_value")
                    # latex_solution = sympy_data.get("latex_solution")
                    
                    print(f"The reference answer is: {reference_answer}")
                    
                except json.JSONDecodeError:
                    # Handle the case where sympy_result is not valid JSON
                    print("Error: sympy_result is not a valid JSON string.")
                    reference_answer = None
                
                print(f"Reference answer extracted: {reference_answer}")
        except Exception as e:
            print(f"SymPy solving failed: {e}")
        
        # Step 5: Format question in LaTeX
        try:
            latex_question = latex_formatter.run(original_question)
            print(f"LaTeX question: {latex_question}")
        except Exception as e:
            print(f"LaTeX formatting failed: {e}")
            latex_question = original_question
        
        # Step 6: Get context
        try:
            docs_context = retriever.invoke(original_question)
            
            # Debug: Print detailed context information
            print(f"\n=== CONTEXT RETRIEVAL DEBUG ===")
            print(f"Original question: {original_question}")
            print(f"Number of retrieved documents: {len(docs_context)}")
            
            for i, doc in enumerate(docs_context[:2]):
                print(f"\n--- Document {i+1} ---")
                print(f"Content preview (first 200 chars): {doc.page_content[:200]}...")
                if hasattr(doc, 'metadata'):
                    print(f"Metadata: {doc.metadata}")
            
            docs_text = "\n\n".join([doc.page_content for doc in docs_context[:2]])  # Limit to 2 docs
            
            # Add image context if available
            if image_result["usage"] == "support" and image_result["supporting_explanation"]:
                print(f"\nAdding image context: {image_result['supporting_explanation'][:100]}...")
                docs_text = image_result["supporting_explanation"] + "\n\n" + docs_text
            
            print(f"\nFinal context length: {len(docs_text)} characters")
            print(f"Context preview (first 300 chars): {docs_text[:300]}...")
            print("=== END CONTEXT DEBUG ===\n")
            
        except Exception as e:
            print(f"Context retrieval failed: {e}")
            docs_text = ""
        
        # Step 7: Get step-by-step explanation using math tutor
        try:
            tutor_response = math_tutor.run({
                "question": latex_question,
                "context": docs_text[:1000],  # Limit context to prevent token overflow
                "reference_answer": reference_answer
            })
            print(f"Tutor response: {tutor_response}")
        except Exception as e:
            print(f"Math tutor failed: {e}")
            # Fallback response
            tutor_response = f"""SOLUTION: {reference_answer if reference_answer else "Unable to solve"}
            
            EXPLANATION:
            1. An error occurred while generating the explanation: {str(e)}
            2. Please try again or check the SymPy solution above."""
        
        # Step 8: Format the tutor response with LaTeX
        try:
            formatted_answer = latex_formatter.run(tutor_response)
            print(f"Formatted answer: {formatted_answer}")
        except Exception as e:
            print(f"LaTeX formatting of answer failed: {e}")
            formatted_answer = tutor_response
        
        # Step 9: Parse the response
        parsed_result = parser.parse(formatted_answer)
        
        print(f"Parsed result: {parsed_result}")
        
        # Step 10: Return structured response
        return {
            "solution": parsed_result["solution"],
            "explanation_steps": parsed_result["explanation_steps"],
            "answer": formatted_answer,
            "image_url": image_result["image_url"],
            "used_image_as": image_result["usage"],
            "sympy_solution": sympy_solution,
            "debug_info": {
                "reference_answer": reference_answer,
                "tutor_raw": tutor_response if 'tutor_response' in locals() else None,
                "context_length": len(docs_text) if 'docs_text' in locals() else 0
            }
        }

    except Exception as e:
        print(f"Error in ask_question: {e}")
        import traceback
        traceback.print_exc()
        return {
            "solution": "Error occurred while processing the question",
            "explanation_steps": ["An error occurred. Please try again."],
            "answer": "Error occurred",
            "image_url": image_result.get("image_url", "") if 'image_result' in locals() else "",
            "used_image_as": "error",
            "sympy_solution": None
        }


@router.post("/ask_english")
def ask_english(query: EnglishQuery):
    result = english_tutor.run(query.question, query.passage)
    print(result)
    # 2) Normalize to dict
    if isinstance(result, dict):
        data = result
    else:
        try:
            data = json.loads(result)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=422, detail=f"Invalid JSON from model: {e.msg}")
    try:
        resp = TutorResponseAdapter.validate_python(data)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Response validation error: {e}")

    return resp

#this is /ask with agent
#@router.post("/ask")
# def ask_question(query: Query):
#     try:
#         # --- Step 0: Image & question ---
#         image_result = process_image_query_with_gpt(query)
#         original_question = image_result["question"]
#         print("Question:", original_question)

#         # --- Step 1: Retriever for this collection ---
#         collection = classify_question_to_collection(original_question)
#         retriever = get_retriever_for_collection(collection)

#         # --- Step 2: LLMs / tools ---
#         agent_llm = ChatOpenAI(
#             model="gpt-4o",
#             temperature=0,
#             openai_api_key=client.api_key
#         )
#         llm_wrapper = OpenAIWrapper(client)

#         extract_tool = ExtractMathTool(llm=llm_wrapper)
#         sympy_tool   = SympySolveTool()
#         ctx_tool     = RetrieveContextTool(retriever=retriever)
#         tutor_tool   = MathTutorTool(llm=llm_wrapper)
#         fmt_tool     = LaTeXFormatterTool(llm=llm_wrapper)

#         tools = [extract_tool, sympy_tool, ctx_tool, tutor_tool, fmt_tool]

#         # --- Step 3: Use simpler agent type ---
#         prefix = """You are a math assistant that follows these steps:

#             1. First, use extract_math tool with the user's question
#             2. Then, use sympy_solver tool with the extracted equation and target
#             3. Next, use retrieve_context tool with the original question
#             4. Then, use math_tutor tool with the extracted question, context, and solution

#             Complete all steps in order and provide the final formatted response in proper JSON format. DO NOT include any additional text before or after the JSON object. DO NOT use markdown code fences like ```json."""

#         agent = initialize_agent(
#             tools=tools,
#             llm=agent_llm,
#             agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
#             verbose=True,
#             max_iterations=8,
#             handle_parsing_errors=True,  # Let LangChain handle parsing errors
#             agent_kwargs={
#                 "prefix": prefix,
#                 "suffix": """Begin! Remember to use the tools in the specified order.

#                 Question: {input}
#                 {agent_scratchpad}"""
#             }
#         )

#         final_text = agent.invoke(original_question)
#         print("Agent final:", final_text)

#         # --- Step 5: Parse response ---
#         parser = MathResponseParser()
#         parsed = parser.parse(final_text)

#         return {
#             "solution": parsed["solution"],
#             "explanation_steps": parsed["explanation_steps"],
#             # "latex_question": parsed["latex_solution"],
#             "image_url": image_result["image_url"],
#             "used_image_as": image_result["usage"],
#             "sympy_solution": None,
#             "debug_info": {
#                 "collection": collection
#             }
#         }

#     except Exception as e:
#         print("Error in ask_question:", e)
#         return {
#             "solution": "Error occurred while processing the question",
#             "explanation_steps": ["An error occurred. Please try again."],
#             "answer": "Error occurred",
#             "image_url": image_result.get("image_url", "") if 'image_result' in locals() else "",
#             "used_image_as": "error",
#             "sympy_solution": None
#         }

# @router.post("/submit_pdf")
# async def submit_pdf(
#     pdf: UploadFile = File(...),
#     exam_name: str = Form(...)  # <-- exam name input (e.g., "SAT")
# ):
#     if pdf.content_type != "application/pdf":
#         return {"error": "Please upload a valid PDF file."}

#     contents = await pdf.read()
#     process_pdf(contents, exam_name.lower())  # <-- runs classification, extraction, and DB insert

#     return {"message": "✅ PDF processed and questions saved to database."}

# @router.post("/ask")
# def ask_question(query: Query):
#     """Improved route using LangChain tools with OpenAI client"""
    
#     try:
#         # Step 1: Process image and get question
#         image_result = process_image_query_with_gpt(query)
#         original_question = image_result["question"]
#         print("Question: " + original_question)
        
#         # Step 2: Classify and get retriever
#         collection = classify_question_to_collection(original_question)
#         retriever = get_retriever_for_collection(collection)
        
#         # Step 3: Initialize LLM wrapper and tools
#         llm_wrapper = OpenAIWrapper(client)
#         llm = OpenAICompatibleLLM(openai_wrapper=llm_wrapper)
        
#         # Create tools
#         math_solver = MathSolverTool(llm=llm_wrapper)
#         latex_formatter = LaTeXFormatterTool(llm=llm_wrapper)

#         math_tool = LangChainTool(
#             name="math_solver",
#             func=math_solver.run,
#             description=math_solver.description
#         )
#         latex_tool = LangChainTool(
#             name="latex_formatter", 
#             func=latex_formatter.run,
#             description=latex_formatter.description
#         )
        
#         tools = [math_tool, latex_tool]

#         # Step 4: Create agent with better prompt
#         agent = initialize_agent(
#             tools=tools,
#             llm=llm,
#             agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
#             verbose=True,
#             handle_parsing_errors=True,
#             agent_kwargs={
#                 "prefix": """You are a math tutor. When solving problems:
#                 1. Use the math_solver tool to get the correct answer
#                 2. If you get a solution, explain the steps clearly
#                 3. Format your final response as:
#                 SOLUTION: [the answer]
#                 EXPLANATION: 
#                 1. [first step]
#                 2. [second step]
#                 etc.
#                 """
#             }
#         )

#         # Step 5: Get context for enhanced response
#         docs_context = retriever.get_relevant_documents(original_question)
#         docs_text = "\n\n".join([doc.page_content for doc in docs_context[:2]])  # Limit context
        
#         enhanced_question = f"""
#         Solve this math problem: {original_question}
        
#         Use the math_solver tool first to get the correct answer, then provide a clear step-by-step explanation.
        
#         Available context: {docs_text[:500]}
#         """

#         # Step 6: Use agent to solve the question
#         agent_response = agent.run(enhanced_question)
#         print(f"Agent response: {agent_response}")

#         # Step 7: Format agent response in LaTeX
#         formatted_answer = latex_formatter.run(agent_response)
#         print(f"Formatted answer: {formatted_answer}")

#         # Step 8: Parse solution & steps using correct parser
#         parser = MathResponseParser()  # ✅ Correct parser for responses
#         parsed_result = parser.parse(formatted_answer)

#         # Step 9: Use SymPy solver as a backup reference
#         sympy_solution = None
#         try:
#             sympy_result = math_solver.run(original_question)
#             print(f"SymPy backup result: {sympy_result}")
#             sympy_solution = sympy_result
#         except Exception as e:
#             print(f"SymPy solving failed: {e}")

#         # Step 10: Return final structured response
#         return {
#             "solution": parsed_result["solution"],
#             "explanation_steps": parsed_result["explanation_steps"],
#             "answer": formatted_answer,
#             "image_url": image_result["image_url"],
#             "used_image_as": image_result["usage"],
#             "sympy_solution": sympy_solution,
#             "agent_raw_response": agent_response  # For debugging
#         }

#     except Exception as e:
#         print(f"Error in ask_question: {e}")
#         import traceback
#         traceback.print_exc()
#         return {
#             "solution": "Error occurred while processing the question",
#             "explanation_steps": ["An error occurred. Please try again."],
#             "answer": "Error occurred",
#             "image_url": image_result.get("image_url", ""),
#             "used_image_as": "error",
#             "sympy_solution": None
#         }



# def solve_equation_with_sympy(question_text):
#     """
#     Attempts to extract and solve mathematical equations from the question text using SymPy.
#     Also evaluates any target expressions mentioned in the question.
#     Returns the solution if found, otherwise returns None.
#     """
#     try:
#         # Step 1: Extract the equation
#         equation_extraction_prompt = f"""
#         Extract the mathematical equation from this question and convert it to SymPy-compatible format.
        
#         Rules:
#         1. Return ONLY the equation in SymPy format (e.g., "Eq(2*x + 3, 13)")
#         2. Use standard variable names (x, y, z, p, etc.)
#         3. If no solvable equation exists, return "NO_EQUATION"
#         4. For fractions like 3/(13p), write as: 3/(13*p)
#         5. For fractions like (17x)/(5y), write as: (17*x)/(5*y)
#         6. Pay careful attention to parentheses and multiplication
        
#         Examples:
#         - "3/(13p) = (17x)/(5y)" becomes "Eq(3/(13*p), (17*x)/(5*y))"
#         - "2x + 3 = 13" becomes "Eq(2*x + 3, 13)"
        
#         Question: {question_text}
        
#         SymPy equation:
#         """
        
#         # Step 2: Extract target expression to evaluate
#         expression_extraction_prompt = f"""
#         Look at the question below and determine the correct mathematical expression that should be evaluated or solved for.

#         Rules:
#         1. If the question explicitly asks "What is the value of [expression]?", return that expression in SymPy format (e.g., "3/x", "2*x + 1").
#         2. If the question asks to "solve for X", "find the value of X", or "write the X-value in terms of ...", return just the variable (e.g., "x", "p").
#         3. If the question mentions "find", "calculate", or "determine" without specifying an expression but clearly refers to a variable in the equation, return that variable.
#         4. Use the same variable names as in the equation.
#         5. If there is no clear expression or variable to evaluate, return "NONE".
#         6. Do not add any other commentary, just the answer.

#         Examples:
#         - "What is the value of 3/x?" returns "3/x"
#         - "Find 2x + 1" returns "2*x + 1"
#         - "Solve for x" returns "x"
#         - "The given equation relates the positive numbers p, x, and y. Write the p-value in terms of x and y." returns "p"

#         Question: {question_text}

#         Target expression:
#         """
        
#         # Get equation
#         equation_response = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[{"role": "user", "content": equation_extraction_prompt}],
#             max_tokens=200,
#             temperature=0
#         )
        
#         equation_str = equation_response.choices[0].message.content.strip()
#         print(f"Extracted equation: {equation_str}")
        
#         # Get target expression
#         expression_response = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[{"role": "user", "content": expression_extraction_prompt}],
#             max_tokens=100,
#             temperature=0
#         )
        
#         target_expression_str = expression_response.choices[0].message.content.strip()
#         print(f"Target expression: {target_expression_str}")
        
#         if equation_str == "NO_EQUATION" or not equation_str:
#             return None
            
#         # Define common symbols
#         x, y, z, p, q, r, s, t, a, b, c, d = symbols('x y z p q r s t a b c d')
        
#         # Try to parse and solve the equation
#         try:
#             # Handle different equation formats
#             if "Eq(" in equation_str:
#                 # Already in Equation format
#                 equation = eval(equation_str, {"Eq": Eq, "sp": sp, "x": x, "y": y, "z": z, "p": p, "q": q, "r": r, "s": s, "t": t, "a": a, "b": b, "c": c, "d": d})
#             else:
#                 # Assume it's an expression equal to 0
#                 expr = eval(equation_str, {"sp": sp, "x": x, "y": y, "z": z, "p": p, "q": q, "r": r, "s": s, "t": t, "a": a, "b": b, "c": c, "d": d})
#                 equation = Eq(expr, 0)
            
#             # Get all free symbols in the equation
#             free_symbols = equation.free_symbols
#             print(f"Free symbols: {free_symbols}")
            
#             if len(free_symbols) == 1:
#                 # Single variable - solve directly
#                 variable = list(free_symbols)[0]
#                 solutions = solve(equation, variable)
                
#                 if solutions:
#                     # Return the first solution in LaTeX format
#                     solution = solutions[0]
#                     simplified_solution = simplify(solution)
#                     latex_solution = latex(simplified_solution)
                    
#                     result = {
#                         "variable": str(variable),
#                         "solution": str(simplified_solution),
#                         "latex_solution": f"${variable} = {latex_solution}$",
#                         "numeric_value": float(simplified_solution.evalf()) if simplified_solution.is_real and simplified_solution.free_symbols == set() else None
#                     }
                    
#                     # Evaluate target expression if specified
#                     if target_expression_str and target_expression_str != "NONE":
#                         try:
#                             target_expr = eval(target_expression_str, {"sp": sp, "x": x, "y": y, "z": z, "p": p, "q": q, "r": r, "s": s, "t": t, "a": a, "b": b, "c": c, "d": d})
#                             evaluated_expr = target_expr.subs(variable, simplified_solution)
#                             simplified_expr = simplify(evaluated_expr)
#                             latex_expr = latex(simplified_expr)
                            
#                             result["target_expression"] = target_expression_str
#                             result["target_value"] = str(simplified_expr)
#                             result["target_latex"] = f"${target_expression_str} = {latex_expr}$"
#                             result["target_numeric"] = float(simplified_expr.evalf()) if simplified_expr.is_real and simplified_expr.free_symbols == set() else None
                            
#                             print(f"Evaluated target expression: {target_expression_str} = {simplified_expr}")
#                         except Exception as e:
#                             print(f"Error evaluating target expression: {e}")
                    
#                     return result
#             elif len(free_symbols) > 1:
#                 # Multiple variables - identify which variable to solve for based on question context
#                 target_variable = None
                
#                 # Look for phrases that indicate which variable to solve for
#                 question_lower = question_text.lower()
#                 if "solve for" in question_lower:
#                     # Extract variable after "solve for"
#                     match = re.search(r'solve for ([a-z])', question_lower)
#                     if match:
#                         target_variable = symbols(match.group(1))
#                 elif "find" in question_lower and any(var in question_lower for var in ['p-value', 'p value', 'value of p']):
#                     target_variable = symbols('p')
#                 elif "find" in question_lower:
#                     # Look for "find x" or "find the value of x"
#                     match = re.search(r'find.*?([a-z])(?:-value|\s|$)', question_lower)
#                     if match:
#                         target_variable = symbols(match.group(1))
                
#                 # If we identified a target variable, solve for it first
#                 if target_variable and target_variable in free_symbols:
#                     try:
#                         solutions = solve(equation, target_variable)
#                         if solutions:
#                             solution = solutions[0]
#                             simplified_solution = simplify(solution)
#                             latex_solution = latex(simplified_solution)
                            
#                             result = {
#                                 "variable": str(target_variable),
#                                 "solution": str(simplified_solution),
#                                 "latex_solution": f"${target_variable} = {latex_solution}$",
#                                 "numeric_value": float(simplified_solution.evalf()) if simplified_solution.is_real and simplified_solution.free_symbols == set() else None
#                             }
                            
#                             # Evaluate target expression if specified
#                             if target_expression_str and target_expression_str != "NONE":
#                                 try:
#                                     target_expr = eval(target_expression_str, {"sp": sp, "x": x, "y": y, "z": z, "p": p, "q": q, "r": r, "s": s, "t": t, "a": a, "b": b, "c": c, "d": d})
#                                     evaluated_expr = target_expr.subs(target_variable, simplified_solution)
#                                     simplified_expr = simplify(evaluated_expr)
#                                     latex_expr = latex(simplified_expr)
                                    
#                                     result["target_expression"] = target_expression_str
#                                     result["target_value"] = str(simplified_expr)
#                                     result["target_latex"] = f"${target_expression_str} = {latex_expr}$"
#                                     result["target_numeric"] = float(simplified_expr.evalf()) if simplified_expr.is_real and simplified_expr.free_symbols == set() else None
                                    
#                                     print(f"Evaluated target expression: {target_expression_str} = {simplified_expr}")
#                                 except Exception as e:
#                                     print(f"Error evaluating target expression: {e}")
                            
#                             return result
#                     except Exception as e:
#                         print(f"Error solving for target variable {target_variable}: {e}")
                
#                 # Fallback: try common variables in order
#                 for var_name in ['p', 'x', 'y', 'z', 'q']:
#                     var_symbol = symbols(var_name)
#                     if var_symbol in free_symbols:
#                         try:
#                             solutions = solve(equation, var_symbol)
#                             if solutions:
#                                 solution = solutions[0]
#                                 simplified_solution = simplify(solution)
#                                 latex_solution = latex(simplified_solution)
                                
#                                 result = {
#                                     "variable": str(var_symbol),
#                                     "solution": str(simplified_solution),
#                                     "latex_solution": f"${var_symbol} = {latex_solution}$",
#                                     "numeric_value": None  # Usually involves other variables
#                                 }
                                
#                                 # Evaluate target expression if specified
#                                 if target_expression_str and target_expression_str != "NONE":
#                                     try:
#                                         target_expr = eval(target_expression_str, {"sp": sp, "x": x, "y": y, "z": z, "p": p, "q": q, "r": r, "s": s, "t": t, "a": a, "b": b, "c": c, "d": d})
#                                         evaluated_expr = target_expr.subs(var_symbol, simplified_solution)
#                                         simplified_expr = simplify(evaluated_expr)
#                                         latex_expr = latex(simplified_expr)
                                        
#                                         result["target_expression"] = target_expression_str
#                                         result["target_value"] = str(simplified_expr)
#                                         result["target_latex"] = f"${target_expression_str} = {latex_expr}$"
#                                         result["target_numeric"] = float(simplified_expr.evalf()) if simplified_expr.is_real and simplified_expr.free_symbols == set() else None
                                        
#                                         print(f"Evaluated target expression: {target_expression_str} = {simplified_expr}")
#                                     except Exception as e:
#                                         print(f"Error evaluating target expression: {e}")
                                
#                                 return result
#                         except Exception as e:
#                             print(f"Error solving for {var_symbol}: {e}")
#                             continue
            
#             return None
            
#         except Exception as parse_error:
#             print(f"Error parsing equation: {parse_error}")
#             return None
            
#     except Exception as e:
#         print(f"Error in solve_equation_with_sympy: {e}")
#         return None

#writing the question in latex format
# latex_prompt = PromptTemplate.from_template(
#     """You are a math formatting assistant. Your task is to rewrite the following SAT math question using proper LaTeX syntax, but only for the math parts.

# - Do **not** rewrite the entire sentence in LaTeX.
# - Only wrap individual math expressions (equations, variables, fractions, exponents, etc.) in dollar signs: `$...$`.
# - Keep all natural language, instructions, and non-math text exactly as-is.
# - Do **not** repeat or rephrase the math expressions outside of LaTeX.
# - Only include the rewritten sentence — no explanations, no extra commentary.

# Question:
# {question}

# Rewritten version:"""
# )

# #formatting the answer and the explanations in latex format
# latex_answer_prompt = PromptTemplate.from_template(
#     """Format the following math explanation using LaTeX for all math expressions.

# - Keep the sentence structure and logic.
# - Only wrap math expressions with `$...$`.
# - Do NOT reword the explanation.

# Explanation:
# {explanation}

# Formatted version:"""
# )

# latex_chain = LLMChain(llm=ChatOpenAI(), prompt=latex_prompt)
# latex_answer_chain = LLMChain(llm=ChatOpenAI(), prompt=latex_answer_prompt)

# qa_prompt = PromptTemplate.from_template(
#     """You are a helpful math tutor. Use the following context to answer the question in a clear and detailed way.

# IMPORTANT: Structure your response as follows:
# 1. Start with "SOLUTION:" followed by the final answer
# 2. Then "EXPLANATION:" followed by numbered steps
# 3. Use LaTeX formatting for all math expressions (wrap in $...$ for inline math)
# 4. Each step should be clear and build upon the previous one
# 5. Include the reasoning behind each step
# 6. Do not continue after reaching the correct answer in its simplest form.
#    - If the solution is already simplified, **do not perform further rearrangements or rewrites**.
#    - Avoid unnecessary steps that alter or restate the correct answer.

# {sympy_reference}

# Example format:
# SOLUTION: $x = 5$

# EXPLANATION:
# 1. **Identify the equation**: We have $2x + 3 = 13$
# 2. **Isolate the variable**: Subtract $3$ from both sides: $2x = 10$
# 3. **Solve for x**: Divide both sides by $2$: $x = 5$
# 4. **Verify**: Substitute back: $2(5) + 3 = 13$ ✓

# Context:
# {context}

# Question:
# {question}

# Answer:""")

# @router.post("/ask")
# def ask_question(query: Query):
#     # Step 1: Analyze image
#     image_result = process_image_query_with_gpt(query)

#     # Step 2: Classify question text
#     collection = classify_question_to_collection(image_result["question"])
#     retriever = get_retriever_for_collection(collection)

#     # Step 3: Format question using LaTeX
#     latex_question = latex_chain.run(question=image_result["question"])
#     print("Question: ", image_result["question"])
#     print("Latex question: ", latex_question)

#     # Step 3.5: Solve equation with SymPy
#     sympy_solution = solve_equation_with_sympy(image_result["question"])
#     sympy_reference = ""
    
#     if sympy_solution:
#         print(f"SymPy found solution: {sympy_solution}")
#         sympy_reference = f"""
#         REFERENCE ANSWER: The correct answer is {sympy_solution['latex_solution']}.
#         Use this as the target solution and work backwards to show the steps that lead to this answer.
#         Make sure your explanation leads to exactly this result.
#         """
#     else:
#         print("No SymPy solution found, proceeding with context-based solving")
#         sympy_reference = ""

#     # Step 4: Build context
#     docs_context = retriever.get_relevant_documents(latex_question)
#     docs_text = "\n\n".join([doc.page_content for doc in docs_context])

#     if image_result["usage"] == "support" and image_result["supporting_explanation"]:
#         docs_text = image_result["supporting_explanation"] + "\n\n" + docs_text

#     # Step 5: Answer using context
#     qa_chain = LLMChain(
#         llm=ChatOpenAI(),
#         prompt=qa_prompt
#     )
#     answer = qa_chain.run({
#         "context": docs_text,
#         "question": latex_question,
#         "sympy_reference": sympy_reference
#     })
#     print("Answer: ", answer)

#     # Step 6: Format answer in LaTeX
#     latex_answer = latex_answer_chain.run(explanation=answer)
#     print("Latex answer: ", latex_answer)
    
#     # Step 7: Parse structured response
#     solution = ""
#     explanation_steps = []
    
#     if "SOLUTION:" in latex_answer and "EXPLANATION:" in latex_answer:
#         print("Found solution and explanation")
#         parts = latex_answer.split("EXPLANATION:")
#         solution = parts[0].replace("SOLUTION:", "").strip()
        
#         explanation_text = parts[1].strip()
#         # Split by numbered steps (1., 2., 3., etc.)
#         import re
#         steps = re.split(r'\n(?=\d+\.)', explanation_text)
#         explanation_steps = [step.strip() for step in steps if step.strip()]
#         print("Explanation steps:", explanation_steps)
#     else:
#         # Fallback if format isn't followed
#         solution = latex_answer
#         explanation_steps = [latex_answer]

#     return {
#         "solution": solution,
#         "explanation_steps": explanation_steps,
#         "answer": latex_answer,  # Keep for backward compatibility
#         "image_url": image_result["image_url"],
#         "used_image_as": image_result["usage"],
#         "sympy_solution": sympy_solution  # Include SymPy solution for debugging/transparency
#     }




        # Step 4: Skip agent creation since we need LangChain LLM for agents
        # We'll use direct tool calls instead (which is actually simpler!)
        
    #     # Step 5: Try to solve with SymPy first
    #     sympy_solution = None
    #     reference_answer = ""
        
    #     try:
    #         sympy_result = math_solver.run(original_question)
    #         if "Could not solve" not in sympy_result and "Error" not in sympy_result:
    #             sympy_solution = sympy_result
    #             # Extract just the answer for reference
    #             if "=" in sympy_result:
    #                 reference_answer = sympy_result.split('\n')[0]
    #             print(f"SymPy solution found: {reference_answer}")
    #     except Exception as e:
    #         print(f"SymPy solving failed: {e}")
        
    #     # Step 6: Build context from retriever
    #     latex_question = latex_formatter.run(original_question)
    #     docs_context = retriever.get_relevant_documents(latex_question)
    #     docs_text = "\n\n".join([doc.page_content for doc in docs_context])
        
    #     # Add image context if available
    #     if image_result["usage"] == "support" and image_result["supporting_explanation"]:
    #         docs_text = image_result["supporting_explanation"] + "\n\n" + docs_text
        
    #     # Step 7: Get comprehensive solution using direct tool calls
    #     try:
    #         # Use the math tutor tool directly instead of agent
    #         agent_response = math_solver.run(
    #             question=latex_question,
    #             context=docs_text[:1000],
    #             reference_answer=reference_answer
    #         )
    #     except Exception as e:
    #         print(f"Math tutor tool failed: {e}")
    #         # Fallback to a simple response
    #         agent_response = f"SOLUTION: Unable to solve\nEXPLANATION:\n1. An error occurred: {str(e)}"
        
    #     # Step 8: Parse the response
    #     parser = MathExtractionParser()
    #     parsed_response = parser.parse(agent_response)
        
    #     # Step 9: Format final answer with LaTeX
    #     formatted_answer = latex_formatter.run(parsed_response["full_response"])
        
    #     # Re-parse formatted answer
    #     final_parsed = parser.parse(formatted_answer)
        
    #     return {
    #         "solution": final_parsed["solution"],
    #         "explanation_steps": final_parsed["explanation_steps"],
    #         "answer": formatted_answer,
    #         "image_url": image_result["image_url"],
    #         "used_image_as": image_result["usage"],
    #         "sympy_solution": sympy_solution,
    #         "agent_used": False,  # We're using direct tool calls instead
    #         "tools_available": [tool.name for tool in tools]
    #     }
        
    # except Exception as e:
    #     print(f"Error in ask_question: {e}")
    #     return {
    #         "error": str(e),
    #         "solution": "Error occurred while processing the question",
    #         "explanation_steps": ["An error occurred. Please try again."],
    #         "answer": "Error occurred",
    #         "image_url": image_result.get("image_url", ""),
    #         "used_image_as": "error",
    #         "sympy_solution": None
    #     }


    
