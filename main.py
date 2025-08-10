from io import BytesIO
import streamlit as st
import pandas as pd
import requests
from urllib.parse import urlparse, parse_qs, urlencode
import re

st.title("Apollo.io People Extractor")

api_key = st.text_input("Enter your Apollo API Key", type="password")
apollo_ui_url = st.text_area("Paste Apollo People Search URL", height=100)
numberpages = st.number_input("Number of pages to fetch", min_value=1, max_value=500, value=1)
perpage = st.number_input("Number of results per page", min_value=1, max_value=100, value=100)

# mapping from frontend (UI) param keys to API param keys
KEY_MAPPING = {
    "personTitles[]": "person_titles[]",
    "personLocations[]": "person_locations[]",
    "personSeniorities[]": "person_seniorities[]",
    "includeSimilarTitles": "include_similar_titles",
    "q_keywords": "q_keywords",
    "organizationLocations[]": "organization_locations[]",
    "q_organization_domains_list[]": "q_organization_domains_list[]",
    "contactEmailStatus[]": "contact_email_status[]",
    "organizationNumEmployeesRanges[]": "organization_num_employees_ranges[]",
    "revenueRange[min]": "revenue_range[min]",
    "revenueRange[max]": "revenue_range[max]",
    "currentlyUsingAllOfTechnologyUids[]": "currently_using_all_of_technology_uids[]",
    "currentlyUsingAnyOfTechnologyUids[]": "currently_using_any_of_technology_uids[]",
    "currentlyNotUsingAnyOfTechnologyUids[]": "currently_not_using_any_of_technology_uids[]",
    "q_organization_job_titles[]": "q_organization_job_titles[]",
    "organizationJobLocations[]": "organization_job_locations[]",
    "organizationNumJobsRange[min]": "organization_num_jobs_range[min]",
    "organizationNumJobsRange[max]": "organization_num_jobs_range[max]",
    "organizationJobPostedAtRange[min]": "organization_job_posted_at_range[min]",
    "organizationJobPostedAtRange[max]": "organization_job_posted_at_range[max]",
    "page": "page",
    "perPage": "per_page",
}

def rename_apollo_params(params: dict) -> dict:
    """Rename frontend-style Apollo UI params to API-ready snake_case keys."""
    api_params = {}
    for key, values in params.items():
        mapped_key = KEY_MAPPING.get(key)
        final_key = mapped_key if mapped_key else re.sub(r'([A-Z])', lambda m: '_' + m.group(1).lower(), key)
        api_params[final_key] = values
        #st.info(f"Renaming {key} to {final_key}")
    return api_params

def send_file_to_webhook(file_bytes: bytes, filename: str):
    url = "https://bizmaxus.app.n8n.cloud/webhook/csv"
    files = {"data": (filename, BytesIO(file_bytes), "application/octet-stream")}
    try:
        resp = requests.post(url, files=files, timeout=15)
        resp.raise_for_status()
        return True, resp.text
    except Exception as e:
        return False, str(e)

if st.button("🔍 Fetch Leads"):
    if not api_key or not apollo_ui_url:
        st.error("Please provide both API key and Apollo search URL.")
    else:
        try:
            parsed = urlparse(apollo_ui_url)
            raw_qs = parse_qs(parsed.fragment.split('/people?')[-1])
            
            # Rename keys to match API format
            api_qs = rename_apollo_params(raw_qs)
            # Add page and per_page override or append if not present
            api_qs["page"] = [str(numberpages)]
            api_qs["per_page"] = [str(perpage)]

            # Build final URL
            query = urlencode(api_qs, doseq=True)
            api_url = f"https://api.apollo.io/api/v1/mixed_people/search?{query}"

            headers = {
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            st.info("Fetching results from Apollo.io...")
            response = requests.post(api_url, headers=headers, json={})

            if response.status_code == 200:
                data = response.json()
                people = data.get("people", [])
                if people:
                    df = pd.json_normalize(people)
                    st.dataframe(df)
                    csv = df.to_csv(index=False).encode("utf-8")
                    
                    st.info("Sending CSV to webhook...")
                    success, result = send_file_to_webhook(csv, "apollo_full_leads.csv")
                    st.download_button("Download CSV", csv, "apollo_leads_full.csv", "text/csv")
                    if success:
                        st.success("CSV sent to webhook successfully.")
                    else:
                        st.warning(f"Failed to send CSV to webhook: {result}")
                else:
                    st.warning("No people found for this query.")
            else:
                st.error(f"API Error {response.status_code}: {response.text}")

        except Exception as e:
            st.error(f"Something went wrong: {e}")
