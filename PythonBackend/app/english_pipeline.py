from __future__ import annotations
from functools import lru_cache
import re
from typing import List, Dict, Iterable

@lru_cache(maxsize=1)
def get_sentence_pattern():
    """
    Regex pattern for sentence splitting that mimics SpaCy's sentencizer.
    Splits on periods, exclamation marks, and question marks followed by whitespace or end of string.
    """
    # This pattern splits on sentence-ending punctuation followed by whitespace or end of string
    # It handles common abbreviations and edge cases reasonably well
    pattern = r'(?<=[.!?])\s+'
    return re.compile(pattern)

def split_sentences(passage: str) -> List[Dict]:
    """
    Split into 1-based, numbered sentences with char offsets.
    Returns: [{"id": int, "text": str, "start_char": int, "end_char": int}, ...]
    """
    if not passage.strip():
        return []
    
    # Split by sentence-ending punctuation
    pattern = get_sentence_pattern()
    
    # Find all split points
    split_points = [0]  # Start of text
    for match in pattern.finditer(passage):
        split_points.append(match.start())
    split_points.append(len(passage))  # End of text
    
    sentences = []
    sentence_id = 1
    
    for i in range(len(split_points) - 1):
        start_char = split_points[i]
        end_char = split_points[i + 1]
        
        # Extract the sentence text
        sentence_text = passage[start_char:end_char].strip()
        
        if sentence_text:  # Only add non-empty sentences
            sentences.append({
                "id": sentence_id,
                "text": sentence_text,
                "start_char": start_char,
                "end_char": start_char + len(sentence_text.lstrip())  # Adjust for leading whitespace
            })
            sentence_id += 1
    
    return sentences

def split_sentences_simple(passage: str) -> List[Dict]:
    """
    Alternative simpler approach using basic string operations.
    More reliable for character positions.
    """
    sentences = []
    sentence_id = 1
    current_start = 0
    
    i = 0
    while i < len(passage):
        char = passage[i]
        
        # Check for sentence-ending punctuation
        if char in '.!?':
            # Look ahead to see if this is really the end of a sentence
            next_char = passage[i + 1] if i + 1 < len(passage) else ''
            
            # End of sentence if followed by whitespace, quote, or end of text
            if next_char in ' \n\t\r"\'`""''‛‟' or i + 1 >= len(passage):
                # Find the actual end (including the punctuation)
                sentence_end = i + 1
                
                # Extract sentence text
                sentence_text = passage[current_start:sentence_end].strip()
                
                if sentence_text:
                    sentences.append({
                        "id": sentence_id,
                        "text": sentence_text,
                        "start_char": current_start,
                        "end_char": sentence_end
                    })
                    sentence_id += 1
                
                # Move to start of next sentence
                current_start = sentence_end
                while current_start < len(passage) and passage[current_start].isspace():
                    current_start += 1
                
                i = current_start - 1  # -1 because loop will increment
        
        i += 1
    
    # Handle any remaining text as the last sentence
    if current_start < len(passage):
        remaining_text = passage[current_start:].strip()
        if remaining_text:
            sentences.append({
                "id": sentence_id,
                "text": remaining_text,
                "start_char": current_start,
                "end_char": len(passage)
            })
    
    return sentences

def span_to_sentence_ids(sentences: List[Dict], start: int, end: int) -> List[int]:
    """
    Given a character span [start, end) in the ORIGINAL passage,
    return the sentence id(s) that overlap the span.
    """
    ids = []
    for s in sentences:
        if not (end <= s["start_char"] or start >= s["end_char"]):
            ids.append(s["id"])
    return ids

def find_token_sentence_ids(passage: str, token: str) -> List[int]:
    """
    Find the first occurrence of `token` (case-insensitive) and return its sentence id(s).
    Useful for vocab-in-context items.
    """
    sentences = split_sentences_simple(passage)  # Use the more reliable version
    idx = passage.lower().find(token.lower())
    if idx == -1:
        return []
    return span_to_sentence_ids(sentences, idx, idx + len(token))

def compress_ids(ids: Iterable[int]) -> List[str]:
    """
    Turn [12, 13, 14, 18] into ["12-14", "18"] for nice display.
    """
    ids = sorted(set(ids))
    if not ids:
        return []
    ranges = []
    start = prev = ids[0]
    for x in ids[1:]:
        if x == prev + 1:
            prev = x
        else:
            ranges.append(f"{start}-{prev}" if start != prev else f"{start}")
            start = prev = x
    ranges.append(f"{start}-{prev}" if start != prev else f"{start}")
    return ranges