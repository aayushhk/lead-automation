import streamlit as st
import requests
from io import BytesIO

# -----------------------------
# Page Setup
# -----------------------------
st.set_page_config(
    page_title="Trigger Webhook",
    page_icon="📤",
    layout="wide",
    initial_sidebar_state="expanded"
)


# -----------------------------
# Main Page
# -----------------------------
st.title("📤 Upload Binary File")
st.markdown(
    """
    Use this tool to upload a binary file and trigger the **n8n webhook**.  
    The file will be sent as part of a `multipart/form-data` POST request.
    """
)

# -----------------------------
# File Upload
# -----------------------------
uploaded_file = st.file_uploader(
    label="Select a binary file",
    type=None,
    help="Upload any file (CSV, image, ZIP, etc.) to trigger the n8n webhook."
)

# -----------------------------
# Upload Trigger
# -----------------------------
def send_file_to_webhook(file_bytes: bytes, filename: str):
    url = "https://bizmaxus.app.n8n.cloud/webhook/csv"
    files = {"data": (filename, BytesIO(file_bytes), "application/octet-stream")}
    try:
        response = requests.post(url, files=files, timeout=15)
        response.raise_for_status()
        return True, response.text
    except requests.exceptions.RequestException as e:
        return False, str(e)

# -----------------------------
# Trigger Button
# -----------------------------
if uploaded_file:
    st.info(f"File ready: **{uploaded_file.name}** ({uploaded_file.size} bytes)")
    if st.button("🚀 Send to Webhook"):
        with st.spinner("Sending file to webhook..."):
            success, result = send_file_to_webhook(uploaded_file.read(), uploaded_file.name)
        if success:
            st.success("✅ File sent successfully!")
            st.code(result, language='json')
        else:
            st.error("❌ Upload failed!")
            st.text(result)
else:
    st.warning("👈 Please select a file to continue.")

# -----------------------------
# Footer
# -----------------------------
st.markdown("---")
st.caption("© 2025 BizMaxus • Built with Streamlit")
