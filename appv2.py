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
    "Personal beliefs": "religious or philosophical beliefs ",
    "Ethnicity": "information on racial/ethnic origin",
    "Sex life": "information relating to sexual activity or sexual orientation ",
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
    "Dietary preferences": "Dietary restrictions or preferences as specified by the user ",
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

            # Multiple additional categories
            if f"extra_cats_{i}" not in st.session_state:
                st.session_state[f"extra_cats_{i}"] = []

            with st.form(key=f"extra_cat_form_{i}"):
                new_extra = st.text_input("Add additional data category (optional)", 
                               placeholder="e.g., Preferred language, nickname")
                if st.form_submit_button("➕ Add") and new_extra.strip():
                    st.session_state[f"extra_cats_{i}"].append(new_extra.strip())

            if st.session_state[f"extra_cats_{i}"]:
                st.write("**Added custom categories:**")
                for j, item in enumerate(st.session_state[f"extra_cats_{i}"]):
                    col1, col2 = st.columns([5, 1])
                    col1.write(f"- {item}")
                    if col2.button("✕", key=f"del_extra_{i}_{j}"):
                        st.session_state[f"extra_cats_{i}"].pop(j)
                        st.rerun()

            comment = ", ".join(st.session_state[f"extra_cats_{i}"])

            # 2. Direct Collection
            st.markdown("---")
            direct_collection = st.radio(
                "Is this information obtained directly from the data subject?",
                ["Yes", "No"],
                key=f"direct_{i}"
            )
            indirect_source = ""
            if direct_collection == "No":
                indirect_source = st.text_input(
                    "How is this information obtained? Please specify the source(s).",
                    placeholder="e.g., Third-party data brokers, publicly available sources, employer records, credit reference agencies",
                    key=f"indirect_src_{i}"
                )

            # 3. Third Parties
            st.markdown("---")
            sharing = st.radio("Is data shared with third parties?", ["No", "Yes"], key=f"share_{i}")
            third_party = ""
            if sharing == "Yes":
                third_party = st.text_input("Who is it shared with?", placeholder="""e.g., Hosting providers, analytics services or any external parties that collect or process the data at your request """, key=f"who_{i}")
            
            # 4. Retention
            retention = st.text_input("Retention Period", placeholder="e.g., For as long as the account is active ", key=f"ret_{i}")
            
            # 5. Transfers
            transfers = st.selectbox("International Transfers?", ["No", "Yes (Outside EU/UK)"], key=f"trans_{i}")
            
            # Save progress locally
            p['details'] = {
                "categories": selected_cats,
                "comment": comment,
                "direct_collection": direct_collection,
                "indirect_source": indirect_source if direct_collection == "No" else "",
                "shared": third_party if sharing == "Yes" else "Internal use only",
                "retention": retention,
                "transfers": transfers
            }

# --- STEP 4: GENERATE & DOWNLOAD ---
if st.button("Generate Excel & Final Notice"):
    
    # --- Sheet 1: Purposes / Responses ---
    rows = []
    for p in st.session_state.purposes:
        rows.append({
            "Company": company_name,
            "Subject Category": subject_cat,
            "Purpose": p['title'],
            "Description": p['desc'],
            "Data Categories": ", ".join(p['details']['categories']),
            "Obtained Directly from Data Subject": p['details']['direct_collection'],
            "Source if Not Direct": p['details']['indirect_source'],
            "Sharing": p['details']['shared'],
            "Retention": p['details']['retention'],
            "Transfers": p['details']['transfers']
        })

    df_purposes = pd.DataFrame(rows)

    # --- Sheet 2: Company Information ---
    df_company = pd.DataFrame([{
        "Company Name": company_name,
        "Data Subjects": subject_cat,
        "Company Activities": activities
    }])

    # --- Create Excel file in memory ---
    from io import BytesIO
    output = BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_purposes.to_excel(writer, index=False, sheet_name='Processing Details')
        df_company.to_excel(writer, index=False, sheet_name='Company Info')

    output.seek(0)

    st.download_button(
        label="Download Excel File",
        data=output,
        file_name="gdpr_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # --- Display Notice in Browser (unchanged) ---
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
                st.write(f"**How long we keep it:** {p['details']['retention']}")
                st.write(f"**Disclosed to:** {p['details']['shared']}")
                if p['details']['direct_collection'] == "Yes":
                    st.write("**Source:** Obtained directly from you.")
                else:
                    source_text = p['details']['indirect_source'] if p['details']['indirect_source'] else "Not specified"
                    st.write(f"**Source:** Not obtained directly from you — {source_text}")
                if p['details']['transfers'] != "No":
                    st.warning("Note: This data is transferred outside the EU/UK.")

    st.subheader("What rights do you have over your data?")
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
