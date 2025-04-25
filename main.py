import os
import tempfile
import pandas as pd
from dotenv import load_dotenv
from groq import Groq
import streamlit as st
import re

# Load environment variables
load_dotenv()

# === Custom Groq wrapper ===
class GroqChatLLM:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def generate_response(self, message: str) -> str:
        groq_response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": message}],
            temperature=0.2
        )
        if hasattr(groq_response, 'choices') and len(groq_response.choices) > 0:
            return groq_response.choices[0].message.content
        else:
            raise ValueError("No valid response from Groq.")

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

# === Groq-enhanced agentic cleaner ===
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

        groq_message = (
            f"You are a data cleaning assistant. Here's a preview of the user's dataset:\n"
            f"{sample_data}\n\n{summary}\n"
            f"Auto-fill missing values per column, clean dirty characters, and remove duplicates. "
            f"Confirm your understanding."
        )

        groq_llm = GroqChatLLM(model_name="llama3-70b-8192")
        groq_reply = groq_llm.generate_response(groq_message)
        print("Groq LLM response:", groq_reply)

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
