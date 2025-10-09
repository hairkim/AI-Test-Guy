# from openai import OpenAI
# from app.extract import pdf_to_images, image_to_base64
# from app.database import SessionLocal
# from app.models import Exam, Section, Question, Solution, EnhancedQuery
# import os, json, re, base64, uuid
# from sqlalchemy.orm import Session
# from supabase import create_client
# from app.models import QuestionEmbedding
# from typing import Optional


# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# def embed_text(text: str) -> list[float]:
#     response = client.embeddings.create(
#         input=text,
#         model="text-embedding-3-small"
#     )
#     return response.data[0].embedding


# def classify_section(base64_img: str) -> str:
#     messages = [
#         {
#             "role": "user",
#             "content": [
#                 {"type": "text", "text": "What section of the SAT is this page from? Answer only one of: Math, Reading, Writing."},
#                 {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_img}"}}
#             ]
#         }
#     ]
#     response = client.chat.completions.create(
#         model="gpt-4o", messages=messages, max_tokens=100
#     )
#     return response.choices[0].message.content.strip()

# def classify_question_to_collection(question: str) -> str:
#     messages = [
#         {
#             "role": "user",
#             "content": (
#                 f"You are a classification assistant. Given a question, return only the name of the most appropriate exam section collection. "
#                 f"The possible collection names are: 'sat_math', 'sat_reading', 'sat_writing'.\n\n"
#                 f"Question: {question}\n\n"
#                 f"Answer with only the collection name, nothing else."
#             )
#         }
#     ]
#     response = client.chat.completions.create(
#         model="gpt-4o",
#         messages=messages,
#         max_tokens=20,
#     )
#     return response.choices[0].message.content.strip()

# def embed_and_answer(session: Session, question_text: str) -> dict:
#     query_vec = embed_text(question_text)

#     # Find most similar questions (top 4)
#     similar = (
#         session.query(QuestionEmbedding)
#         .order_by(QuestionEmbedding.embedding.l2_distance(query_vec))
#         .limit(4)
#         .all()
#     )

#     context = "\n---\n".join(item.text for item in similar)

#     messages = [
#         {"role": "system", "content": "You are an SAT tutor. Use the examples to solve the new question."},
#         {"role": "user", "content": f"Examples:\n{context}\n\nNow solve: {question_text}\nReturn a JSON object with 'answer', 'explanation', and 'steps', where steps is a list of objects each with 'step_num' and 'step_text'. Do not return steps as plain strings.'"}
#     ]
#     response = client.chat.completions.create(
#         model="gpt-4o", messages=messages, max_tokens=3000
#     )

#     match = re.search(r"\{.*\}", response.choices[0].message.content, re.DOTALL)
#     if match:
#         try:
#             return json.loads(match.group())
#         except json.JSONDecodeError:
#             return {}
#     return {"answer": "", "explanation": "", "steps": []}


# def extract_questions(base64_img: str) -> list:
#     prompt = (
#         """You are an AI tutor. Extract all SAT questions from the given image. Return a JSON array of objects, where each object follows this exact structure:

#         [
#             {
#                 "question": "What is 2 + 2?",
#                 "choices": ["A. 3", "B. 4", "C. 5", "D. 6"]
#             }
#         ]

#        Do not include commentary. Do not change the format."""
#     )

#     messages = [
#         {
#             "role": "user",
#             "content": [
#                 {"type": "text", "text": prompt},
#                 {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_img}"}}
#             ]
#         }
#     ]
#     response = client.chat.completions.create(
#         model="gpt-4o", messages=messages, max_tokens=2000
#     )
#     content = response.choices[0].message.content

#     match = re.search(r"\[\s*\{.*\}\s*\]", content, re.DOTALL)
#     if match:
#         try:
#             return json.loads(match.group())
#         except json.JSONDecodeError:
#             return []
#     return []

# def save_to_db(session: Session, exam_name: str, section_name: str, questions: list, base64_img: str):
#     exam = session.query(Exam).filter_by(name=exam_name).first()
#     if not exam:
#         exam = Exam(name=exam_name, description="")
#         session.add(exam)

#     section = session.query(Section).filter_by(name=section_name, exam_id=exam.id).first()
#     if not section:
#         section = Section(name=section_name, exam_id=exam.id)
#         session.add(section)

#     session.commit()  # Commit once after ensuring exam/section exist

#     for q in questions:
#         print("Processing:", q.get("question", ""))
#         img_url = upload_image_to_supabase(base64_img) if "image" in q else None
#         ai_response = embed_and_answer(session, q.get("question", ""))

#         if not isinstance(ai_response, dict):  # Failsafe
#             print("Unexpected AI response:", ai_response)
#             continue

