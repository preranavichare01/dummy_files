import os
import pandas as pd
import re
import streamlit as st
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# Load API key
load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")

# Hugging Face Wrapper
class HuggingFaceLLM:
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.client = InferenceClient(model=model_id, token=HF_API_KEY)

    def generate_cleaning_code(self, df: pd.DataFrame) -> str:
        preview = df.head(10).to_csv(index=False)
        schema = df.dtypes.to_string()
        nulls = df.isnull().sum().to_string()

        prompt = f"""
You are a Python data cleaning expert.
Below is a sample CSV preview of the dataset:
{preview}

Schema:
{schema}

Null values:
{nulls}

Write valid Python Pandas code to:
- Drop duplicates
- Fill missing values (use mean for numeric, mode or empty string for categorical)
- Remove special characters from text columns
- Assign the result to the same variable 'df'

Important rules:
- Do NOT include markdown formatting (no ```python or ```).
- Do NOT use axis=0 in fillna with a dictionary.
- Return only clean executable Python code without comments.
"""
        result = self.client.text_generation(prompt, max_new_tokens=512, temperature=0.1)
        return result.strip()

def remove_leading_zeros(code: str) -> str:
    return re.sub(r'\b0+([1-9]\d*)\b', r'\1', code)

def agentic_clean_with_code(file) -> pd.DataFrame:
    try:
        df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
        print("[INFO] File loaded. Sending preview to LLM...")

        llm = HuggingFaceLLM("mistralai/Mistral-7B-Instruct-v0.3")
        code = llm.generate_cleaning_code(df)
        code = remove_leading_zeros(code)
        code = code.replace("```python", "").replace("```", "").strip()  # Remove markdown if present
        print("[LLM] Generated Code:\n", code)

        local_env = {"df": df.copy()}
        exec(code, {}, local_env)
        result_df = local_env.get("df", pd.DataFrame())

        if not isinstance(result_df, pd.DataFrame):
            raise ValueError("LLM code did not return a valid DataFrame.")

        print("[INFO] Cleaning successful.")
        return result_df

    except Exception as e:
        print(f"[ERROR] LLM cleaning failed: {e}")
        return pd.DataFrame()

# Streamlit UI
st.set_page_config(page_title="Agentic Cleaner", layout="centered")
st.title("🧠 Agentic Cleaner - Auto Data Cleaning with AI")

uploaded_file = st.file_uploader("📤 Upload CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file:
    cleaned_df = agentic_clean_with_code(uploaded_file)

    if not cleaned_df.empty:
        st.success("✅ Preview of Cleaned Data")
        st.dataframe(cleaned_df.head(10))

        csv = cleaned_df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Cleaned CSV", csv, "cleaned_data.csv", "text/csv")
    else:
        st.error("❌ Failed to clean the file. Please try again.")
