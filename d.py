from openai import OpenAI
import os
import pandas as pd
from typing import Dict
from openai import OpenAI
 
# ==== CONFIG ====
DATASET_FOLDER = "test"
NVIDIA_API_KEY = "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"
NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1"
MODEL="nvidia/llama-3.1-nemotron-ultra-253b-v1"
# ================
 
client = OpenAI(
    base_url=NVIDIA_API_URL,
    api_key=NVIDIA_API_KEY
)
 
def describe_table(name: str, df: pd.DataFrame) -> str:
    schema = ", ".join([f"{col} ({dtype})" for col, dtype in zip(df.columns, df.dtypes)])
    sample = df.head(3).to_dict(orient="records")
    return f"Table: {name}\nSchema: {schema}\nSample: {sample}\n"
 
def analyze_table_relationships(dataframes: Dict[str, pd.DataFrame]) -> None:
    prompt = (
        """ You are a data analysis assistant. Based on the following table schemas and samples, identify:
        - If there is just one non empty table directly return True
        - Tables that are unrelated
        - How the remaining tables are connected logically
        Only response you give must be True or False.
        Give True if two or more tables are connected if none of the tables have any connection with any other table only then give False.
        Give no other response like instructions or acknowledgement only give this single result.
        DO NOT reveal your reasoning.
        """
    )
 
    for name, df in dataframes.items():
        prompt += describe_table(name, df) + "\n"
 
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful data analysis assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.6,
        top_p=0.7,
        max_tokens=4096,
        stream=True
    )
 
    print("\n--- Model result ---\n")
    for chunk in completion:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="")
 
def load_tables_from_folder(folder_path: str) -> Dict[str, pd.DataFrame]:
    dataframes = {}
    for filename in os.listdir(folder_path):
        path = os.path.join(folder_path, filename)
        try:
            if filename.endswith((".xls", ".xlsx")):
                xls = pd.ExcelFile(path)
                for sheet in xls.sheet_names:
                    df = xls.parse(sheet)
                    key = f"{filename}:{sheet}"
                    dataframes[key] = df
            elif filename.endswith((".csv", ".tsv")):
                try:
                    df = pd.read_csv(path, encoding='utf-8')
                except UnicodeDecodeError:
                    df = pd.read_csv(path, encoding='ISO-8859-1')
                key = filename
                dataframes[key] = df
        except Exception as e:
            print(f"Error loading {filename}: {e}")
    return dataframes
 
def main():
    print(f"Loading files from: {DATASET_FOLDER}")
    tables = load_tables_from_folder(DATASET_FOLDER)
    print(f"Loaded {len(tables)} tables.")
 
    print("Checking semantic connectivity...")
    analyze_table_relationships(tables)
 
if __name__ == "__main__":
    main()
 
