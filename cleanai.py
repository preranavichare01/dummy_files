import os
import pandas as pd
import requests
from dotenv import load_dotenv
import streamlit as st
import re

# Load environment variables
load_dotenv()

# === Hugging Face Inference API Wrapper ===
class HuggingFaceLLM:
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.api_url = f"https://api-inference.huggingface.co/models/{model_id}"
        self.headers = {
            "Authorization": f"Bearer {os.getenv('HF_API_KEY')}",
            "Content-Type": "application/json"
        }

    def generate_response(self, message: str) -> str:
        payload = {
            "inputs": message,
            "parameters": {
                "temperature": 0.2,
                "max_new_tokens": 512,
                "do_sample": True
            }
        }
        response = requests.post(self.api_url, headers=self.headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result[0]['generated_text'].strip()

# === Improved Data Cleaning ===
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df.replace(["null", "None", "NaN", ""], pd.NA, inplace=True)
    df.drop_duplicates(inplace=True)

    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            if "id" in col.lower() or "index" in col.lower():
                df[col].fillna("Unknown", inplace=True)
            else:
                if df[col].skew() > 1:
                    df[col].fillna(df[col].median(), inplace=True)
                else:
                    df[col].fillna(df[col].mean(), inplace=True)
        elif pd.api.types.is_categorical_dtype(df[col]) or df[col].dtype == object:
            df[col].fillna("Unknown", inplace=True)
            # Remove unwanted characters
            df[col] = df[col].astype(str).apply(lambda x: re.sub(r'[^\w\s]', '', x))
        else:
            df[col].fillna(method='ffill', inplace=True)

    return df

# === Hugging Face-enhanced agentic cleaner ===
def agentic_clean(file) -> pd.DataFrame:
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
        else:
            raise ValueError("Unsupported file type")

        sample_data = df.head().to_csv(index=False)
        summary = f"Column types:\n{df.dtypes.to_string()}\nMissing values:\n{df.isnull().sum().to_string()}"

        # Use Hugging Face LLM to generate response for cleaning task
        hf_message = (
            f"You are a data cleaning assistant. Here's a preview of the user's dataset:\n"
            f"{sample_data}\n\n{summary}\n"
            f"Auto-fill missing values per column, clean dirty characters, and remove duplicates. "
            f"Confirm your understanding."
        )

        hf_llm = HuggingFaceLLM(model_id="HuggingFaceH4/zephyr-7b-beta")  
        hf_reply = hf_llm.generate_response(hf_message)
        print("HF LLM response:", hf_reply)

        # Proceed with local cleaning if LLM suggests so
        cleaned_df = clean_data(df)
        return cleaned_df

    except Exception as e:
        print(f"Agentic cleaner failed: {e}")
        return pd.DataFrame()

# === Streamlit Interface ===
st.set_page_config(page_title="Agentic Cleaner", layout="centered")
st.title("🧠 Agentic AI - CSV/Excel Cleaner")

uploaded_file = st.file_uploader("📤 Upload your CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file:
    st.success("✅ File uploaded successfully!")

    if st.button("🚀 Clean with Agent"):
        try:
            with st.spinner("Cleaning your file..."):
                cleaned_df = agentic_clean(uploaded_file)

            if cleaned_df.empty:
                st.error("⚠️ The cleaning agent failed or returned no data.")
            else:
                st.success("✅ Cleaning complete!")
                st.dataframe(cleaned_df.head(10))

                csv_data = cleaned_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Download Cleaned CSV",
                    data=csv_data,
                    file_name="cleaned_data.csv",
                    mime='text/csv'
                )
        except Exception as e:
            st.error(f"Agent failed: {e}")






