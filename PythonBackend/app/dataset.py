from app.database import SessionLocal, Base, engine, get_db
from app.models import SATQuestion, SATQuestionEmbedding, CollegeSATScore
from app.embeddingModels import MathBERTEmbeddings, get_mpnet_embeddings
from app.chain import get_vectorstore
from openai import OpenAI
import os, uuid, time
from datasets import load_dataset
import torch
from transformers import AutoTokenizer, AutoModel
import pandas as pd
import re
from app.survival_models import SurvivalSession

# MODEL_ID = "tbs17/MathBERT-custom"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


#for embeddings
# dataset = load_dataset("ndavidson/sat-math-chain-of-thought") dataset for initial embeddings
csv_path = "sat_scores.csv"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
db = SessionLocal()

# embedder = MathBERTEmbeddings(MODEL_ID, DEVICE)

# def createEmbedding(question: SATQuestion) -> SATQuestionEmbedding:
#     embedding_vector = embedder.embed_query(question.question_text)  # -> List[float]
#     return SATQuestionEmbedding(
#         question_id=question.id,
#         text=question.question_text,
#         embedding=embedding_vector
#     )


# def insert_from_dataset():
#     start = time.time()

#     # --- Ensure exam/section ---
#     exam = db.query(SATExam).filter_by(name="sat").first()
#     if not exam:
#         exam = SATExam(name="sat", description="")
#         db.add(exam)
#         db.flush()

#     section = db.query(Section).filter_by(name="math", exam_id=exam.id).first()
#     if not section:
#         section = Section(name="math", exam_id=exam.id)
#         db.add(section)
#         db.flush()

#     db.commit()

#     # --- Vector store for LangChain tables ---
#     # name the collection by exam/section (must match what you use when retrieving)
#     collection_name = "sat_math"
#     vectorstore = get_vectorstore(collection_name)

#     train_set = dataset["train"]
#     subset = train_set.select(range(len(train_set) // 6))

#     # batch buffers for vectorstore.add_texts
#     batch_texts: List[str] = []
#     batch_metas: List[Dict] = []
#     batch_ids: List[str] = []
#     BATCH_SIZE = 100

#     def flush_batch():
#         if not batch_texts:
#             return
#         vectorstore.add_texts(
#             texts=batch_texts,
#             metadatas=batch_metas,
#             ids=batch_ids,           # prevents duplicates if re-running
#         )
#         batch_texts.clear()
#         batch_metas.clear()
#         batch_ids.clear()

#     for row in subset:
#         question_text = row["question"]

#         # --- your own tables ---
#         q = Question(
#             section_id=section.id,
#             question_text=question_text,
#             answer=row.get("answer"),
#         )
#         db.add(q)
#         db.flush()  # get q.id

#         db.add(createEmbedding(q))  # optional: keep your own embedding table

#         for i, step in enumerate(row["reasoning_chain"]["steps"]):
#             db.add(Solution(
#                 question_id=q.id,
#                 step_num=i + 1,
#                 step_text=step.get("explanation", "")
#             ))

#         # --- LangChain tables (add to batch) ---
#         batch_texts.append(question_text)
#         batch_metas.append({
#             "exam": "sat",
#             "section": "math",
#             "question_id": q.id,
#             # add whatever you need for filtering later:
#             # "answer": row.get("answer"),
#         })
#         batch_ids.append(str(q.id))   # your DB id as stable doc id

#         # flush periodically
#         if len(batch_texts) >= BATCH_SIZE:
#             flush_batch()
#             print("🔎 Indexed", BATCH_SIZE, "questions into langchain_pg_embedding")

#     # final flush
#     flush_batch()
#     db.commit()

#     print(f"✅ Inserted into your tables and langchain_pg_* in {time.time() - start:.2f}s")

# # insert_from_dataset()


# def get_embedding_model():
#     """Initialize the embedding model"""
#     print(f"🤖 Loading embedding model: all-mpnet-base-v2")
#     model = get_mpnet_embeddings()
#     print(f"✅ Model loaded! Embedding dimension: 768")
#     return model

# def preprocess_question_text(row) -> str:
#     """
#     Create rich text for embedding by combining question parts
#     """
#     text_parts = []
    
#     # Always include the main question
#     text_parts.append(row['question'])
    
#     # Add section and domain context
#     text_parts.append(f"[{row['section']} - {row['domain']}]")
    
#     # Include paragraph for reading comprehension
#     if pd.notna(row['paragraph']):
#         # Truncate very long paragraphs
#         paragraph = row['paragraph']
#         if len(paragraph) > 800:
#             paragraph = paragraph[:800] + "..."
#         text_parts.append(f"Passage: {paragraph}")
    
#     # Add answer choices for context
#     choices = [row['choice_A'], row['choice_B'], row['choice_C'], row['choice_D']]
#     text_parts.append(f"Choices: {' | '.join(choices)}")
    
#     return " ".join(text_parts)

# def import_csv_to_database(csv_path: str = "sat_questions_cleaned.csv"):
#     """Import the CSV data into new SAT tables"""
    
