import os
import pandas as pd
import requests
import re
from dotenv import load_dotenv
import streamlit as st

# Load .env and API key
load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")

# Hugging Face Inference API Wrapper
class HuggingFaceLLM:
    def __init__(self, model_id: str):
        self.api_url = f"https://api-inference.huggingface.co/models/{model_id}"
        self.headers = {
            "Authorization": f"Bearer {HF_API_KEY}",
            "Content-Type": "application/json"
        }

    def generate_code(self, sample_df: pd.DataFrame) -> str:
        preview = sample_df.head(10).to_csv(index=False)
        schema = sample_df.dtypes.to_string()
        nulls = sample_df.isnull().sum().to_string()

        prompt = f"""
You are a Python data cleaning expert.
Below is a sample CSV preview of the dataset:
{preview}

Schema:
{schema}

Null values:
{nulls}

Write only valid Python Pandas code to:
- Drop duplicates
- Handle missing values appropriately
- Clean special characters from text fields
- Ensure the result is in a DataFrame called 'df'
- Do NOT include numbers with leading zeros
- Do NOT include markdown, comments, or explanations
Only output the code.
"""

        payload = {
            "inputs": prompt,
            "parameters": {
                "temperature": 0.1,
                "max_new_tokens": 512
            }
        }

        response = requests.post(self.api_url, headers=self.headers, json=payload)
        response.raise_for_status()
        result = response.json()

        if isinstance(result, list) and 'generated_text' in result[0]:
            return result[0]['generated_text']
        elif isinstance(result, dict) and 'generated_text' in result:
            return result['generated_text']
        else:
            raise ValueError("Unexpected response format from Hugging Face model")

# Fix leading zeros in integers
def remove_leading_zeros(code: str) -> str:
    pattern = re.compile(r'\b0+([1-9]\d*)\b')  # Matches integers like 0012 or 012
    return pattern.sub(r'\1', code)

# Cleaning Function
def agentic_clean_with_code(file) -> pd.DataFrame:
    try:
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        elif file.name.endswith((".xls", ".xlsx")):
            df = pd.read_excel(file)
        else:
            raise ValueError("Unsupported file type")

        hf_llm = HuggingFaceLLM(model_id="mistralai/Mistral-7B-Instruct-v0.1")
        cleaning_code = hf_llm.generate_code(df)

        # Fix leading zero syntax issues
        cleaning_code = remove_leading_zeros(cleaning_code)

        st.code(cleaning_code, language="python")

        # Safe execution
        local_env = {"df": df.copy()}
        try:
            compile(cleaning_code, "<string>", "exec")
            exec(cleaning_code, {}, local_env)
            cleaned_df = local_env["df"]
        except SyntaxError as se:
            st.error(f"❌ Syntax Error in LLM-generated code:\n{se}")
            return pd.DataFrame()
        except Exception as e:
            st.error(f"❌ Error executing LLM code:\n{e}")
            return pd.DataFrame()

        return cleaned_df

    except Exception as e:
        st.error(f"Agent failed: {e}")
        return pd.DataFrame()

# Streamlit UI
st.set_page_config(page_title="🔧 Fully Automated Agentic Cleaner", layout="centered")
st.title("🤖 Agentic AI: Fully Automated Data Cleaner")

uploaded_file = st.file_uploader("📤 Upload your CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file:
    st.success("✅ File uploaded!")

    if st.button("🚀 Clean Automatically"):
        with st.spinner("Agent is thinking..."):
            cleaned_df = agentic_clean_with_code(uploaded_file)

        if not cleaned_df.empty:
            st.success("✅ Cleaned successfully!")
            st.dataframe(cleaned_df.head(10))

            csv = cleaned_df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Cleaned CSV", csv, "cleaned_data.csv", "text/csv")
