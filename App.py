```python
import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import os

# ==================================
# PAGE CONFIG
# ==================================

st.set_page_config(
    page_title="Academic Reality Checker",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 Academic Reality Checker")
st.subheader("AI-Powered Syllabus vs Industry Skill Analysis")

# ==================================
# GEMINI API KEY
# ==================================

api_key = st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    api_key = st.text_input(
        "Enter Gemini API Key",
        type="password"
    )

if not api_key:
    st.warning("Please provide a Gemini API key.")
    st.stop()

genai.configure(api_key=api_key)

# ==================================
# PDF TEXT EXTRACTION
# ==================================

def extract_pdf_text(uploaded_file):
    text = ""

    try:
        reader = PdfReader(uploaded_file)

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    except Exception as e:
        st.error(f"PDF Reading Error: {e}")

    return text

# ==================================
# GEMINI ANALYSIS
# ==================================

def analyze_syllabus(text):

    prompt = f"""
You are an expert placement mentor.

Analyze the following college syllabus.

Provide:

1. Key Topics Found
2. Industry-Relevant Skills Missing
3. Placement Readiness Score (0-100)
4. Gap Analysis
5. Recommended Technologies
6. Recommended Certifications
7. Project Ideas
8. 6-Month Learning Roadmap
9. Internship Preparation Advice

Syllabus:

{text[:15000]}
"""

    model = genai.GenerativeModel("gemini-1.5-flash")

    response = model.generate_content(prompt)

    return response.text

# ==================================
# FILE UPLOAD
# ==================================

uploaded_file = st.file_uploader(
    "Upload Syllabus PDF",
    type=["pdf"]
)

if uploaded_file:

    st.success("PDF Uploaded Successfully")

    with st.spinner("Extracting syllabus..."):
        syllabus_text = extract_pdf_text(uploaded_file)

    if syllabus_text.strip() == "":
        st.error("Could not extract text from PDF.")
        st.stop()

    st.subheader("Extracted Content Preview")

    st.text_area(
        "Preview",
        syllabus_text[:3000],
        height=250
    )

    if st.button("Analyze with Gemini AI"):

        with st.spinner("Analyzing syllabus..."):

            result = analyze_syllabus(syllabus_text)

        st.subheader("Analysis Report")

        st.markdown(result)

        st.download_button(
            label="Download Report",
            data=result,
            file_name="academic_reality_report.txt",
            mime="text/plain"
        )

# ==================================
# SIDEBAR
# ==================================

with st.sidebar:

    st.header("About")

    st.write("""
Academic Reality Checker helps students compare
their syllabus with current industry expectations.
""")

    st.write("### Features")
    st.write("✅ PDF Upload")
    st.write("✅ Gemini AI Analysis")
    st.write("✅ Skill Gap Detection")
    st.write("✅ Learning Roadmap")
    st.write("✅ Download Report")

    st.write("---")
    st.caption("Built using Streamlit + Gemini")
```
