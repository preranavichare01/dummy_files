import streamlit as st
import pandas as pd
from agent import process_with_agent, save_cleaned_file  # External cleaning agent

# UI configuration
st.set_page_config(page_title="🧹 AI Data Cleaner", layout="centered")
st.title("🧹 AI Data Cleaning & Preprocessing Agent")
st.write("Upload your dataset and let the AI clean it automatically!")

# File uploader
uploaded_file = st.file_uploader("📁 Upload your CSV, Excel, or JSON file", type=["csv", "xlsx", "json"])

# File handling
def handle_file_upload(file):
    file_type = file.type
    file_name = file.name

    # Read file into DataFrame
    try:
        if file_type == "text/csv":
            df = pd.read_csv(file)
        elif file_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            df = pd.read_excel(file)
        elif file_type == "application/json":
            df = pd.read_json(file)
        else:
            st.error("❌ Unsupported file format.")
            return
    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
        return

    st.subheader("📄 Original Data Preview")
    st.dataframe(df.head())

    # Process with agent
    cleaned_df = process_with_agent(df)

    st.subheader("✅ Cleaned Data Preview")
    st.dataframe(cleaned_df.head())

    # Save and allow download
    output_file = f"cleaned_{file_name}"
    save_cleaned_file(cleaned_df, output_file)

    with open(output_file, "rb") as f:
        st.download_button("⬇️ Download Cleaned File", f, file_name=output_file)

# Trigger file processing
if uploaded_file:
    handle_file_upload(uploaded_file)