#     start_time = time.time()
#     db = SessionLocal()
    
#     try:
#         # Load CSV
#         print(f"📂 Loading CSV from: {csv_path}")
#         df = pd.read_csv(csv_path, encoding='utf-8')
#         print(f"📊 Loaded {len(df)} questions")
        
#         # Clean data - remove rows with missing choices
#         print("🧹 Cleaning data...")
#         original_count = len(df)
#         df = df.dropna(subset=['choice_A', 'choice_B', 'choice_C', 'choice_D', 'correct_answer'])
        
#         # Fill missing values with empty strings or appropriate defaults
#         df['paragraph'] = df['paragraph'].fillna('')
#         df['visual_type'] = df['visual_type'].fillna('')
        
#         print(f"📊 After cleaning: {len(df)} questions (removed {original_count - len(df)} incomplete rows)")
        
#         # Initialize embedding model
#         embedder = get_embedding_model()
        
#         # Batch processing
#         BATCH_SIZE = 50  # Smaller batches for memory efficiency
#         questions_added = 0
#         embeddings_added = 0
        
#         print(f"🚀 Starting import in batches of {BATCH_SIZE}...")
        
#         for i in range(0, len(df), BATCH_SIZE):
#             batch_end = min(i + BATCH_SIZE, len(df))
#             batch = df.iloc[i:batch_end]
            
#             print(f"📦 Processing batch {i//BATCH_SIZE + 1}: rows {i+1}-{batch_end}")
            
#             # Prepare batch data for embeddings
#             batch_texts = []
#             batch_questions = []
            
#             for _, row in batch.iterrows():
#                 # Check if question already exists
#                 existing = db.query(SATQuestion).filter_by(id=row['id']).first()
#                 if existing:
#                     print(f"⏭️  Skipping existing question: {row['id']}")
#                     continue
                
#                 # Create SAT question
#                 sat_question = SATQuestion(
#                     id=row['id'],
#                     section=row['section'],
#                     domain=row['domain'],
#                     difficulty=row['difficulty'],
#                     question_text=row['question'],
#                     paragraph=row['paragraph'] if row['paragraph'] else None,  # Convert empty string to None
#                     choice_a=row['choice_A'],
#                     choice_b=row['choice_B'],
#                     choice_c=row['choice_C'],
#                     choice_d=row['choice_D'],
#                     correct_answer=row['correct_answer'],
#                     explanation=row['explanation'],
#                     visual_type=row['visual_type'] if row['visual_type'] else None  # Convert empty string to None
#                 )
                
#                 db.add(sat_question)
#                 batch_questions.append(sat_question)
                
#                 # Prepare text for embedding
#                 embedding_text = preprocess_question_text(row)
#                 batch_texts.append(embedding_text)
                
#                 questions_added += 1
            
#             # Commit questions first to get IDs
#             db.flush()
            
#             # Generate embeddings in batch (much faster)
#             if batch_texts:
#                 print("🧠 Generating embeddings...")
#                 embeddings = embedder.embed_documents(batch_texts)
                
#                 # Create embedding records
#                 for question, embedding_text, embedding_vector in zip(batch_questions, batch_texts, embeddings):
#                     sat_embedding = SATQuestionEmbedding(
#                         question_id=question.id,
#                         text=embedding_text,
#                         embedding=embedding_vector
#                     )
#                     db.add(sat_embedding)
#                     embeddings_added += 1
            
#             # Commit batch
#             db.commit()
            
#             elapsed = time.time() - start_time
#             rate = (i + len(batch)) / elapsed
#             print(f"✅ Batch complete! Progress: {batch_end}/{len(df)} ({batch_end/len(df)*100:.1f}%) | Rate: {rate:.1f} questions/sec")
        
#         total_time = time.time() - start_time
#         print(f"\n🎉 Import completed successfully!")
#         print(f"📊 Statistics:")
#         print(f"   • Questions imported: {questions_added}")
#         print(f"   • Embeddings created: {embeddings_added}")
#         print(f"   • Total time: {total_time:.1f}s")
#         print(f"   • Average rate: {questions_added/total_time:.1f} questions/sec")
        
#         # Verify import
#         total_questions = db.query(SATQuestion).count()
#         total_embeddings = db.query(SATQuestionEmbedding).count()
#         print(f"✅ Verification:")
#         print(f"   • Total questions in database: {total_questions}")
#         print(f"   • Total embeddings in database: {total_embeddings}")
        
#     except Exception as e:
#         print(f"❌ Error during import: {e}")
#         db.rollback()
#         raise
        
#     finally:
#         db.close()

# def verify_import():
#     """Verify the import worked correctly"""
    
#     try:
#         # Check question counts by section
#         math_count = db.query(SATQuestion).filter_by(section="Math").count()
#         english_count = db.query(SATQuestion).filter_by(section="English").count()
        
#         print(f"\n📊 Database Contents:")
#         print(f"   • Math questions: {math_count}")
#         print(f"   • English questions: {english_count}")
#         print(f"   • Total questions: {math_count + english_count}")
        
