# app.py
import streamlit as st
import json
import os
import tempfile
from datetime import datetime
from adgm_checklist import COMPANY_INCORPORATION_CHECKLIST, detect_doc_type_by_text, ADGM_CITATIONS
from docx_utils import extract_docx_paragraphs, create_reviewed_docx, summarize_issues
from pathlib import Path

st.set_page_config(page_title="ADGM Corporate Agent (Prototype)", layout="wide")

st.title("ADGM-Compliant Corporate Agent — Prototype")

st.markdown(
    """
This prototype accepts `.docx` files, checks completeness vs an ADGM checklist (example: company incorporation),
detects red flags, inserts inline comments into a reviewed `.docx` and produces a structured JSON report.
"""
)

st.sidebar.header("Options")
use_rag = st.sidebar.checkbox("Enable RAG citations (requires embeddings & vector DB)", value=False)

uploaded_files = st.file_uploader(
    "Upload one or more .docx files (examples: AoA, MoA, Board Resolution, Register of Members, UBO declaration)",
    type=["docx"],
    accept_multiple_files=True,
)

if not uploaded_files:
    st.info("Upload .docx files to begin. Example set: Articles of Association, Memorandum, Board Resolution, UBO form.")
    st.stop()

# Create temp workspace
workspace = Path(tempfile.mkdtemp(prefix="adgm_agent_"))
st.write("Working directory:", workspace)

docs = []
for f in uploaded_files:
    # save to disk
    saved_path = workspace / f.name
    with open(saved_path, "wb") as outf:
        outf.write(f.getbuffer())
    docs.append(saved_path)

st.write(f"Uploaded {len(docs)} files.")

# Parse docs and detect type
st.header("Document parsing & classification")
doc_summaries = []
for p in docs:
    text_paragraphs = extract_docx_paragraphs(p)
    detected = detect_doc_type_by_text("\n".join(text_paragraphs))
    doc_summaries.append({
        "filename": p.name,
        "path": str(p),
        "detected_type": detected,
        "paragraph_count": len(text_paragraphs),
    })
    st.markdown(f"**{p.name}** — detected type: *{detected}* — paragraphs: {len(text_paragraphs)}")
    if st.checkbox(f"Show preview paragraphs for {p.name}", key=f"preview_{p.name}"):
        st.write("\n\n".join(text_paragraphs[:20]))

# Checklist verification (example: Company Incorporation)
st.header("Checklist verification")
# For demo, assume user tries Company Incorporation process
process = st.selectbox("Which process are you attempting?", ["Company Incorporation", "Other"])
if process == "Company Incorporation":
    required = COMPANY_INCORPORATION_CHECKLIST
    st.markdown("**Required documents for Company Incorporation (sample)**")
    for r in required:
        st.write(f"- {r}")

    uploaded_types = [s["detected_type"] for s in doc_summaries]
    present = [r for r in required if r in uploaded_types]
    missing = [r for r in required if r not in uploaded_types]

    st.success(f"Detected {len(present)} of {len(required)} required documents.")
    if missing:
        st.error("Missing documents:")
        for m in missing:
            st.write(f"- {m}")
    else:
        st.success("All required documents appear present.")

# Red flag detection & inline comment generation
st.header("Analysis & Red-Flag Detection")
severity_map = {"High": 3, "Medium": 2, "Low": 1}

# Gather all issues across docs
all_issues = []
for p in docs:
    paras = extract_docx_paragraphs(p)
    # simple rules in summarize_issues wrapper
    issues = summarize_issues(paras, filename=p.name, check_adgm=True)
    all_issues.extend(issues)
    st.write(f"Found {len(issues)} issues in {p.name}")

# Show issues in UI
if all_issues:
    st.subheader("Issues (detected)")
    for idx, issue in enumerate(all_issues, 1):
        st.markdown(f"**{idx}. [{issue['severity']}] {issue['document']} — {issue['section']}**")
        st.write(issue["issue"])
        if "suggestion" in issue:
            st.info(issue["suggestion"])
        if "citation_key" in issue:
            cite = ADGM_CITATIONS.get(issue["citation_key"])
            if cite:
                st.caption(f"Citation: {cite}")

# Create reviewed docx with "inline comments" (implemented as appended comment paragraphs near flagged paragraph indices)
if st.button("Generate Reviewed .docx and JSON report"):
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    reviewed_files = []
    json_summary = {
        "process": "Company Incorporation" if process == "Company Incorporation" else "Unknown",
        "documents_uploaded": len(docs),
        "required_documents": len(COMPANY_INCORPORATION_CHECKLIST) if process == "Company Incorporation" else None,
        "missing_documents": missing if process == "Company Incorporation" else [],
        "issues_found": all_issues,
    }

    for p in docs:
        reviewed_path = workspace / f"reviewed_{p.name}"
        # create reviewed docx with comments appended
        create_reviewed_docx(p, reviewed_path, all_issues)
        reviewed_files.append(reviewed_path)

    # Save JSON summary
    json_path = workspace / f"osint_summary_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(json_summary, jf, indent=2)

    st.success("Reviewed files and JSON summary created.")
    st.write("Download reviewed documents:")
    for f in reviewed_files:
        with open(f, "rb") as rf:
            st.download_button(label=f"Download {f.name}", data=rf.read(), file_name=f.name)

    with open(json_path, "rb") as jf:
        st.download_button(label="Download JSON summary", data=jf.read(), file_name=json_path.name)

    st.info(f"Workspace: {workspace} (you can zip and submit this folder)")

st.markdown("---")
st.info("This is a functional prototype. For full production: plug in an embeddings model for RAG, secure the app, and expand rule coverage.")

