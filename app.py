# app.py

# -- Safe to import everything now --
import streamlit as st
from logica import match_linkedin_bullhorn

# -- Streamlit App UI --
st.set_page_config(page_title="LinkedIn vs Bullhorn Matcher", layout="centered")
st.title("🔍 LinkedIn vs Bullhorn Rol/Bedrijf Change Checker")

st.markdown("""
Upload twee CSV files: ééntje geëxporteerd van **LinkedIn**, en de andere uit **Bullhorn**. Zorg ervoor dat je bij het exporteren van Bullhorn de kolommen aantikt uit "CSV_Export". Die komen overeen met Naam, Huidige functietitel, en Bedrijf.  
Na het uploaden van de bestanden, kun je de fuzzy matching gevoeligheid aanpassen voor zowel bedrijfsnamen als functietitels tussen 0 en 100. Rond de 60 is aangeraden voor bedrijf, voor functietitel kan je wat strenger zijn, hier kan je mee spelen.
Belangrijk om te vermelden: dit is een fuzzy matching tool, dus het is mogelijk dat er fouten in de matching zitten. Controleer goed de resultaten voor je deze gebruikt, vooral bij mensen met namen die veel voorkomen (sophie bakker bijv.)
""")

# Uploads
file1 = st.file_uploader("📄 Upload Bullhorn CSV", type="csv")
file2 = st.file_uploader("📄 Upload LinkedIn CSV", type="csv")

# Sliders for fuzzy threshold
fuzzy_company = st.slider("Sensitiviteit bedrijf", 0, 100, 60)
fuzzy_role = st.slider("Sensitiviteit functietitel", 0, 100, 60)

# Only show button if both files are uploaded
if file1 and file2:
    if st.button("▶️ Run Analyse"):
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
