import pandas as pd
from langchain_nvidia_ai_endpoints import ChatNVIDIA
import re

agent = ChatNVIDIA(
    model="mistralai/mistral-small-24b-instruct",
    api_key="NVIDIA API key",  # Replace with your NVIDIA API key
    temperature=0.2,
    top_p=0.7,
    max_tokens=2048
)

def ask_agent(prompt: str) -> str:
    response = ""
    for chunk in agent.stream([{"role": "user", "content": prompt}]):
        print(chunk.content, end="")
        response += chunk.content
    return response

def process_with_agent(df: pd.DataFrame) -> pd.DataFrame:
    sample_data = df.head(5).to_csv(index=False)

    prompt = f"""
You are a data preprocessing agent.
A full pandas DataFrame called 'df' is already loaded in memory.

Clean this dataset using the following rules:
1. Detect column types automatically.
2. For missing values:
   - If column is numeric, fill with mean or median (choose appropriately).
   - If column is text, fill with 'unknown'.
3. Remove duplicate rows.
4. Remove special characters from string columns (like $#@&*).
5. Do NOT drop any columns.
6. Only output working Python code that modifies the existing 'df' — do not read from or write to any files.
7. Your output must start with 'df =' and must return the fully cleaned DataFrame.

Here is a sample of the data to help you infer the column types:
{sample_data}

Only output valid Python code (no markdown, no extra explanation).
"""

    agent_code = ask_agent(prompt)
    print("\n\n[🔧 Agent Generated Code Start]")
    print(agent_code)
    print("[🔧 Agent Generated Code End]\n\n")

    # Clean formatting
    agent_code = agent_code.replace("```python", "").replace("```", "").strip()

    local_df = df.copy()
    local_vars = {"df": local_df, "pd": pd, "re": re}

    try:
        exec(agent_code, {"pd": pd, "re": re}, local_vars)
        cleaned_df = local_vars["df"]
    except Exception as e:
        print("\n[❌ ERROR executing agent code]:", e)
        print("\n[⚠️ Fallback to original DataFrame returned.]")
        cleaned_df = local_df

    return cleaned_df

def save_cleaned_file(df: pd.DataFrame, original_file_path: str) -> None:
    file_extension = original_file_path.split('.')[-1].lower()

    if file_extension == 'csv':
        df.to_csv(original_file_path, index=False)
    elif file_extension in ['xls', 'xlsx']:
        df.to_excel(original_file_path, index=False)
    elif file_extension == 'json':
        df.to_json(original_file_path, orient='records', lines=True)
    else:
        raise ValueError("Unsupported file format.")

    print(f"File saved as {original_file_path}")
