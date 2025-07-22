from fastapi import APIRouter, UploadFile, File
from app.models import Query
from app.chain import qa_chain
from app.extract import pdf_to_images, image_to_base64
import pdfplumber
from openai import OpenAI
import json
import os
import re


router = APIRouter()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@router.post("/ask")
def ask_question(query: Query):
    answer = qa_chain.run(query.question)
    return {"answer": answer}


@router.post("/submit_pdf")
async def submit_pdf(pdf: UploadFile = File(...)):
    if pdf.content_type != "application/pdf":
        return {"error": "Please upload a valid PDF file."}
    
    contents = await pdf.read()
    images = pdf_to_images(contents)
    encoded_images = [image_to_base64(img) for img in images]

    formatted_data = []

    for base64_img in encoded_images:
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "You are an AI tutor trained to extract multiple SAT Math questions from an image. "
                            "For each question found in the image, extract and return the following in JSON format:\n\n"
                            "{\n"
                            "  \"question\": \"...\",\n"
                            "  \"choices\": [\"A. ...\", \"B. ...\", \"C. ...\", \"D. ...\"],\n"
                            "  \"answer\": \"...\",\n"
                            "  \"explanation\": \"...\",\n"
                            "  \"image\": \"(optional, only include if a diagram or visual is necessary and cannot be easily described in text)\"\n"
                            "}\n\n"
                            "Return a JSON array of such objects. Do not include the image key unless the visual is essential. "
                            "If the diagram or equation can be described in text or LaTeX, do not include an image key."
                        )
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_img}"
                        }
                    }
                ]
            }
        ]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=1000
        )

        content = response.choices[0].message.content

        try:
            json_array_match = re.search(r"\[\s*\{.*\}\s*\]", content, re.DOTALL)
            if json_array_match:
                parsed_list = json.loads(json_array_match.group())
                for parsed in parsed_list:
                    formatted_question = {
                        "question": parsed.get("question", ""),
                        "choices": parsed.get("choices", []),
                        "answer": parsed.get("answer", ""),
                        "explanation": parsed.get("explanation", ""),
                        "image": f"data:image/png;base64,{base64_img}" if "image" in parsed else ""  # add image to question
                    }
                    formatted_data.append(formatted_question)
                    with open("data/sat_math_questions.jsonl", "a") as f:
                        f.write(json.dumps(formatted_question) + "\n")
            else:
                print("⚠️ No JSON array found!")
                formatted_data.append({"raw_response": content})
        except json.JSONDecodeError:
            print("⚠️ Failed to parse JSON!")
            formatted_data.append({"raw_response": content})

    return {"message": "success lets gooo"}
    
