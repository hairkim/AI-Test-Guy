from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.models import EnhancedQuery, EnglishQuery
from app.chain import get_retriever_for_collection
from openai import OpenAI
import os
from functools import lru_cache
from app.tools import (
    OpenAIWrapper, MathTutorTool, LaTeXFormatterTool, MathResponseParser,
    MathSolverTool, ExtractMathTool, RetrieveContextTool, SympySolveTool,
)
from app.threeagenttutor import ConversationalSATTutor
from app.english_tutor_agent import ConversationalEnglishSATTutor
from app.mathtools import create_math_tutor
from app.english_tools import EnglishTutorTool, TutorResponseAdapter, create_enhanced_tutor
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI
from langchain.schema import OutputParserException
import json
from typing import Optional
from app.pipeline import process_image_query_with_gpt, classify_question_to_collection

router = APIRouter()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

WOLFRAM_APPID = os.getenv("WOLFRAM_APPID")

@lru_cache(maxsize=1)
def get_toolbox():
    """Create tools once, lazily, in-process."""
    llm_wrapper = OpenAIWrapper(client)
    sat_tutor = ConversationalSATTutor(llm_wrapper, WOLFRAM_APPID)
    toolbox = {
        "llm_wrapper": llm_wrapper,
        "math_solver": MathSolverTool(llm=llm_wrapper),
        "math_tutor":  MathTutorTool(llm=llm_wrapper),  
        "latex_formatter": LaTeXFormatterTool(llm=llm_wrapper),
        "parser": MathResponseParser(),
        "english_tutor": create_enhanced_tutor(llm_wrapper, enable_ml=True),
        "sat_tutor": sat_tutor,
        "sat_english_tutor": ConversationalEnglishSATTutor(llm_wrapper)
    }
    return toolbox

#global toolbox for all tools
tb = get_toolbox()

@router.post("/ask")
def ask(query: EnhancedQuery):
    """Enhanced SAT Math question handler with comprehensive error handling"""
    sat_tutor = tb["sat_tutor"]
    
    # Use the new agent
    solution = sat_tutor.solve(query.question)
    
    return {
        "solution": solution
    }


@router.post("/ask_english")
def ask_english(query: EnglishQuery):
    """Enhanced SAT English question handler with comprehensive error handling"""

    #load all of the tools once
    english_tutor     = tb["sat_english_tutor"]
    
    # Use the new agent
    solution = english_tutor.solve(query.question, query.passage if query.passage else None)
    
    return {
        "solution": solution
    }

#this is the old ask question function
# @router.post("/ask")
# def ask_question(query: EnhancedQuery):
#     """Simplified route - no agent, direct tool usage"""
    
#     #load all of the tools once
#     tb = get_toolbox()
#     math_solver       = tb["math_solver"]
#     math_tutor        = tb["math_tutor"]
#     latex_formatter   = tb["latex_formatter"]
#     parser            = tb["parser"]
#     try:
#         # print(f"The query: {query.model_dump()}")
#         # Step 1: Process image and get question
#         image_result = process_image_query_with_gpt(query)
#         original_question = image_result["question"]
#         print("Question: " + original_question)
        
#         # Step 2: Classify and get retriever
#         collection = classify_question_to_collection(original_question)
#         print("Collection name used:", collection)
#         retriever = get_retriever_for_collection(collection)
        
        
#         # Step 4: Get SymPy solution first
#         sympy_solution = None
#         reference_answer = ""
#         try:
#             sympy_result = math_solver.run(original_question)
#             print(f"SymPy result: {sympy_result}")
            
#             if "Could not solve" not in sympy_result and "Error" not in sympy_result:
#                 # Parse the JSON string into a Python dictionary
#                 try:
#                     sympy_data = json.loads(sympy_result)
#                     # Access the 'answer' key directly
#                     reference_answer = sympy_data.get("answer")
                    
#                     # You can also get other values
#                     # numeric_value = sympy_data.get("numeric_value")
#                     # latex_solution = sympy_data.get("latex_solution")
                    
#                     print(f"The reference answer is: {reference_answer}")
                    
#                 except json.JSONDecodeError:
#                     # Handle the case where sympy_result is not valid JSON
#                     print("Error: sympy_result is not a valid JSON string.")
#                     reference_answer = None
                
#                 print(f"Reference answer extracted: {reference_answer}")
#         except Exception as e:
#             print(f"SymPy solving failed: {e}")
        
