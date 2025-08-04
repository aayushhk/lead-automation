# apollo_scraper_app.py
from io import BytesIO
import streamlit as st
import pandas as pd
import requests
from urllib.parse import urlparse
import json

st.title("Apollo.io People Extractor")

api_key = st.text_input(" Enter your Apollo API Key", type="password")
apollo_ui_url = st.text_area(" Paste Apollo People Search URL", height=100)
numberpages = st.number_input("Number of pages to fetch", min_value=1, max_value=100, value=1)
perpage = st.number_input("Number of results per page", min_value=1, max_value=100, value=100)

def send_file_to_webhook(file_bytes: bytes, filename: str):
    url = "https://bizmaxus.app.n8n.cloud/webhook/csv"
    files = {"data": (filename, BytesIO(file_bytes), "application/octet-stream")}
    try:
        response = requests.post(url, files=files, timeout=15)
        response.raise_for_status()
        return True, response.text
    except requests.exceptions.RequestException as e:
        return False, str(e)

if st.button("🔍 Fetch Leads"):
    if not api_key or not apollo_ui_url:
        st.error("Please provide both API key and Apollo search URL.")
    else:
        try:
            # Extract query string from Apollo UI URL
            parsed = urlparse(apollo_ui_url)
            query_string = parsed.fragment.replace('/people?', '')
            api_url = f"https://api.apollo.io/api/v1/mixed_people/search?{query_string}&per_page={perpage}&page={numberpages}"

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

                if not people:
                    st.warning("No people found for this query.")
                else:
                    # Convert full raw person data to DataFrame
                    df = pd.json_normalize(people)
                    st.dataframe(df)

                    csv = df.to_csv(index=False).encode('utf-8')
                    
                    success, result = send_file_to_webhook(csv, "apollo_full_leads.csv")
                    st.download_button(
                        "Download CSV",
                        csv,
                        "apollo_leads_full.csv",
                        "text/csv"
                    )
                    if success:
                        st.success(" CSV sent to webhook successfully.")
                    else:
                        st.warning(f" Failed to send CSV to webhook: {result}")
            else:
                st.error(f"API Error {response.status_code}: {response.text}")

        except Exception as e:
            st.error(f"Something went wrong: {e}")