#         # Show sample questions
#         print(f"\n📝 Sample Questions:")
        
#         math_sample = db.query(SATQuestion).filter_by(section="Math").first()
#         if math_sample:
#             print(f"   Math: {math_sample.question_text[:100]}...")
        
#         english_sample = db.query(SATQuestion).filter_by(section="English").first()
#         if english_sample:
#             print(f"   English: {english_sample.question_text[:100]}...")
            
#         # Check embeddings
#         embedding_count = db.query(SATQuestionEmbedding).count()
#         print(f"   • Total embeddings: {embedding_count}")
        
#     finally:
#         db.close()



def setup_complete_database():
    """Set up both your app tables AND LangChain vector tables"""
    
    print("Creating application tables...")
    Base.metadata.create_all(bind=engine)
    
    # 2. Initialize vector store (creates LangChain tables)
    print("Setting up vector store...")
    vectorstore = get_vectorstore("sat_questions")
    
    return vectorstore

def parse_sat_range(sat_range_str):
    """
    Parse SAT range string like "1200-1400" into min and max values
    
    Args:
        sat_range_str: String like "1200-1400", "1200 - 1400", or other formats
    
    Returns:
        tuple: (min_score, max_score) or (None, None) if parsing fails
    """
    if not sat_range_str:
        return None, None
    
    # Clean the string
    cleaned = str(sat_range_str).strip()
    
    # Try different patterns for SAT score ranges
    patterns = [
        r'(\d{3,4})\s*-\s*(\d{3,4})',  # "1200-1400" or "1200 - 1400"
        r'(\d{3,4})\s*to\s*(\d{3,4})',  # "1200 to 1400"
        r'(\d{3,4})\s*/\s*(\d{3,4})',   # "1200/1400"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, cleaned, re.IGNORECASE)
        if match:
            try:
                min_score = int(match.group(1))
                max_score = int(match.group(2))
                
                # Validate SAT score ranges (200-800 per section, 400-1600 total)
                if 400 <= min_score <= 1600 and 400 <= max_score <= 1600 and min_score <= max_score:
                    return min_score, max_score
            except ValueError:
                continue
    
    print(f"Warning: Could not parse SAT range: '{sat_range_str}'")
    return None, None

def load_sat_scores_csv(csv_file_path: str):
    """
    Load SAT scores from CSV file into the database
    
    Args:
        csv_file_path: Path to the CSV file
    """
    try:
        # Read the CSV file
        print(f"Reading CSV file: {csv_file_path}")
        df = pd.read_csv(csv_file_path)
        
        print(f"Loaded {len(df)} rows from CSV")
        print("Columns:", df.columns.tolist())
        
        # Show first few rows for verification
        print("\nFirst 3 rows:")
        print(df.head(3))
        
        # Create database tables if they don't exist
        Base.metadata.create_all(bind=engine)
        
        # Get database session
        db = next(get_db())
        
        successful_inserts = 0
        failed_inserts = 0
        
        for index, row in df.iterrows():
            try:
                college_name = str(row['College']).strip()
                sat_range_str = str(row['SAT 25-75 Percentile']).strip()
                
                # Skip empty rows
                if not college_name or college_name.lower() in ['nan', '']:
                    print(f"Skipping row {index + 1}: Empty college name")
                    failed_inserts += 1
                    continue
                
                # Parse SAT range
                sat_min, sat_max = parse_sat_range(sat_range_str)
                
                # Check if college already exists
                existing = db.query(CollegeSATScore).filter(
                    CollegeSATScore.college_name == college_name
                ).first()
                
                if existing:
                    print(f"Updating existing record for: {college_name}")
                    existing.sat_range = sat_range_str
                    existing.sat_min = sat_min
                    existing.sat_max = sat_max
                else:
                    # Create new record
                    college_score = CollegeSATScore(
                        college_name=college_name,
                        sat_range=sat_range_str,
                        sat_min=sat_min,
                        sat_max=sat_max,
                    )
                    db.add(college_score)
                
                successful_inserts += 1
                
            except Exception as e:
                print(f"Error processing row {index + 1}: {e}")
                print(f"Row data: {row.to_dict()}")
                failed_inserts += 1
                continue
        
        # Commit all changes
        db.commit()
        
        print(f"\n✅ Data loading completed!")
        print(f"Successfully processed: {successful_inserts} records")
        print(f"Failed to process: {failed_inserts} records")
        print(f"Total records in database: {db.query(CollegeSATScore).count()}")
        
        # Show some sample data
        print("\nSample records from database:")
        samples = db.query(CollegeSATScore).limit(5).all()
        for sample in samples:
            print(f"  {sample.college_name}: {sample.sat_range} (min: {sample.sat_min}, max: {sample.sat_max})")
        
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        if 'db' in locals():
            db.rollback()
    finally:
        if 'db' in locals():
            db.close()

# load_sat_scores_csv(csv_path)


setup_complete_database()
# try:
#     import_csv_to_database(csv_path)
# except Exception as e:
#     print(f"❌ Import failed: {e}")
#     exit(1)
    
# verify_import()
