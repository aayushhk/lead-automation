import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# --- Page Config ---
st.set_page_config(page_title="Lead Dashboard", layout="wide", page_icon="📊")

st.sidebar.markdown("## 📊 Lead Dashboard")
st.sidebar.markdown("Easily monitor leads, interactions & performance.")

# --- Custom CSS for styling ---
st.markdown("""
    <style>
        .metric-card {
            padding: 15px;
            border-radius: 12px;
            background-color: #f9f9f9;
            box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
            text-align: center;
        }
        .metric-value {
            font-size: 26px;
            font-weight: bold;
            color: #2E86C1;
        }
        .metric-label {
            font-size: 14px;
            color: #555;
        }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar ---



# --- Fetch Data ---
FULL_LIST_URL = "https://bizmaxus.app.n8n.cloud/webhook/full-list"
try:
    response = requests.get(FULL_LIST_URL)
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame(data)
except Exception as e:
    st.error(f"Failed to fetch data: {e}")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.header("🔍 Filters")
mode_options = df["mode"].dropna().unique().tolist() if "mode" in df.columns else []
status_options = df["status"].dropna().unique().tolist() if "status" in df.columns else []

selected_modes = st.sidebar.multiselect("Mode", mode_options, default=mode_options)
selected_statuses = st.sidebar.multiselect("Status", status_options, default=status_options)

# --- Apply Filters ---
filtered_df = df.copy()
if "mode" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["mode"].isin(selected_modes)]
if "status" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["status"].isin(selected_statuses)]

# --- Top Metrics Row ---
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(df)}</div>
            <div class="metric-label">Total Leads</div>
        </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(filtered_df)}</div>
            <div class="metric-label">Filtered Leads</div>
        </div>
    """, unsafe_allow_html=True)
with col3:
    replied_count = filtered_df[filtered_df["status"] == "Replied"].shape[0] if "status" in filtered_df.columns else 0
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{replied_count}</div>
            <div class="metric-label">Replied</div>
        </div>
    """, unsafe_allow_html=True)

# --- Tabs for Dashboard Views ---
tab1, tab2, tab3 = st.tabs(["📄 Data Table", "📊 Charts", "⏰ Timeline"])

# --- Tab 1: Data Table ---
with tab1:
    st.dataframe(filtered_df, use_container_width=True)

# --- Tab 2: Charts ---
with tab2:
    col1, col2 = st.columns(2)

    if "mode" in filtered_df.columns:
        mode_counts = filtered_df["mode"].value_counts().reset_index()
        mode_counts.columns = ["Mode", "Count"]
        fig_mode = px.bar(mode_counts, x="Mode", y="Count", title="Lead Count by Mode", text_auto=True)
        fig_mode.update_layout(template="plotly_white")
        col1.plotly_chart(fig_mode, use_container_width=True)

    if "status" in filtered_df.columns:
        status_counts = filtered_df["status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        fig_status = px.pie(status_counts, names="Status", values="Count", title="Lead Distribution by Status")
        fig_status.update_traces(textinfo='percent+label')
        col2.plotly_chart(fig_status, use_container_width=True)

# --- Tab 3: Timeline ---
with tab3:
    if "last email" in filtered_df.columns:
        try:
            filtered_df["last email"] = pd.to_datetime(filtered_df["last email"], utc=True, errors='coerce')
            time_df = filtered_df.dropna(subset=["last email"])
            time_df["Time (Hour)"] = time_df["last email"].dt.strftime('%Y-%m-%d %H:00')
            hourly_counts = time_df.groupby("Time (Hour)").size().reset_index(name="Emails")

            fig_time = px.bar(
                hourly_counts,
                x="Time (Hour)",
                y="Emails",
                title="Email Activity by Hour (UTC)",
                labels={"Emails": "Count", "Time (Hour)": "Hour"},
            )
            fig_time.update_xaxes(tickangle=45)
            fig_time.update_layout(template="plotly_white")
            st.plotly_chart(fig_time, use_container_width=True)
        except Exception:
            st.info("No valid `last email` timestamps found.")
    else:
        st.info("No `last email` column found in dataset.")
