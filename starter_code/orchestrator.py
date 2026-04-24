import json
import time
import os

# Robust path handling
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "raw_data")

# Import các thành phần dựa trên code bạn đã cung cấp
from schema import UnifiedDocument
from process_pdf import extract_pdf_data
from process_transcript import clean_transcript
from process_html import parse_html_catalog
from process_csv import process_sales_csv
from process_legacy_code import extract_logic_from_code
from quality_check import run_quality_gate

# ==========================================
# ROLE 4: DEVOPS & INTEGRATION SPECIALIST
# ==========================================

def main():
    start_time = time.time()
    final_kb = []
    
    # --- FILE PATH SETUP ---
    pdf_path = os.path.join(RAW_DATA_DIR, "lecture_notes.pdf")
    trans_path = os.path.join(RAW_DATA_DIR, "demo_transcript.txt")
    html_path = os.path.join(RAW_DATA_DIR, "product_catalog.html")
    csv_path = os.path.join(RAW_DATA_DIR, "sales_records.csv")
    code_path = os.path.join(RAW_DATA_DIR, "legacy_pipeline.py")
    
    output_path = os.path.join(os.path.dirname(SCRIPT_DIR), "processed_knowledge_base.json")

    # Danh sách các tác vụ cần xử lý: (hàm_xử_lý, đường_dẫn_file, tên_loại)
    processing_tasks = [
        (extract_pdf_data, pdf_path, "PDF"),
        (clean_transcript, trans_path, "Transcript"),
        (parse_html_catalog, html_path, "HTML"),
        (process_sales_csv, csv_path, "CSV"),
        (extract_logic_from_code, code_path, "Legacy Code")
    ]

    print("--- Starting Pipeline Ingestion ---")

    for processor, path, label in processing_tasks:
        if not os.path.exists(path):
            print(f"WARNING: File not found for {label}: {path}")
            continue

        try:
            # 1. Gọi hàm xử lý chuyên biệt cho từng loại dữ liệu
            doc_data = processor(path)
            
            # 2. Chạy qua Quality Gate (Kiểm tra độ dài, mã độc, logic discrepancy)
            # Lưu ý: doc_data có thể là dict hoặc instance của UnifiedDocument tùy vào hàm xử lý
            if doc_data and run_quality_gate(doc_data):
                # Nếu run_quality_gate trả về True, tài liệu hợp lệ
                # Đảm bảo lưu dưới dạng dict để dễ dàng dump JSON sau này
                if hasattr(doc_data, "dict"):
                    final_kb.append(doc_data.dict())
                else:
                    final_kb.append(doc_data)
                print(f"[SUCCESS] {label} processed and passed QA.")
            else:
                print(f"[REJECTED] {label} failed quality checks or processing.")
                
        except Exception as e:
            print(f"[ERROR] Failed to process {label}: {str(e)}")

    # --- SAVE FINAL KNOWLEDGE BASE ---
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(final_kb, f, indent=4, ensure_ascii=False)
        print(f"\n--- Output saved to: {output_path} ---")
    except Exception as e:
        print(f"Error saving output file: {e}")

    end_time = time.time()
    print(f"Pipeline finished in {end_time - start_time:.2f} seconds.")
    print(f"Total valid documents stored: {len(final_kb)}")


if __name__ == "__main__":
    main()