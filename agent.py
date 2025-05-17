import pandas as pd
import re
from langchain_nvidia_ai_endpoints import ChatNVIDIA

# Setup LLM
agent = ChatNVIDIA(
    model="mistralai/mistral-small-24b-instruct",
    api_key="YOUR_API_KEY_HERE",  # Replace with actual
    temperature=0.2,
    top_p=0.7,
    max_tokens=2048
)

def ask_agent(prompt: str) -> str:
    response = ""
    try:
        for chunk in agent.stream([{"role": "user", "content": prompt}]):
            response += chunk.content
        if not response.strip():
            raise ValueError("Empty response from agent")
    except Exception as e:
        print(f"[❌ Agent API Error]: {e}")
        response = ""
    return response

# --- Advanced Cleaner Using Agent ---
def process_with_agent(df: pd.DataFrame) -> pd.DataFrame:
    sample_data = df.head(5).to_csv(index=False)

    prompt = f"""
You are a Python data cleaning expert. Clean the following pandas DataFrame `df`.

Rules:
1. Preserve all column names and types.
2. For missing values:
   - Fill numeric with mean.
   - Fill text/date columns with "unknown".
3. Remove duplicate rows.
4. Do NOT remove underscores (_) in JOB_ID.
5. Keep @ and . in EMAIL fields.
6. Clean PHONE_NUMBER: retain only digits, format as XXX-XXX-XXXX if 10 digits.
7. Do not drop any columns.
8. Preserve all rows.
9. Remove leading/trailing whitespaces.
10. Keep all date strings as-is.

Data:
{sample_data}

Only return Python code starting with `df = ...`
"""

    agent_code = ask_agent(prompt)
    print("[🔧 Generated Code]:\n", agent_code)

    if not agent_code:
        print("⚠️ No response from agent. Applying fallback.")
        return basic_data_cleaning(df)

    agent_code = agent_code.replace("```python", "").replace("```", "").strip()

    local_df = df.copy()
    local_vars = {"df": local_df, "pd": pd, "re": re}

    try:
        exec(agent_code, {"pd": pd, "re": re}, local_vars)
        cleaned_df = local_vars["df"]
    except Exception as e:
        print("[❌ Error executing agent code]:", e)
        cleaned_df = basic_data_cleaning(df)

    return cleaned_df

# --- Backup cleaner ---
def basic_data_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.columns:
        if df[col].dtype in ['float64', 'int64']:
            df[col].fillna(df[col].mean(), inplace=True)
        else:
            df[col].fillna("unknown", inplace=True)
            if col.lower() == 'email':
                continue
            if col.lower() == 'job_id':
                df[col] = df[col].astype(str).str.strip()
            elif col.lower() == 'phone_number':
                df[col] = df[col].apply(lambda x: clean_phone_number(str(x)))
            else:
                df[col] = df[col].astype(str).apply(lambda x: re.sub(r'[^\w\s@.-]', '', x))
                df[col] = df[col].str.strip()

    df.drop_duplicates(inplace=True)
    return df

# --- Phone Number Formatter ---
def clean_phone_number(phone: str) -> str:
    digits = re.sub(r'\D', '', phone)
    if len(digits) == 10:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    return digits if digits else "unknown"

# --- Save Output ---
def save_cleaned_file(df: pd.DataFrame, original_file_path: str) -> None:
    ext = original_file_path.split('.')[-1].lower()
    try:
        if ext == 'csv':
            df.to_csv(original_file_path, index=False)
        elif ext in ['xls', 'xlsx']:
            df.to_excel(original_file_path, index=False)
        elif ext == 'json':
            df.to_json(original_file_path, orient='records', lines=True)
        else:
            raise ValueError("Unsupported output format.")
        print(f"[✅ Saved]: {original_file_path}")
    except Exception as e:
        print(f"[❌ Save Failed]: {e}")
