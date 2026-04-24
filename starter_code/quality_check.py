# ==========================================
# ROLE 3: OBSERVABILITY & QA ENGINEER
# ==========================================
# Task: Implement quality gates to reject corrupt data or logic discrepancies.

def run_quality_gate(document_dict):
    # Support both dictionary and Pydantic model
    if hasattr(document_dict, "model_dump"):
        doc = document_dict.model_dump()
    elif hasattr(document_dict, "dict"):
        doc = document_dict.dict()
    elif isinstance(document_dict, dict):
        doc = document_dict
    else:
        doc = {"content": str(document_dict)}

    content = doc.get("content", "")

    # Reject documents with 'content' length < 20 characters
    if len(content) < 20:
        return False

    # Reject documents containing toxic/error strings
    toxic_strings = ["null pointer exception", "ocr error", "traceback"]
    content_lower = content.lower()
    for toxic in toxic_strings:
        if toxic in content_lower:
            return False

    # Flag discrepancies (e.g., if tax calculation comment says 8% but code says 10%)
    if "8%" in content and ("10%" in content or "0.10" in content):
        doc_id = doc.get("document_id", "unknown")
        print(f"WARNING: Discrepancy flagged in document '{doc_id}': Tax calculation mentions 8% but code says 10%.")
        
        # Add flag to metadata
        if isinstance(document_dict, dict):
            if "source_metadata" not in document_dict:
                document_dict["source_metadata"] = {}
            document_dict["source_metadata"]["flagged_discrepancy"] = True
        elif hasattr(document_dict, "source_metadata"):
            if document_dict.source_metadata is None:
                document_dict.source_metadata = {}
            document_dict.source_metadata["flagged_discrepancy"] = True
    
    # Return True if pass, False if fail.
    return True
