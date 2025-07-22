from io import BytesIO
import pdfplumber
import re
import json
from pdf2image import convert_from_bytes
import base64
from io import BytesIO

# Step 1: Extract text from PDF bytes (not file path)
def extract_text_from_bytes(pdf_bytes):
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
    return text

# Step 2: Split text into question blocks
def split_into_questions(text):
    # Matches newlines followed by a number and another newline (e.g., "\n12\n")
    blocks = re.split(r'\n\d{1,2}\n', text)
    return [b.strip() for b in blocks if b.strip()]

# Step 3: Extract question + choices
def extract_components(block):
    lines = block.splitlines()
    choices = []
    question_lines = []

    for line in lines:
        if re.match(r'^[A-D]\)', line.strip()):
            choices.append(line.strip()[3:].strip())  # removes 'A) ' part
        else:
            question_lines.append(line.strip())

    question = " ".join(question_lines)
    return {
        "question": question,
        "choices": choices,
        "answer": "",
        "explanation": ""
    }

# Main function that takes PDF bytes and returns a list of question objects
def parse_pdf_to_json(pdf_bytes, output_path):
    text = extract_text_from_bytes(pdf_bytes)
    blocks = split_into_questions(text)

    print(f"🔍 Found {len(blocks)} question blocks")

    questions = [extract_components(b) for b in blocks]

    with open(output_path, "w") as f:
        for q in questions:
            f.write(json.dumps(q) + "\n")

    print(f"✅ Saved to {output_path}")


def pdf_to_images(pdf_bytes):
    images = convert_from_bytes(pdf_bytes)
    return images  # each image is a PIL.Image

def image_to_base64(pil_img):
    buffered = BytesIO()
    pil_img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")
