import streamlit as st
import pandas as pd
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from io import BytesIO

# --- CONFIGURATION ---
# In Streamlit Secrets, define companies as:
#
# [companies]
# "acme-code-1234" = "Acme Corp"
# "globex-code-9981" = "Globex Industries"
#
# Each key is the access code, each value is the company display name.

SHEET_NAME = "GDPR Questionnaire Data"

DATA_CATEGORIES = {
    "Identification data and contact details": "name, home address, phone numbers, email, DOB, ID numbers",
    "Personal characteristics": "age, gender, marital status, languages, emergency contacts",
    "Immigration data": "visa, passport, work permits",
    "Composition of household": "name, address and DOB of dependents",
    "Genetic information": "inherited or genetic characteristics",
    "Physical data": "size, weight, hair/eye colour, distinctive features",
    "Biometric information": "facial images, fingerprints, behavioural characteristics",
    "Health-related data": "physical/mental health, medical certificates",
    "Aspects of lifestyle": "eating and drinking habits, behavioural data, wellness information that does not qualify as 'health data'",
    "Complaints/Incidents/Accidents": "information about accidents or complaints involved in",
    "Leisure activities": "hobbies, sports, interests",
    "Memberships": "charitable, voluntary, or club memberships",
    "Electronic localisation data": "GPS tracking, mobile phone location",
    "Personal beliefs": "religious or philosophical beliefs",
    "Ethnicity": "information on racial/ethnic origin",
    "Sex life": "information relating to sexual activity or sexual orientation",
    "Political/Union": "political affiliation, mandates, trade union membership",
    "Judicial details": "criminal records, alleged offences",
    "Education and training": "CV, degrees, interview notes, certifications",
    "Profession and job": "salary, function, attendance, work history",
    "Financial details": "payroll, tax, bank accounts, expenses, pensions",
    "Performance information": "grades, disciplinary records, absence records",
    "Picture recordings": "camera recording, photographic recording, video recording, digital photographs, images of surveillance cameras",
    "Audio recordings": "tape recording, recorded phone calls or messages",
    "Electronic identification": "User ID, passwords, IP addresses",
    "Insurance and benefits": "Health and life insurance claims",
    "Dietary preferences": "Dietary restrictions or preferences as specified by the user",
    "Social security number": "national social security number"
}


# --- AUTHENTICATION HELPERS ---

def get_companies():
    return dict(st.secrets.get("companies", {}))

def validate_code(code):
    return get_companies().get(code.strip())

def make_tab_name(company_name):
    safe = company_name
    for ch in ["\\", "/", "?", "*", "[", "]", ":"]:
        safe = safe.replace(ch, "-")
    safe = safe.strip("'")
    return safe[:100]


# --- GOOGLE SHEETS CONNECTION ---

def get_gsheet_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    return gspread.authorize(creds)

def load_data_from_sheet(company_name):
    tab = make_tab_name(company_name)
    try:
        client = get_gsheet_client()
        sheet = client.open(SHEET_NAME).worksheet(tab)
        records = sheet.get_all_records()
        if records:
            raw = records[0].get("state", "{}")
            return json.loads(raw)
    except gspread.exceptions.WorksheetNotFound:
        pass
    except Exception as e:
        st.warning(f"Could not load saved data: {e}")
    return {}

def save_data_to_sheet(company_name, state_dict):
    tab = make_tab_name(company_name)
    try:
        client = get_gsheet_client()
        spreadsheet = client.open(SHEET_NAME)
        try:
            sheet = spreadsheet.worksheet(tab)
        except gspread.exceptions.WorksheetNotFound:
            sheet = spreadsheet.add_worksheet(title=tab, rows=10, cols=3)
            sheet.update("A1:B1", [["last_updated", "state"]])

        state_json = json.dumps(state_dict, default=str)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        all_values = sheet.get_all_values()
        if len(all_values) > 1:
            sheet.update("A2:B2", [[now, state_json]])
        else:
            sheet.append_row([now, state_json])
        return True
    except Exception as e:
        st.error(f"Could not save data: {e}")
        return False


# --- STATE HELPERS ---

def extract_saveable_state():
    saveable = {}
    for key in ["company_name", "subject_cat", "activities", "purposes"]:
        if key in st.session_state:
            saveable[key] = st.session_state[key]
    for i in range(len(st.session_state.get("purposes", []))):
        k = f"extra_cats_{i}"
        if k in st.session_state:
            saveable[k] = st.session_state[k]
    return saveable

