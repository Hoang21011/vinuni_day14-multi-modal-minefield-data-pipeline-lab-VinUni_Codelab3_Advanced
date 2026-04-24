import google.generativeai as genai
import os
import json
import time
import random
from dotenv import load_dotenv
from google.api_core import exceptions
from schema import UnifiedDocument

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def extract_pdf_data(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return None
        
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    print(f"Uploading {file_path} to Gemini...")
    try:
        pdf_file = genai.upload_file(path=file_path)
    except Exception as e:
        print(f"Failed to upload file to Gemini: {e}")
        return None
        
    prompt = """
Analyze this document and extract the following:
1. Title
2. Author
3. Main Topics
4. Any Tables (as a list of JSON objects or empty list if none)

Output exactly as a JSON object matching this exact format:
{
    "document_id": "pdf-doc-001",
    "content": "Title: [Insert Title Here]\nMain Topics: [Insert Main Topics Here]",
    "source_type": "PDF",
    "author": "[Insert author name here]",
    "timestamp": null,
    "source_metadata": {
        "original_file": "lecture_notes.pdf",
        "tables": [Insert Tables here or []]
    }
}
"""
    
    max_retries = 5
    base_delay = 1
    
    for attempt in range(max_retries):
        try:
            print(f"Generating content from PDF using Gemini (Attempt {attempt + 1})...")
            response = model.generate_content([pdf_file, prompt])
            content_text = response.text
            
            # Simple cleanup if the response is wrapped in markdown json block
            if content_text.strip().startswith("```json"):
                content_text = content_text.strip()[7:]
            if content_text.strip().endswith("```"):
                content_text = content_text.strip()[:-3]
            if content_text.strip().startswith("```"):
                content_text = content_text.strip()[3:]
                
            raw_json = json.loads(content_text.strip())
            
            # Trap: Gemini's response is a string. Parse it into your UnifiedDocument schema.
            # Using Pydantic model to validate and parse
            doc = UnifiedDocument(**raw_json)
            return doc.dict()
            
        except exceptions.ResourceExhausted:
            # SLA: Implement Exponential Backoff for 429 errors.
            wait_time = (base_delay * 2 ** attempt) + random.uniform(0, 1)
            print(f"Rate limit hit (429). Retrying in {wait_time:.2f} seconds...")
            time.sleep(wait_time)
        except Exception as e:
            print(f"Error during Gemini processing: {e}")
            break
            
    return None

if __name__ == "__main__":
    # Test script trực tiếp
    import os
    # Lấy đường dẫn tuyệt đối đến file PDF trong raw_data
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_pdf = os.path.join(os.path.dirname(current_dir), "raw_data", "lecture_notes.pdf")
    
    print(f"--- Testing PDF Extraction ---")
    result = extract_pdf_data(test_pdf)
    if result:
        print("\nSuccess! Extracted Data:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("\nExtraction failed.")