#         question = Question(
#             section_id=section.id,
#             question_text=q.get("question", ""),
#             choices=q.get("choices", []),
#             answer=ai_response.get("answer", ""),
#             explanation=ai_response.get("explanation", ""),
#             image=img_url
#         )
#         session.add(question)
#         session.flush()  # Assigns question.id before adding foreign keys

#         vector = embed_text(q.get("question", ""))
#         embedding_row = QuestionEmbedding(
#             question_id=question.id,
#             text=q.get("question", ""),
#             embedding=vector
#         )
#         session.add(embedding_row)

#         for i, step in enumerate(ai_response.get("steps", []), start=1):
#             if isinstance(step, dict):
#                 step_obj = Solution(
#                     question_id=question.id,
#                     step_num=step.get("step_num", i),
#                     step_text=step.get("step_text", "")
#                 )
#             else:
#                 # step is just a string
#                 step_obj = Solution(
#                     question_id=question.id,
#                     step_num=i,
#                     step_text=str(step)
#                 )
#             session.add(step_obj)

#     session.commit()  # Final commit after all data added


# def process_pdf(pdf_bytes: bytes, exam_name: str):
#     images = pdf_to_images(pdf_bytes)
#     encoded = [image_to_base64(img) for img in images]
#     db = SessionLocal()
#     for img in encoded:
#         section = classify_section(img).strip().lower()
#         if section not in ["math", "reading", "writing"]:
#             print(f"⚠️ Skipping unknown section: {section}")
#             continue
#         questions = extract_questions(img)
#         if questions:
#             save_to_db(db, exam_name, section, questions, img)
#     db.close()


# def process_image_to_question(base64_img: str) -> str:
#     prompt = """
#         You are a math assistant. Given the image of an SAT math question, extract only the question text (not the answer choices), and rewrite it using LaTeX formatting **only** for mathematical expressions.

#         - Keep the natural language intact.
#         - Wrap all math symbols, expressions, variables, and numbers in dollar signs: `$...$`.
#         - Do NOT include answer choices or explanations.
#         - Return only the rewritten question text in one paragraph — no extra commentary.
#     """

#     messages = [
#         {
#             "role": "user",
#             "content": [
#                 {"type": "text", "text": prompt},
#                 {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_img}"}}
#             ]
#         }
#     ]

#     response = client.chat.completions.create(
#         model="gpt-4o",
#         messages=messages,
#         max_tokens=500
#     )

#     return response.choices[0].message.content.strip()

# # Also update your process_image_query_with_gpt function signature
# def process_image_query_with_gpt(query: EnhancedQuery) -> dict:  
#     """
#     Process image query with improved vision capabilities and better question detection
#     Note: Now works with EnhancedQuery which allows question to be None
#     """
#     if query.image is not None:
#         print("iamge was found yes lets goooo")
#     if not query.image:
#         # Handle case where only question text is provided
#         if query.question:
#             return {
#                 "question": query.question,
#                 "usage": "question",
#                 "supporting_explanation": None,
#                 "image_url": None
#             }
#         else:
#             # This shouldn't happen due to validator, but just in case
#             return {
#                 "question": "No question or image provided",
#                 "usage": "error",
#                 "supporting_explanation": None,
#                 "image_url": None
#             }

#     # Rest of the function remains the same...
#     vision_prompt = """
#     You are analyzing an image that may contain a math question or supporting material.
    
#     User input: "{user_input}"
    
#     Your task:
#     1. If the image contains a complete math question (equations, word problems, diagrams with questions), respond with:
#        "QUESTION: [extract the complete question text here]"
    
#     2. If the image contains supporting material (diagrams, graphs, charts, figures) that helps with solving a question, respond with:
#        "SUPPORT: [describe what the image shows and how it relates to math problem solving]"
    
#     3. If the image is unclear or contains no mathematical content, respond with:
#        "UNCLEAR: [brief description of what you see]"
    
#     Be precise and extract mathematical notation carefully. Include all variables, equations, and constraints. You do not need to include the answer choices in your response.
#     """.format(user_input=query.question or "(no text provided)")

#     try:
#         response = client.chat.completions.create(
#             model="gpt-4o",
#             messages=[
#                 {
#                     "role": "user", 
#                     "content": [
#                         {"type": "text", "text": vision_prompt},
#                         {
#                             "type": "image_url", 
#                             "image_url": {
#                                 "url": f"data:image/jpeg;base64,{query.image}",
#                                 "detail": "high"
#                             }
#                         }
#                     ]
#                 }
#             ],
#             max_tokens=1500,
#             temperature=0.1
#         )

#         output = response.choices[0].message.content.strip()
#         print(f"Vision API response: {output}")