def restore_state(saved):
    for key, value in saved.items():
        if key not in st.session_state:
            st.session_state[key] = value


# --- PAGE CONFIG ---
st.set_page_config(page_title="GDPR Notice Generator", layout="wide")


# =============================================
# ACCESS CODE GATE
# =============================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_company" not in st.session_state:
    st.session_state.current_company = None

if not st.session_state.authenticated:
    st.title("⚖️ GDPR Data Protection Notice Generator")
    st.markdown("---")
    st.subheader("🔒 Please enter your access code to continue")
    col1, col2 = st.columns([2, 3])
    with col1:
        code_input = st.text_input("Access Code", type="password", placeholder="Enter your code...")
        if st.button("Unlock", type="primary"):
            company = validate_code(code_input)
            if company:
                st.session_state.authenticated = True
                st.session_state.current_company = company
                with st.spinner(f"Loading saved progress for {company}..."):
                    saved = load_data_from_sheet(company)
                    if saved:
                        restore_state(saved)
                        st.success(f"✅ Progress loaded for **{company}**!")
                    else:
                        st.info(f"No saved progress found for **{company}**. Starting fresh.")
                st.rerun()
            else:
                st.error("Incorrect access code. Please try again.")
    st.stop()


# =============================================
# MAIN APP
# =============================================
company = st.session_state.current_company

if "purposes" not in st.session_state:
    st.session_state.purposes = []

# --- HEADER ---
col_title, col_company, col_save = st.columns([3, 2, 1])
with col_title:
    st.title("⚖️ GDPR Data Protection Notice Generator")
with col_company:
    st.markdown("<br>", unsafe_allow_html=True)
    st.info(f"🏢 Logged in as: **{company}**")
with col_save:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 Save Progress", type="primary"):
        with st.spinner("Saving..."):
            if save_data_to_sheet(company, extract_saveable_state()):
                st.success("Saved!")

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

company_name = st.text_input(
    "Company Name",
    value=st.session_state.get("company_name", company),
    placeholder="e.g., Acme Corp.",
    key="company_name"
)
subject_options = ["Employees", "Customers", "Website Users", "Event Participants", "Loyalty Card Holders", "Athletes", "Other"]
subject_cat = st.selectbox(
    "Who are the Data Subjects?",
    subject_options,
    index=subject_options.index(st.session_state.get("subject_cat", "Employees")),
    key="subject_cat"
)
activities = st.text_area(
    "What relevant activities does your company perform?",
    value=st.session_state.get("activities", ""),
    placeholder="e.g., Organizing music events and promoting artists.",
    key="activities"
)

# --- STEP 2: PURPOSES ---
st.header("2. Purposes of Processing")

with st.form("purpose_form"):
    p_title = st.text_input("Purpose Title", placeholder="e.g., Administration of the Platform")
    p_desc = st.text_area("Plain Language Description", placeholder="Creating user accounts, resetting passwords, etc.")
    if st.form_submit_button("Add Purpose") and p_title:
        st.session_state.purposes.append({"title": p_title, "desc": p_desc, "details": {}})

if st.session_state.purposes:
    st.subheader("Current Purposes")
    for i, p in enumerate(st.session_state.purposes):
        c1, c2 = st.columns([6, 1])
        c1.write(f"**{i+1}. {p['title']}**")
        if c2.button("🗑️", key=f"del_purpose_{i}", help="Remove this purpose"):
            st.session_state.purposes.pop(i)
            st.rerun()

