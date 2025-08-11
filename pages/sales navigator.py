from io import BytesIO
import requests
import pandas as pd
import streamlit as st

# --- Function to send file to webhook ---
def send_file_to_webhook(file_bytes: bytes, filename: str):
    url = "https://bizmaxus.app.n8n.cloud/webhook/salesnav"
    files = {"data": (filename, BytesIO(file_bytes), "application/octet-stream")}
    try:
        response = requests.post(url, files=files, timeout=15)
        response.raise_for_status()
        return True, response.text
    except requests.exceptions.RequestException as e:
        return False, str(e)

# --- Initialize session state ---
if "df_result" not in st.session_state:
    st.session_state.df_result = None
if "csv_bytes" not in st.session_state:
    st.session_state.csv_bytes = None

# --- Column mapping ---
COLUMN_MAPPING = {
    "person.id": "id",
    "person.first_name": "first_name",
    "person.last_name": "last_name",
    "person.name": "name",
    "person.linkedin_url": "linkedin_url",
    "person.title": "title",
    "person.email_status": "email_status",
    "person.photo_url": "photo_url",
    "person.twitter_url": "twitter_url",
    "person.github_url": "github_url",
    "person.facebook_url": "facebook_url",
    "person.extrapolated_email_confidence": "extrapolated_email_confidence",
    "person.headline": "headline",
    "person.email": "email",
    "person.organization_id": "organization_id",
    "person.employment_history": "employment_history",
    "person.state": "state",
    "person.city": "city",
    "person.country": "country",
    "person.departments": "departments",
    "person.subdepartments": "subdepartments",
    "person.seniority": "seniority",
    "person.functions": "functions",
    "person.intent_strength": "intent_strength",
    "person.show_intent": "show_intent",
    "person.email_domain_catchall": "email_domain_catchall",
    "person.revealed_for_current_team": "revealed_for_current_team",
    "person.organization.id": "organization.id",
    "person.organization.name": "organization.name",
    "person.organization.website_url": "organization.website_url",
    "person.organization.blog_url": "organization.blog_url",
    "person.organization.angellist_url": "organization.angellist_url",
    "person.organization.linkedin_url": "organization.linkedin_url",
    "person.organization.twitter_url": "organization.twitter_url",
    "person.organization.facebook_url": "organization.facebook_url",
    "person.organization.primary_phone.number": "organization.primary_phone.number",
    "person.organization.primary_phone.source": "organization.primary_phone.source",
    "person.organization.primary_phone.sanitized_number": "organization.primary_phone.sanitized_number",
    "person.organization.languages": "organization.languages",
    "person.organization.alexa_ranking": "organization.alexa_ranking",
    "person.organization.phone": "organization.phone",
    "person.organization.linkedin_uid": "organization.linkedin_uid",
    "person.organization.founded_year": "organization.founded_year",
    "person.organization.publicly_traded_symbol": "organization.publicly_traded_symbol",
    "person.organization.publicly_traded_exchange": "organization.publicly_traded_exchange",
    "person.organization.logo_url": "organization.logo_url",
    "person.organization.crunchbase_url": "organization.crunchbase_url",
    "person.organization.primary_domain": "organization.primary_domain",
    "person.organization.sanitized_phone": "organization.sanitized_phone",
    "person.organization.organization_headcount_six_month_growth": "organization.organization_headcount_six_month_growth",
    "person.organization.organization_headcount_twelve_month_growth": "organization.organization_headcount_twelve_month_growth",
    "person.organization.organization_headcount_twenty_four_month_growth": "organization.organization_headcount_twenty_four_month_growth",
    "person.organization.market_cap": "organization.market_cap",
}

# --- Streamlit UI ---
st.title("Apollo.io Lead Enrichment Tool")

st.subheader("🔑 API Authentication")
api_key = st.text_input("Apollo API Key", type="password")

st.subheader("🧭 Sales Navigator")
st.write("Use the fields below to refine your search. You can leave fields empty to search broadly. Results will be enriched with Apollo.io data. ")

with st.container(border=True):

    linkedin_url = st.text_input("LinkedIn URL")
with st.expander("Optional Search search fields", expanded=False):
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    name = st.text_input("Full Name")
    email = st.text_input("Email")
    hashed_email = st.text_input("Hashed Email")
    organization_name = st.text_input("Organization Name")
    domain = st.text_input("Domain")
    person_id = st.text_input("Person ID")

reveal_personal_emails = st.checkbox("Reveal Personal Emails", value=True)
reveal_phone_number = st.checkbox("Reveal Phone Number", value=False)

webhook_url = ""
if reveal_phone_number:
    webhook_url = st.text_input(
        "Webhook URL (Required if revealing phone numbers)",
        value="https://bizmaxus.app.n8n.cloud/webhook/salesnav"
    )

# --- Enrich Lead Button ---
if st.button("🔍 Enrich Lead"):
    if not api_key:
        st.error("Please enter your Apollo API Key.")
    elif reveal_phone_number and not webhook_url:
        st.error("Webhook URL is required when Reveal Phone Number is enabled.")
    else:
        params = {
            "first_name": first_name,
            "last_name": last_name,
            "name": name,
            "email": email,
            "hashed_email": hashed_email,
            "organization_name": organization_name,
            "domain": domain,
            "id": person_id,
            "linkedin_url": linkedin_url,
            "reveal_personal_emails": str(reveal_personal_emails).lower()
        }

        if reveal_phone_number:
            params["reveal_phone_number"] = "true"
            params["webhook_url"] = webhook_url
        else:
            params["reveal_phone_number"] = "false"

        params = {k: v for k, v in params.items() if v}

        url = "https://api.apollo.io/api/v1/people/match"
        headers = {
            "accept": "application/json",
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "x-api-key": api_key
        }

        try:
            with st.spinner("Enriching lead..."):
                response = requests.post(url, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                if data:
                    # Normalize and rename columns
                    df_result = pd.json_normalize(data)
                    df_result.rename(columns=COLUMN_MAPPING, inplace=True)

                    # Ensure all expected columns are present
                    for col in COLUMN_MAPPING.values():
                        if col not in df_result.columns:
                            df_result[col] = None

                    # Reorder columns based on mapping order
                    df_result = df_result[list(COLUMN_MAPPING.values())]

                    st.session_state.df_result = df_result
                    st.session_state.csv_bytes = df_result.to_csv(index=False).encode('utf-8')
                    st.success("Lead enrichment request sent successfully!")

                    if reveal_phone_number:
                        st.info("📞 Phone numbers will be sent asynchronously to your webhook URL.")
                else:
                    st.warning("No data returned from Apollo.")
            else:
                st.error(f"Error: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {str(e)}")

# --- Show results if available ---
if st.session_state.df_result is not None:
    st.subheader("📊 Enriched Lead Data")
    st.dataframe(st.session_state.df_result)

    st.download_button(
        "📥 Download CSV",
        data=st.session_state.csv_bytes if st.session_state.csv_bytes else b"",
        file_name="enriched_lead.csv",
        mime="text/csv"
    )

    if st.button("📤 Add Lead to Campaign"):
        if st.session_state.csv_bytes:
            success, msg = send_file_to_webhook(st.session_state.csv_bytes, "enriched_lead.csv")
            if success:
                st.success(f"✅ Lead sent to campaign successfully! Response: {msg}")
            else:
                st.error(f"❌ Failed to send lead: {msg}")
        else:
            st.error("❌ No CSV data available to send.")
