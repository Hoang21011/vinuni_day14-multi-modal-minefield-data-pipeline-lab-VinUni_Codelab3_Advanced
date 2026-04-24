import json
import os

def run_forensic_test():
    print("=== STARTING FORENSIC DEBRIEF ===")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_path = os.path.join(os.path.dirname(script_dir), "processed_knowledge_base.json")
    
    if not os.path.exists(base_path):
        # Fallback to CWD
        base_path = "processed_knowledge_base.json"
        if not os.path.exists(base_path):
            print("Error: processed_knowledge_base.json not found. Pipeline failed.")
            return
            
    with open(base_path, "r", encoding='utf-8') as f:

        data = json.load(f)
    
    score = 0
    total = 3
    
    # Q1: Check for duplicate avoidance
    # ids = [d['document_id'] for d in data if 'csv' in d['document_id']]
    # Thay vì: ids = [d['document_id'] for d in data]
# Hãy dùng:
    ids = [d.get('document_id', 'unknown_id') for d in data if isinstance(d, dict)]
    len_ids = len(ids)
    len_unique_ids = len(set(ids))
    if len(ids) == len(set(ids)):
        print("[PASS] No duplicate IDs in CSV processing.")
        score += 1
    else:
        print("[FAIL] Duplicate IDs detected in the Knowledge Base.")
        
    # Q2: Check for price extraction from transcript
    transcript_doc = next((d for d in data if d['source_type'] == 'Transcript'), None)
    if transcript_doc and transcript_doc.get('source_metadata', {}).get('detected_price_vnd') == 500000:
        print("[PASS] Correct price extracted from Vietnamese audio transcript.")
        score += 1
    else:
        print("[FAIL] Failed to extract the price mentioned in the audio transcript.")
        
    # Q3: Check for quality gate effectiveness
# Q3: Check for quality gate effectiveness
    # Sử dụng .get() để tránh KeyError nếu bản ghi bị lỗi cấu trúc
    # 1. Đảm bảo d luôn là dict bằng cách kiểm tra kiểu dữ liệu
# Nếu d là list, ta lấy phần tử đầu tiên của nó (nếu có)
    corrupt_check = any(
    "Null pointer exception" in str(d.get('content', '')) 
    for d in data if isinstance(d, dict)
)
    if not corrupt_check:
        print("[PASS] Quality gate successfully rejected corrupt content.")
        score += 1
    else:
        print("[FAIL] Quality gate failed: Corrupt data found in Knowledge Base.")
        
    print(f"\nFinal Forensic Score: {score}/{total}")
if __name__ == "__main__":
    run_forensic_test()
