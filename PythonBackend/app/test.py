# import requests
# import urllib.parse
# import os

# def test_wolfram_simple_api(app_id, query="3+5"):
#     """Test the Simple API that returns an image"""
#     encoded_query = urllib.parse.quote(query)
#     url = f"http://api.wolframalpha.com/v1/simple?appid={app_id}&i={encoded_query}"
    
#     print(f"Simple API URL: {url}")
    
#     try:
#         response = requests.get(url)
#         print(f"Status Code: {response.status_code}")
#         print(f"Content Type: {response.headers.get('content-type')}")
        
#         if response.status_code == 200:
#             print("✅ Simple API works! (Returns an image)")
#             # Save the image to see the result
#             with open("wolfram_result.png", "wb") as f:
#                 f.write(response.content)
#             print("Saved result as wolfram_result.png")
#         else:
#             print(f"❌ Error: {response.text}")
            
#     except Exception as e:
#         print(f"❌ Exception: {e}")

# def test_wolfram_full_api(app_id, query="3+5"):
#     """Test the Full Results API that the Python library uses"""
#     url = f"http://api.wolframalpha.com/v2/query"
#     params = {
#         'input': query,
#         'appid': app_id,
#         'format': 'plaintext',
#         'output': 'JSON'  # Try JSON instead of XML for easier reading
#     }
    
#     print(f"\nFull API URL: {url}")
#     print(f"Parameters: {params}")
    
#     try:
#         response = requests.get(url, params=params)
#         print(f"Status Code: {response.status_code}")
#         print(f"Content Type: {response.headers.get('content-type')}")
        
#         if response.status_code == 200:
#             print("✅ Full API works!")
#             print("Response preview:")
#             print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
#         else:
#             print(f"❌ Error: {response.text}")
            
#     except Exception as e:
#         print(f"❌ Exception: {e}")

# def test_wolfram_library(app_id, query="3+5"):
#     """Test the actual wolframalpha library"""
#     try:
#         import wolframalpha
#         client = wolframalpha.Client(app_id)
        
#         print(f"\nTesting wolframalpha library with query: {query}")
#         result = client.query(query)
        
#         print("✅ Library works!")
#         print("Pods found:")
#         for pod in result.pods:
#             print(f"  - {pod.title}: {pod.text}")
            
#     except Exception as e:
#         print(f"❌ Library error: {type(e).__name__}: {e}")


# WOLFRAM_APPID = "KHJXV8LJU7"
# print(f"Wolfram App ID: {WOLFRAM_APPID}")

# print("Testing Wolfram Alpha APIs...")
# test_wolfram_simple_api(WOLFRAM_APPID)
# test_wolfram_full_api(WOLFRAM_APPID)
# test_wolfram_library(WOLFRAM_APPID)

from datasets import load_dataset
import pandas as pd

ds = load_dataset("emozilla/sat-reading")
train_df = ds["train"].to_pandas()
val_df = ds["validation"].to_pandas()
test_df = ds["test"].to_pandas()

# Add split column
train_df["split"] = "train"
val_df["split"] = "validation"
test_df["split"] = "test"

# Combine
full_df = pd.concat([train_df, val_df, test_df], ignore_index=True)

# Remove duplicates based on the question text
full_df = full_df.drop_duplicates(subset=["text"])

# Drop unfinished rows (blank/missing text)
full_df = full_df[full_df["text"].notna() & (full_df["text"].str.strip() != "")]

# Drop invalid answers (must be A, B, C, or D)
full_df = full_df[full_df["answer"].isin(["A", "B", "C", "D"])]

# Save to CSV
full_df.to_csv("sat_reading_cleaned.csv", index=False)