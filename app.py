# app.py

import subprocess
import sys

# -- Auto-install required packages if missing --
def install_if_missing(package):
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# List of required base modules
required_modules = [
    "streamlit",
    "pandas",
    "chardet",
    "xlsxwriter",
    "thefuzz"
]

for module in required_modules:
    import_name = "thefuzz" if module == "thefuzz" else module
    install_if_missing(import_name)

# -- Safe to import everything now --
import streamlit as st
from logica import match_linkedin_bullhorn

# -- Streamlit App UI --
st.set_page_config(page_title="LinkedIn vs Bullhorn Matcher", layout="centered")
st.title("🔍 LinkedIn vs Bullhorn Rol/Bedrijf Change Checker")

st.markdown("""
Upload two CSV files: one exported from **LinkedIn**, and one from **Bullhorn**.  
Then click the button to run the role and company change analysis.
""")

# Uploads
file1 = st.file_uploader("📄 Upload first CSV", type="csv")
file2 = st.file_uploader("📄 Upload second CSV", type="csv")

# Sliders for fuzzy threshold
fuzzy_company = st.slider("🏢 Company match sensitivity", 0, 100, 60)
fuzzy_role = st.slider("🧑‍💼 Role match sensitivity", 0, 100, 60)

# Only show button if both files are uploaded
if file1 and file2:
    if st.button("▶️ Run Analysis"):
        try:
            output = match_linkedin_bullhorn(file1, file2, fuzzy_company, fuzzy_role)
            st.success("✅ Matching completed successfully!")
            st.download_button(
                label="📥 Download Excel Report",
                data=output,
                file_name="role_change_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"❌ Something went wrong:\n\n{e}")
