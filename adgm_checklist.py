# adgm_checklist.py
import re

# Example sample checklist for company incorporation (can be extended)
COMPANY_INCORPORATION_CHECKLIST = [
    "Articles of Association",
    "Memorandum of Association",
    "Board Resolution Template",
    "Incorporation Application Form",
    "Register of Members and Directors",
    "UBO Declaration Form",
]

# Simple ADGM citation mapping (placeholder)
ADGM_CITATIONS = {
    "companies_regulation_jurisdiction": "ADGM Companies Regulations 2020, Art. 6",
    "ubo_regulation": "ADGM UBO Rules (example placeholder)",
}

# Heuristic doc-type detection (very simple)
def detect_doc_type_by_text(text: str) -> str:
    txt = text.lower()
    if "articles of association" in txt or "article" in txt and "association" in txt:
        return "Articles of Association"
    if "memorandum of association" in txt or "memorandum" in txt:
        return "Memorandum of Association"
    if "board resolution" in txt:
        return "Board Resolution Template"
    if "register of members" in txt or "register of directors" in txt:
        return "Register of Members and Directors"
    if "ubo" in txt or "ultimate beneficial owner" in txt:
        return "UBO Declaration Form"
    if "application for incorporation" in txt or "incorporation application" in txt:
        return "Incorporation Application Form"
    # fallback: return 'Unknown' but include a guess by title keywords
    if "agreement" in txt:
        return "Commercial Agreement"
    return "Unknown"

# Utility functions for rule-based red-flag detection
def check_jurisdiction_paragraph(paragraph_text: str):
    # Look for common non-ADGM jurisdictions and missing ADGM mention
    lower = paragraph_text.lower()
    issues = []
    if "u.a.e federal courts" in lower or "federal courts of the uae" in lower:
        issues.append({
            "issue": "References UAE Federal Courts instead of ADGM jurisdiction.",
            "severity": "High",
            "citation_key": "companies_regulation_jurisdiction",
            "suggestion": "Replace jurisdiction clause to reference ADGM Courts/Jurisdiction."
        })
    if ("adgm" not in lower) and ("jurisdiction" in lower or "governing law" in lower):
        issues.append({
            "issue": "Jurisdiction clause does not explicitly reference ADGM.",
            "severity": "Medium",
            "citation_key": "companies_regulation_jurisdiction",
            "suggestion": "Update jurisdiction/governing law clause to specify 'ADGM'."
        })
    return issues

def detect_missing_signature(paragraphs):
    # heuristic: look for signature lines/blocks
    joined = "\n".join(paragraphs[-10:]).lower()
    if ("signature" not in joined) and ("signed" not in joined) and ("authorized signatory" not in joined):
        return [{
            "issue": "No signature block or signatory section detected near end of document.",
            "severity": "High",
            "suggestion": "Add signatory block with name, designation and date."
        }]
    return []

def detect_ambiguous_language(paragraph_text):
    # naive detection of non-binding language
    ambig_markers = ["may", "best efforts", "endeavour to", "possibly", "subject to", "to the extent possible"]
    lower = paragraph_text.lower()
    for marker in ambig_markers:
        if marker in lower and len(lower.split()) < 200:
            return [{
                "issue": f"Ambiguous/non-binding language found ('{marker}')",
                "severity": "Low",
                "suggestion": "Consider replacing ambiguous phrasing with clear, binding obligations."
            }]
    return []