#     except Exception as e:
#         print(f"GPT-4 Vision error: {e}")
#         # Fallback: treat as question if user provided text, otherwise return error
#         if query.question and query.question.strip():
#             return {
#                 "question": query.question,
#                 "usage": "question",
#                 "supporting_explanation": "Image processing failed, using text input only",
#                 "image_url": None
#             }
#         else:
#             return {
#                 "question": "Unable to process image. Please provide a text description of your math question.",
#                 "usage": "error",
#                 "supporting_explanation": None,
#                 "image_url": None
#             }

#     # Parse the structured response
#     if output.startswith("QUESTION:"):
#         extracted_question = output.replace("QUESTION:", "").strip()
#         final_question = combine_question_sources(query.question, extracted_question)
        
#         return {
#             "question": final_question,
#             "usage": "question",
#             "supporting_explanation": None,
#             "image_url": upload_image_to_supabase(query.image)
#         }
    
#     elif output.startswith("SUPPORT:"):
#         supporting_text = output.replace("SUPPORT:", "").strip()
#         image_url = upload_image_to_supabase(query.image)
        
#         final_question = query.question or "Please solve the math problem shown in the image."
        
#         return {
#             "question": final_question,
#             "usage": "support",
#             "supporting_explanation": supporting_text,
#             "image_url": image_url
#         }
    
#     else:  # UNCLEAR or unexpected response
#         print(f"Unclear image analysis: {output}")
#         if query.question and query.question.strip():
#             return {
#                 "question": query.question,
#                 "usage": "question",
#                 "supporting_explanation": f"Image analysis unclear: {output}",
#                 "image_url": None
#             }
#         else:
#             return {
#                 "question": "Unable to extract a clear math question from the image. Please provide a text description.",
#                 "usage": "error",
#                 "supporting_explanation": output,
#                 "image_url": None
#             }

# def combine_question_sources(user_text: Optional[str], extracted_text: str) -> str:
#     """
#     Intelligently combine user-provided text with extracted image text
#     """
#     if not user_text or not user_text.strip():
#         return extracted_text
    
#     if not extracted_text or not extracted_text.strip():
#         return user_text
    
#     # If they're very similar, just use the extracted text (likely more complete)
#     user_clean = re.sub(r'\s+', ' ', user_text.lower().strip())
#     extracted_clean = re.sub(r'\s+', ' ', extracted_text.lower().strip())
    
#     if user_clean in extracted_clean or extracted_clean in user_clean:
#         return extracted_text if len(extracted_text) > len(user_text) else user_text
    
#     # If different, combine them
#     return f"{user_text}\n\nAdditional details from image: {extracted_text}"


# def upload_image_to_supabase(base64_str: str) -> str:
#     """
#     Upload image to Supabase storage with better error handling
#     """
#     try:
#         # Decode and validate image
#         image_bytes = base64.b64decode(base64_str)
#         if len(image_bytes) == 0:
#             print("Error: Empty image data")
#             return ""
        
#         # Generate unique filename
#         filename = f"question_{uuid.uuid4().hex}.jpg"
#         filepath = f"question-images/{filename}"

#         # Upload to Supabase
#         res = supabase.storage.from_("question-images").upload(
#             filepath,
#             image_bytes,
#             {"content-type": "image/jpeg", "upsert": "false"}
#         )
        
#         # Check for successful upload
#         if hasattr(res, 'data') and res.data:
#             public_url = f"{SUPABASE_URL}/storage/v1/object/public/question-images/{filename}"
#             print(f"Image uploaded successfully: {public_url}")
#             return public_url
#         else:
#             print(f"Upload failed - Response: {res}")
#             return ""
            
#     except Exception as e:
#         print(f"Error uploading image to Supabase: {e}")
#         return ""


# def validate_image_data(base64_str: str) -> bool:
#     """
#     Validate that the base64 string contains valid image data
#     """
#     try:
#         image_bytes = base64.b64decode(base64_str)
#         # Check if it starts with common image headers
#         if image_bytes.startswith(b'\xff\xd8\xff'):  # JPEG
#             return True
#         elif image_bytes.startswith(b'\x89PNG\r\n\x1a\n'):  # PNG
#             return True
#         elif image_bytes.startswith(b'GIF87a') or image_bytes.startswith(b'GIF89a'):  # GIF
#             return True
#         else:
#             return False
#     except:
#         return False




# #def upload_image_to_supabase(base64_str: str) -> str:
# #     image_bytes = base64.b64decode(base64_str)
# #     filename = f"question_{uuid.uuid4().hex}.png"
# #     filepath = f"question-images/{filename}"

# #     res = supabase.storage.from_("question-images").upload(
# #         filepath,
# #         image_bytes,
# #         {"content-type": "image/png"}
# #     )
# #     if hasattr(res, 'data') and res.data:
# #         return f"{SUPABASE_URL}/storage/v1/object/public/{filepath}"
# #     print("Upload failed:", res)
# #     return ""