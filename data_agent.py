import pandas as pd
from langchain_nvidia_ai_endpoints import ChatNVIDIA
import re

# Initialize NVIDIA LLM client
agent = ChatNVIDIA(
    model="mistralai/mistral-small-24b-instruct",
    api_key="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",  # Replace with your NVIDIA API key
    temperature=0.2,
    top_p=0.7,
    max_tokens=2048
)

def ask_agent(prompt: str) -> str:
    """Sends prompt to the NVIDIA model and streams response."""
    response = ""
    for chunk in agent.stream([{"role": "user", "content": prompt}]):
        print(chunk.content, end="")  # Show agent thoughts in terminal
        response += chunk.content
    return response

def process_with_agent(df: pd.DataFrame) -> pd.DataFrame:
    """Sends a data sample to LLM and applies the cleaning instructions."""
    sample_data = df.head(5).to_csv(index=False)

    prompt = f"""
You are a data preprocessing agent.
Clean the dataset below using Python and pandas with the following rules:

1. Detect column types automatically.
2. For missing values:
   - If column is numeric, fill with mean or median (choose appropriately).
   - If column is text, fill with 'unknown'.
3. Remove duplicate rows.
4. Remove special characters from string columns (like $#@&*).
5. Do NOT drop any columns.
6. Only return clean Python code starting from 'df =', no markdown or explanations.

Sample Data:
{sample_data}

Only output the cleaned code block, no markdown or description.
"""

    agent_code = ask_agent(prompt)

    print("\n\n[🔧 Agent Generated Code Start]")
    print(agent_code)
    print("[🔧 Agent Generated Code End]\n\n")

    # Clean formatting: remove backticks or markdown
    agent_code = agent_code.replace("```python", "").replace("```", "").strip()

    # Prepare scope and execute safely
    local_df = df.copy()
    local_vars = {"df": local_df, "pd": pd, "re": re}

    try:
        exec(agent_code, {"pd": pd, "re": re}, local_vars)
        cleaned_df = local_vars["df"]
    except Exception as e:
        print("\n[❌ ERROR executing agent code]:", e)
        print("\n[⚠️ Fallback to original DataFrame returned.]")
        cleaned_df = local_df  # Fallback to original DataFrame in case of failure

    return cleaned_df

def save_cleaned_file(df: pd.DataFrame, original_file_path: str) -> None:
    """Save the entire cleaned dataset back to the original file format."""
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
