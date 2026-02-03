import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURATION & DATA ---
DATA_CATEGORIES = {
    "Identification data and contact details": "name, home address, phone numbers, email, DOB, ID numbers ",
    "Personal characteristics": "age, gender, marital status, languages, emergency contacts ",
    "Immigration data": "visa, passport, work permits ",
    "Composition of household": "name, address and DOB of dependents ",
    "Genetic information": "inherited or genetic characteristics ",
    "Physical data": "size, weight, hair/eye colour, distinctive features ",
    "Biometric information": "facial images, fingerprints, behavioural characteristics ",
    "Health-related data": "physical/mental health, medical certificates ",
    "Aspects of lifestyle": "eating and drinking habits, behavioural data, wellness information that does not qualify as 'health data' ",
    "Complaints/Incidents/Accidents": "information about accidents or complaints involved in ",
    "Leisure activities": "hobbies, sports, interests ",
    "Memberships": "charitable, voluntary, or club memberships ",
    "Electronic localisation data": "GPS tracking, mobile phone location ",
    "Sensitive beliefs": "racial/ethnic origin, religious or philosophical beliefs ",
    "Sex life": "information relating to sex life, sexual orientation ",
    "Political/Union": "political affiliation, mandates, trade union membership ",
    "Judicial details": "criminal records, alleged offences ",
    "Education and training": "CV, degrees, interview notes, certifications ",
    "Profession and job": "salary, function, attendance, work history ",
    "Financial details": "payroll, tax, bank accounts, expenses, pensions ",
    "Performance information": "grades, disciplinary records, absence records ",
    "Picture recordings": "camera recording, photographic recording, video recording, digital photographs, images of surveillance cameras ",
    "Audio recordings" : "tape recording, recorded phone calls or messages",
    "Electronic identification": "User ID, passwords, IP addresses " ,
    "Insurance and benefits": "Health and life insurance claims ",
    "Dietary preferences": "As specified by the user ",
    "social security number": "national social security number"
}

st.set_page_config(page_title="GDPR Notice Generator", layout="wide")

# --- INTRODUCTION ---
st.title("⚖️ GDPR Data Protection Notice Generator")
st.markdown("""
This tool collects information to inform **Data Subjects** (the people whose data you use) about how their personal data is processed.
**Guidance:**
* Consult Key Stakeholders: Speak with department heads, IT teams, and legal advisors who understand your data processing operations.
* Check Data Systems: Examine your databases, CRM systems, HR systems, and other platforms to understand what data you collect and store.
* Look at contracts with service providers, processors, and partners to understand data sharing arrangements.
* Allow Sufficient Time: Completing this questionnaire thoroughly may take 30-60 minutes. Accuracy is more important than speed.
* Each questionnaire relates to one category of data subjects. If you process data about different categories of data subjects, you can repeat the exercise for each new category.
""")

# --- STEP 1: COMPANY INFO ---
st.header("1. General Information")
company_name = st.text_input("Company Name", placeholder="e.g., Acme Corp.")
subject_cat = st.selectbox("Who are the Data Subjects?", 
                          ["Employees", "Customers", "Website Users", "Event Participants", "Loyalty Card Holders", "Athletes", "Other"])
activities = st.text_area("What relevant activities does your company perform?", 
                         placeholder="e.g., Organizing music events and promoting artists.")

# --- STEP 2: PURPOSES ---
st.header("2. Purposes of Processing")
if 'purposes' not in st.session_state:
    st.session_state.purposes = []

with st.form("purpose_form"):
    p_title = st.text_input("Purpose Title", placeholder="e.g., Administration of the Platform")
    p_desc = st.text_area("Plain Language Description", placeholder="Creating user accounts, resetting passwords, etc.")
    add_p = st.form_submit_button("Add Purpose")
    if add_p and p_title:
        st.session_state.purposes.append({"title": p_title, "desc": p_desc, "details": []})

if st.session_state.purposes:
    st.subheader("Current Purposes")
    for i, p in enumerate(st.session_state.purposes):
        st.write(f"**{i+1}. {p['title']}**")

# --- STEP 3: LOOP TOPICS ---
if st.session_state.purposes:
    st.header("3. Detail Data Usage per Purpose")
    for i, p in enumerate(st.session_state.purposes):
        with st.expander(f"Details for: {p['title']}"):
            # 1. Categories
            selected_cats = st.multiselect(f"Select data categories for {p['title']}", 
                                           options=list(DATA_CATEGORIES.keys()), key=f"cat_{i}")
            comment = st.text_input("Additional detail (optional)", key=f"com_{i}")
            
            # 2. Third Parties
            sharing = st.radio("Is data shared with third parties?", ["No", "Yes"], key=f"share_{i}")
            third_party = ""
            if sharing == "Yes":
                third_party = st.text_input("Who is it shared with?", placeholder="""e.g., Hosting providers, analytics services or any external parties that collect or process the data at your request """, key=f"who_{i}")
            
            # 3. Retention
            retention = st.text_input("Retention Period", placeholder="e.g., For as long as the account is active ", key=f"ret_{i}")
            
            # 4. Transfers
            transfers = st.selectbox("International Transfers?", ["No", "Yes (Outside EU/UK)"], key=f"trans_{i}")
            
            # Save progress locally
            p['details'] = {
                "categories": selected_cats,
                "comment": comment,
                "shared": third_party if sharing == "Yes" else "Internal use only",
                "retention": retention,
                "transfers": transfers
            }

# --- STEP 4: GENERATE & DOWNLOAD ---
if st.button("Generate CSV & Final Notice"):
    # Save to CSV
    rows = []
    for p in st.session_state.purposes:
        rows.append({
            "Company": company_name,
            "Subject": subject_cat,
            "Purpose": p['title'],
            "Description": p['desc'],
            "Data": ", ".join(p['details']['categories']),
            "Sharing": p['details']['shared'],
            "Retention": p['details']['retention'],
            "Transfers": p['details']['transfers']
        })
    df = pd.DataFrame(rows)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV Data", csv, "gdpr_data.csv", "text/csv")

    # Display Notice in Browser
    st.markdown("---")
    st.header(f"Data Protection Notice: {company_name}")
    
    st.subheader("Why do we process your personal data?")
    for p in st.session_state.purposes:
        with st.status(f"Click to see: {p['title']}"):
            st.write(p['desc'])

    st.subheader("Which personal data do we use?")
    for p in st.session_state.purposes:
        for cat in p['details']['categories']:
            with st.status(f"Category: {cat}"):
                st.write(f"**Specifics:** {DATA_CATEGORIES[cat]}")
                st.write(f"**Purpose:** {p['title']}")
                st.write(f"**How long we keep it:** {p['details']['retention']} [cite: 35]")
                st.write(f"**Disclosed to:** {p['details']['shared']} [cite: 35]")
                if p['details']['transfers'] != "No":
                    st.warning("Note: This data is transferred outside the EU/UK.")

    st.subheader("What rights do you have over your data? ")
    st.markdown("""
    * **Right to Access**: Request a copy of your data.
    * **Right to Correct**: Update inaccurate information.
    * **Right to Erasure**: Request deletion when no longer necessary.
    * **Right to Object**: Restrict processing under certain conditions.
    * **Right to Data Portability**: Transfer your data to another organization.
    """)
    
    # Reset button after generating notice
    st.markdown("---")
    if st.button("🔄 Start New Questionnaire", type="primary"):
        # Clear all session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()