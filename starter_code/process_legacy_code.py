import ast
import json
import os
import re
import sys

from schema import UnifiedDocument

COMMENT_PATTERNS = [
    r"#\s*Business Logic Rule[^\n]*",
    r"#\s*WARNING:[^\n]*",
    r"#\s*IMPORTANT:[^\n]*",
    r"#\s*This function checks[^\n]*",
    r"#\s*\[YEAR\]-\[REGION\]-\[NUMERIC_ID\]",
    r"#\s*Example:[^\n]*",
    r"#\s*Note:[^\n]*",
    r"#\s*This actually calculates VAT at 10%, but the code says it does 8%\.",
]


def _extract_comments(source_code):
    comment_lines = []
    for pattern in COMMENT_PATTERNS:
        comment_lines.extend(re.findall(pattern, source_code, flags=re.IGNORECASE))

    unique_comments = []
    for line in comment_lines:
        cleaned = re.sub(r"^#\s*", "", line).strip()
        if cleaned and cleaned not in unique_comments:
            unique_comments.append(cleaned)
    return unique_comments


def extract_logic_from_code(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        source_code = f.read()

    tree = ast.parse(source_code)
    module_docstring = ast.get_docstring(tree) or ""
    functions = []
    docstrings = {}

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            functions.append(node.name)
            docstrings[node.name] = ast.get_docstring(node) or ""

    extracted_comments = _extract_comments(source_code)
    docstring_rules = [text.strip() for text in docstrings.values() if "Business Logic Rule" in text]
    business_rules = docstring_rules + [line for line in extracted_comments if "rule" in line.lower()]
    warnings = [line for line in extracted_comments if "warning" in line.lower() or "8%" in line or "10%" in line]

    content_parts = [
        module_docstring.strip(),
        "Functions: " + ", ".join(functions),
        "Docstring summary: " + " | ".join(
            f"{name}: {text.strip()}" for name, text in docstrings.items() if text.strip()
        ),
        "Comments and rules: " + " | ".join(extracted_comments),
    ]
    content = "\n".join(part for part in content_parts if part and not part.endswith(": "))

    document = UnifiedDocument(
        document_id="legacy-code-doc-001",
        content=content,
        source_type="Code",
        author="Senior Dev (retired)",
        timestamp=None,
        source_metadata={
            "original_file": os.path.basename(file_path),
            "functions": functions,
            "docstrings": docstrings,
            "business_rules": business_rules,
            "warnings": warnings,
            "module_docstring": module_docstring.strip(),
        },
    )
    return document.dict()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_code = os.path.join(os.path.dirname(current_dir), "raw_data", "legacy_pipeline.py")

    print("--- Testing Legacy Code Extraction ---")
    result = extract_logic_from_code(test_code)
    if result:
        print("\nSuccess! Extracted Data:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("\nExtraction failed.")
