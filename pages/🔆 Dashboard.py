import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(page_title="Lead Dashboard", layout="wide")
st.title("📊 Lead Interaction Dashboard")

# --- Define endpoints ---
BASE_URL = "https://bizmaxus.app.n8n.cloud/webhook"
ENDPOINTS = {
    "Incoming": f"{BASE_URL}/incoming",
    "Outgoing": f"{BASE_URL}/outgoing",
    "SMS": f"{BASE_URL}/sms",
    "Followup": f"{BASE_URL}/followup",
    "Replied": f"{BASE_URL}/replied",
    "Awaiting": f"{BASE_URL}/awaiting",
    "Calls": f"{BASE_URL}/calls",
}

all_dataframes = {}

# --- Fetch all data first ---
for label, url in ENDPOINTS.items():
    try:
        response = requests.get(url)
        data = response.json()
        df = pd.DataFrame(data)
        all_dataframes[label] = df
    except Exception as e:
        st.error(f"Failed to fetch {label}: {e}")
        all_dataframes[label] = pd.DataFrame()

# --- Show counts at top ---
st.subheader("📦 Lead Category Counts")
count_cols = st.columns(len(ENDPOINTS))
for i, (label, df) in enumerate(all_dataframes.items()):
    with count_cols[i]:
        st.metric(label, len(df))

# --- Show expanders for each dataframe ---
st.subheader("🗃 Data Views")
for label, df in all_dataframes.items():
    with st.expander(f"View {label} DataFrame — {len(df)} records"):
        st.dataframe(df, use_container_width=True)

# --- Reply Rate Chart ---
if "Outgoing" in all_dataframes and "Replied" in all_dataframes:
    outgoing_count = len(all_dataframes["Outgoing"])
    replied_count = len(all_dataframes["Replied"])

    st.subheader("📬 Reply Rate")

    reply_df = pd.DataFrame({
        "Type": ["Outgoing", "Replied"],
        "Count": [outgoing_count, replied_count]
    })

    fig_reply = px.pie(reply_df, values="Count", names="Type", title="Reply Rate")
    st.plotly_chart(fig_reply, use_container_width=True)

# --- Time-based Email Activity Chart ---
st.subheader("⏰ Email Activity Timeline (based on `last email`)")

timestamps = []
for label, df in all_dataframes.items():
    if "last email" in df.columns:
        try:
            parsed_times = pd.to_datetime(df["last email"], utc=True, errors='coerce')
            timestamps.extend(parsed_times.dropna())
        except Exception:
            pass

if timestamps:
    time_df = pd.DataFrame(timestamps, columns=["Timestamp"])
    time_df["Time (Hour)"] = time_df["Timestamp"].dt.strftime('%Y-%m-%d %H:00')

    hourly_counts = time_df.groupby("Time (Hour)").size().reset_index(name="Emails")

    fig_time = px.bar(
        hourly_counts,
        x="Time (Hour)",
        y="Emails",
        title="Email Activity by Hour (UTC)",
        labels={"Emails": "Count", "Time (Hour)": "Hour"},
    )
    fig_time.update_xaxes(tickangle=45)
    st.plotly_chart(fig_time, use_container_width=True)
else:
    st.info("No valid `last email` timestamps found in any dataset.")
