import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# ---------------------------------
# PAGE CONFIG
# ---------------------------------

st.set_page_config(
    page_title="Academic Reality Checker",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 Academic Reality Checker")
st.write("Upload your syllabus PDF and compare it with industry requirements using Gemini AI.")

# ---------------------------------
# GEMINI API KEY
# ---------------------------------

api_key = ""

try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    pass

if not api_key:
    api_key = st.text_input(
        "Enter Gemini API Key",
        type="password"
    )

if not api_key:
    st.info("Please enter your Gemini API key to continue.")
    st.stop()

genai.configure(api_key=api_key)

# ---------------------------------
# PDF TEXT EXTRACTION
# ---------------------------------

def extract_pdf_text(uploaded_file):
    text = ""

    try:
        reader = PdfReader(uploaded_file)

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    except Exception as e:
        st.error(f"Error reading PDF: {e}")

    return text

# ---------------------------------
# GEMINI ANALYSIS
# ---------------------------------

def analyze_syllabus(text):

    prompt = f"""
You are an expert career mentor and placement trainer.

Analyze this syllabus and provide:

1. Subjects and Skills Found
2. Missing Industry Skills
3. Placement Readiness Score (0-100)
4. Gap Analysis
5. Recommended Technologies
6. Recommended Certifications
7. Project Ideas
8. Learning Roadmap
9. Internship Preparation Tips

Syllabus:

{text[:12000]}
"""

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")

        response = model.generate_content(prompt)

        return response.text

    except Exception as e:
        return f"Gemini Error: {str(e)}"

# ---------------------------------
# FILE UPLOAD
# ---------------------------------

uploaded_file = st.file_uploader(
    "Upload Syllabus PDF",
    type=["pdf"]
)

if uploaded_file:

    st.success("PDF Uploaded Successfully")

    with st.spinner("Extracting text from PDF..."):
        syllabus_text = extract_pdf_text(uploaded_file)

    if syllabus_text.strip() == "":
        st.error("Could not extract text from PDF.")
        st.stop()

    st.subheader("Syllabus Preview")

    st.text_area(
        "Extracted Text",
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

# ---------------------------------
# SIDEBAR
# ---------------------------------

with st.sidebar:

    st.header("About Project")

    st.write("""
This project compares a college syllabus
with current industry requirements and
generates an AI-powered learning roadmap.
""")

    st.markdown("### Features")
    st.write("✅ PDF Upload")
    st.write("✅ Gemini AI Analysis")
    st.write("✅ Skill Gap Detection")
    st.write("✅ Placement Readiness Score")
    st.write("✅ Learning Roadmap")
    st.write("✅ Download Report")