# --- STEP 3: DETAIL PER PURPOSE ---
if st.session_state.purposes:
    st.header("3. Detail Data Usage per Purpose")
    for i, p in enumerate(st.session_state.purposes):
        with st.expander(f"Details for: {p['title']}"):
            saved_details = p.get("details", {})

            # --- Data Categories ---
            default_cats = saved_details.get("categories", [])
            selected_cats = st.multiselect(
                f"Select data categories for {p['title']}",
                options=list(DATA_CATEGORIES.keys()),
                default=[c for c in default_cats if c in DATA_CATEGORIES],
                key=f"cat_{i}"
            )

            # Extra custom categories
            if f"extra_cats_{i}" not in st.session_state:
                st.session_state[f"extra_cats_{i}"] = saved_details.get("extra_cats", [])

            with st.form(key=f"extra_cat_form_{i}"):
                new_extra = st.text_input(
                    "Add additional data category (optional)",
                    placeholder="e.g., Preferred language, nickname"
                )
                if st.form_submit_button("➕ Add") and new_extra.strip():
                    st.session_state[f"extra_cats_{i}"].append(new_extra.strip())

            if st.session_state[f"extra_cats_{i}"]:
                st.write("**Added custom categories:**")
                for j, item in enumerate(st.session_state[f"extra_cats_{i}"]):
                    c1, c2 = st.columns([5, 1])
                    c1.write(f"- {item}")
                    if c2.button("✕", key=f"del_extra_{i}_{j}"):
                        st.session_state[f"extra_cats_{i}"].pop(j)
                        st.rerun()

            comment = ", ".join(st.session_state[f"extra_cats_{i}"])

            # --- Direct Collection: per-category Yes/No ---
            st.markdown("---")
            st.markdown("**Is this information obtained directly from the data subject?**")

            # Combine standard selected + custom extra categories for the toggle list
            all_cats_for_purpose = selected_cats + st.session_state[f"extra_cats_{i}"]

            # Load previously saved per-category direct values
            saved_direct_per_cat = saved_details.get("direct_per_cat", {})

            direct_per_cat = {}

            if all_cats_for_purpose:
                # Header row
                h1, h2, h3 = st.columns([4, 1, 1])
                h1.markdown("**Data Category**")
                h2.markdown("**Yes**")
                h3.markdown("**No**")
                st.markdown("<hr style='margin: 4px 0'>", unsafe_allow_html=True)

                for cat in all_cats_for_purpose:
                    # Sanitise category name for use as a widget key
                    cat_key = cat.replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "")
                    widget_key = f"direct_{i}_{cat_key}"

                    # Determine saved default: True = direct (Yes), False = not direct (No)
                    saved_val = saved_direct_per_cat.get(cat, True)  # default Yes

                    col_label, col_yes, col_no = st.columns([4, 1, 1])
                    col_label.write(cat)

                    # Use a selectbox rendered as two radio-style columns
                    # We store as bool: True = Yes (direct), False = No (not direct)
                    current_val = st.session_state.get(widget_key, saved_val)

                    yes_style = "primary" if current_val else "secondary"
                    no_style  = "primary" if not current_val else "secondary"

                    if col_yes.button("Yes", key=f"{widget_key}_yes", type=yes_style, use_container_width=True):
                        st.session_state[widget_key] = True
                        st.rerun()
                    if col_no.button("No", key=f"{widget_key}_no", type=no_style, use_container_width=True):
                        st.session_state[widget_key] = False
                        st.rerun()

                    direct_per_cat[cat] = st.session_state.get(widget_key, saved_val)

            else:
                st.caption("No data categories selected yet. Select categories above to answer this question.")

            # Single shared source field shown below the table
            st.markdown("---")
            indirect_source = st.text_area(
                "If the information is not obtained directly from the data subject, please specify the source here.",
                value=saved_details.get("indirect_source", ""),
                placeholder="e.g., Third-party data brokers, publicly available sources, employer records, credit reference agencies",
                key=f"indirect_src_{i}",
                height=80
            )

            # --- Third Parties ---
            st.markdown("---")
            share_options = ["No", "Yes"]
            share_default = "Yes" if saved_details.get("shared", "Internal use only") != "Internal use only" else "No"
            sharing = st.radio(
                "Is data shared with third parties?",
                share_options,
                index=share_options.index(share_default),
                key=f"share_{i}"
            )
            third_party = ""
            if sharing == "Yes":
                third_party = st.text_input(
                    "Who is it shared with?",
                    value=saved_details.get("shared", "") if share_default == "Yes" else "",
                    placeholder="e.g., Hosting providers, analytics services",
                    key=f"who_{i}"
                )

            # --- Retention ---
            retention = st.text_input(
                "Retention Period",
                value=saved_details.get("retention", ""),
                placeholder="e.g., For as long as the account is active",
                key=f"ret_{i}"
            )

            # --- Transfers ---
            trans_options = ["No", "Yes (Outside EU/UK)"]
            trans_default = saved_details.get("transfers", "No")
            transfers = st.selectbox(
                "International Transfers?",
                trans_options,
                index=trans_options.index(trans_default) if trans_default in trans_options else 0,
                key=f"trans_{i}"
            )

            # Write back to purpose details
            p['details'] = {
                "categories": selected_cats,
                "extra_cats": st.session_state[f"extra_cats_{i}"],
                "comment": comment,
                "direct_per_cat": direct_per_cat,
                "indirect_source": indirect_source,
                "shared": third_party if sharing == "Yes" else "Internal use only",
                "retention": retention,
                "transfers": transfers
            }