#         # Step 5: Format question in LaTeX
#         try:
#             latex_question = latex_formatter.run(original_question)
#             print(f"LaTeX question: {latex_question}")
#         except Exception as e:
#             print(f"LaTeX formatting failed: {e}")
#             latex_question = original_question
        
#         # Step 6: Get context
#         try:
#             docs_context = retriever.invoke(original_question)
            
#             # Debug: Print detailed context information
#             print(f"\n=== CONTEXT RETRIEVAL DEBUG ===")
#             print(f"Original question: {original_question}")
#             print(f"Number of retrieved documents: {len(docs_context)}")
            
#             for i, doc in enumerate(docs_context[:2]):
#                 print(f"\n--- Document {i+1} ---")
#                 print(f"Content preview (first 200 chars): {doc.page_content[:200]}...")
#                 if hasattr(doc, 'metadata'):
#                     print(f"Metadata: {doc.metadata}")
            
#             docs_text = "\n\n".join([doc.page_content for doc in docs_context[:2]])  # Limit to 2 docs
            
#             # Add image context if available
#             if image_result["usage"] == "support" and image_result["supporting_explanation"]:
#                 print(f"\nAdding image context: {image_result['supporting_explanation'][:100]}...")
#                 docs_text = image_result["supporting_explanation"] + "\n\n" + docs_text
            
#             print(f"\nFinal context length: {len(docs_text)} characters")
#             print(f"Context preview (first 300 chars): {docs_text[:300]}...")
#             print("=== END CONTEXT DEBUG ===\n")
            
#         except Exception as e:
#             print(f"Context retrieval failed: {e}")
#             docs_text = ""
        
#         # Step 7: Get step-by-step explanation using math tutor
#         try:
#             tutor_response = math_tutor.run({
#                 "question": latex_question,
#                 "context": docs_text[:1000],  # Limit context to prevent token overflow
#                 "reference_answer": reference_answer
#             })
#             print(f"Tutor response: {tutor_response}")
#         except Exception as e:
#             print(f"Math tutor failed: {e}")
#             # Fallback response
#             tutor_response = f"""SOLUTION: {reference_answer if reference_answer else "Unable to solve"}
            
#             EXPLANATION:
#             1. An error occurred while generating the explanation: {str(e)}
#             2. Please try again or check the SymPy solution above."""
        
#         # Step 8: Format the tutor response with LaTeX
#         try:
#             formatted_answer = latex_formatter.run(tutor_response)
#             print(f"Formatted answer: {formatted_answer}")
#         except Exception as e:
#             print(f"LaTeX formatting of answer failed: {e}")
#             formatted_answer = tutor_response
        
#         # Step 9: Parse the response
#         parsed_result = parser.parse(formatted_answer)
        
#         print(f"Parsed result: {parsed_result}")
        
#         # Step 10: Return structured response
#         return {
#             "solution": parsed_result["solution"],
#             "explanation_steps": parsed_result["explanation_steps"],
#             "answer": formatted_answer,
#             "image_url": image_result["image_url"],
#             "used_image_as": image_result["usage"],
#             "sympy_solution": sympy_solution,
#             "debug_info": {
#                 "reference_answer": reference_answer,
#                 "tutor_raw": tutor_response if 'tutor_response' in locals() else None,
#                 "context_length": len(docs_text) if 'docs_text' in locals() else 0
#             }
#         }

#     except Exception as e:
#         print(f"Error in ask_question: {e}")
#         import traceback
#         traceback.print_exc()
#         return {
#             "solution": "Error occurred while processing the question",
#             "explanation_steps": ["An error occurred. Please try again."],
#             "answer": "Error occurred",
#             "image_url": image_result.get("image_url", "") if 'image_result' in locals() else "",
#             "used_image_as": "error",
#             "sympy_solution": None
#         }

# @router.post("/ask")
# def ask(query: EnhancedQuery):
#     tb = get_toolbox()
#     math_agent = create_math_tutor(tb["llm_wrapper"], wolfram_app_id=WOLFRAM_APPID)
    
#     # Process image
#     image_result = process_image_query_with_gpt(query)
#     question = image_result["question"]
    
#     # Use the new agent
#     solution = math_agent.solve(question, image_result.get("supporting_explanation"))
    
#     return {
#         "solution": solution.answer,
#         "explanation_steps": solution.steps,
#         "answer": solution.explanation,
#         "confidence": solution.confidence,
#         "method": solution.method_used
#     }