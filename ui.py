import streamlit as st
import pandas as pd
from io import StringIO
from agent import process_with_agent, save_cleaned_file  # Import agent functions

# Function to handle file upload, processing, and downloading
def handle_file_upload(file):
    file_type = file.type
    file_path = file.name
    if file_type == "text/csv":
        df = pd.read_csv(file)
    elif file_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        df = pd.read_excel(file)
    elif file_type == "application/json":
        df = pd.read_json(file)
    else:
        st.error("Unsupported file type.")
        return

    # Display the first 5 rows of the uploaded file
    st.write("Preview of the uploaded file:")
    st.write(df.head())

    # Process the file using the agent
    cleaned_df = process_with_agent(df)

    # Display a preview of the cleaned data (first 5 rows)
    st.write("Preview of the cleaned data:")
    st.write(cleaned_df.head())

    # Save and allow download of the cleaned file
    output_file = "cleaned_" + file_path
    save_cleaned_file(cleaned_df, output_file)

    # Allow the user to download the cleaned file
    with open(output_file, "rb") as f:
        st.download_button("Download Cleaned File", f, file_name=output_file)

# Streamlit UI
st.title("Data Cleaning and Preprocessing Agent")
uploaded_file = st.file_uploader("Upload your CSV, Excel, or JSON file", type=["csv", "xlsx", "json"])

if uploaded_file:
    handle_file_upload(uploaded_file)