# --- STEP 4: GENERATE & DOWNLOAD ---
st.markdown("---")
if st.button("📄 Generate Excel & Final Notice"):
    rows = []
    for p in st.session_state.purposes:
        d = p.get('details', {})
        direct_per_cat = d.get('direct_per_cat', {})

        # One row per data category for clarity in the export
        all_cats = d.get('categories', []) + ([c for c in [d.get('comment', '')] if c])
        cats_list = d.get('categories', [])
        extra_list = d.get('extra_cats', [])
        all_cats_export = cats_list + extra_list

        if all_cats_export:
            for cat in all_cats_export:
                rows.append({
                    "Company": st.session_state.get("company_name", ""),
                    "Subject Category": st.session_state.get("subject_cat", ""),
                    "Purpose": p['title'],
                    "Description": p['desc'],
                    "Data Category": cat,
                    "Obtained Directly from Data Subject": "Yes" if direct_per_cat.get(cat, True) else "No",
                    "Source if Not Direct": d.get('indirect_source', '') if not direct_per_cat.get(cat, True) else "",
                    "Sharing": d.get('shared', ''),
                    "Retention": d.get('retention', ''),
                    "Transfers": d.get('transfers', '')
                })
        else:
            rows.append({
                "Company": st.session_state.get("company_name", ""),
                "Subject Category": st.session_state.get("subject_cat", ""),
                "Purpose": p['title'],
                "Description": p['desc'],
                "Data Category": "",
                "Obtained Directly from Data Subject": "",
                "Source if Not Direct": d.get('indirect_source', ''),
                "Sharing": d.get('shared', ''),
                "Retention": d.get('retention', ''),
                "Transfers": d.get('transfers', '')
            })

    df_purposes = pd.DataFrame(rows)
    df_company = pd.DataFrame([{
        "Company Name": st.session_state.get("company_name", ""),
        "Data Subjects": st.session_state.get("subject_cat", ""),
        "Company Activities": st.session_state.get("activities", "")
    }])

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_purposes.to_excel(writer, index=False, sheet_name='Processing Details')
        df_company.to_excel(writer, index=False, sheet_name='Company Info')
    output.seek(0)

    st.download_button(
        label="⬇️ Download Excel File",
        data=output,
        file_name=f"gdpr_{make_tab_name(company)}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # --- Final Notice ---
    st.markdown("---")
    st.header(f"Data Protection Notice: {st.session_state.get('company_name', '')}")

    st.subheader("Why do we process your personal data?")
    for p in st.session_state.purposes:
        with st.status(f"Click to see: {p['title']}"):
            st.write(p['desc'])

    st.subheader("Which personal data do we use?")
    for p in st.session_state.purposes:
        d = p.get('details', {})
        direct_per_cat = d.get('direct_per_cat', {})
        all_cats = d.get('categories', []) + d.get('extra_cats', [])
        for cat in all_cats:
            with st.status(f"Category: {cat}"):
                st.write(f"**Specifics:** {DATA_CATEGORIES.get(cat, cat)}")
                st.write(f"**Purpose:** {p['title']}")
                st.write(f"**How long we keep it:** {d.get('retention', '')}")
                st.write(f"**Disclosed to:** {d.get('shared', '')}")
                is_direct = direct_per_cat.get(cat, True)
                if is_direct:
                    st.write("**Source:** Obtained directly from you.")
                else:
                    source_text = d.get('indirect_source') or "Not specified"
                    st.write(f"**Source:** Not obtained directly from you — {source_text}")
                if d.get('transfers', 'No') != "No":
                    st.warning("Note: This data is transferred outside the EU/UK.")

    st.subheader("What rights do you have over your data?")
    st.markdown("""
    * **Right to Access**: Request a copy of your data.
    * **Right to Correct**: Update inaccurate information.
    * **Right to Erasure**: Request deletion when no longer necessary.
    * **Right to Object**: Restrict processing under certain conditions.
    * **Right to Data Portability**: Transfer your data to another organization.
    """)

st.markdown("---")
if st.button("🔄 Start New Questionnaire", type="secondary"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
