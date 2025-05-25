import pandas as pd
import re
from openai import OpenAI

# Initialize NVIDIA LLM API client
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="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"
)

# Ask the LLM agent
def ask_agent(prompt: str) -> str:
    try:
        completion = client.chat.completions.create(
            model="nvidia/llama-3.3-nemotron-super-49b-v1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            top_p=0.9,
            max_tokens=4096,
            stream=False
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"[❌ Agent API Error]: {e}")
        return ""

# Generate cleaning code using LLM
def generate_cleaning_code(full_df: pd.DataFrame) -> str:
    sample_data = full_df.head(5).to_csv(index=False)

    prompt = f"""
You are a Python pandas data cleaning expert.

Given a pandas DataFrame named `df` (already loaded in memory), write Python code to clean it following these rules:

1. Keep all columns and their names unchanged.
2. For numeric columns, fill missing values with the mean of that column.
3. For all object, string, or datetime-like columns (including text and dates), fill missing values with the string 'unknown'. Treat values like None, 'None', 'nan', 'NaN', NaT, and empty cells as missing.
4. Remove duplicate rows.
5. Trim leading and trailing whitespace from all string fields.
6. Remove special characters like %, $, #, etc. from all text columns except the 'EMAIL' column.
7. For the 'EMAIL' column, only trim spaces — do not modify characters.
8. For the 'PHONE_NUMBER' column or similar column name, if it exists: keep only digits; if it has 10 digits, format it as XXX-XXX-XXXX;Treat `unknown` as missing .
9. Preserve underscores in the 'JOB_ID' column, if it exists.
10. Do not drop or add any columns.
11. Keep all rows (except removed duplicates).
12. Convert all date or datetime columns to string using `astype(str)` before cleaning. Treat `unknown` as missing .
13. Always check if specific columns ('PHONE_NUMBER', 'EMAIL', 'JOB_ID') exist before processing them.
14. Use `astype(str)` to convert columns to string, not `pd.to_string()`.
15. Return only the Python code that transforms and reassigns the DataFrame `df`.
16. Do NOT include explanations or placeholder code.
17. Start the code directly with `df =` or transformations on `df`.



Sample data (first 5 rows):
{sample_data}
"""
    code = ask_agent(prompt)
    return code.replace("```python", "").replace("```", "").strip()

# Run the generated code
def process_with_agent(full_df: pd.DataFrame) -> pd.DataFrame:
    code = generate_cleaning_code(full_df)
    print("[🔧 Generated Code]:\n", code)

    if not code:
        print("⚠️ No code returned by agent. Returning original DataFrame.")
        return full_df

    try:
        local_vars = {"df": full_df.copy(), "pd": pd, "re": re}
        exec(code, {"pd": pd, "re": re}, local_vars)
        cleaned_df = local_vars["df"]
        cleaned_df.columns = cleaned_df.columns.str.strip()  # Just column name cleanup
        return cleaned_df
    except Exception as e:
        print(f"[❌ Execution Error]: {e}")
        return full_df

# Save cleaned file
def save_cleaned_file(df: pd.DataFrame, output_path: str):
    ext = output_path.split('.')[-1].lower()
    try:
        if ext == 'csv':
            df.to_csv(output_path, index=False)
        elif ext in ['xls', 'xlsx']:
            df.to_excel(output_path, index=False)
        elif ext == 'json':
            df.to_json(output_path, orient='records', lines=True)
        else:
            raise ValueError("Unsupported file format")
        print(f"[✅ File saved]: {output_path}")
    except Exception as e:
        print(f"[❌ Save Failed]: {e}")
