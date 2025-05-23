# main.py

import os
import re
import argparse
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from typing import Dict

#
# 1) Load configuration from .env
#
load_dotenv()
CLEANING_KEY       = os.getenv("NVIDIA_CLEANING_KEY")
QC_KEY             = os.getenv("NVIDIA_QC_KEY")
FEASIBILITY_KEY    = os.getenv("NVIDIA_FEASIBILITY_KEY")
BASE_URL           = os.getenv("OPENAI_BASE_URL", "https://integrate.api.nvidia.com/v1")
DEFAULT_INPUT_DIR  = os.getenv("DATASET_FOLDER", "test")
DEFAULT_OUTPUT_DIR = os.getenv("OUTPUT_FOLDER", "cleaned")


#
# 2) FEASIBILITY CHECKER (Code 1)
#
feas_client = OpenAI(base_url=BASE_URL, api_key=FEASIBILITY_KEY)

def describe_table(name: str, df: pd.DataFrame) -> str:
    schema = ", ".join(f"{c}({t})" for c, t in zip(df.columns, df.dtypes))
    sample = df.head(3).to_dict(orient="records")
    return f"Table: {name}\nSchema: {schema}\nSample: {sample}\n"

def load_tables_from_folder(folder: str) -> Dict[str, pd.DataFrame]:
    dfs = {}
    for fn in os.listdir(folder):
        path = os.path.join(folder, fn)
        try:
            if fn.endswith((".xls", ".xlsx")):
                xls = pd.ExcelFile(path)
                for s in xls.sheet_names:
                    dfs[f"{fn}:{s}"] = xls.parse(s)
            elif fn.endswith((".csv", ".tsv")):
                try:
                    dfs[fn] = pd.read_csv(path, encoding="utf-8")
                except UnicodeDecodeError:
                    dfs[fn] = pd.read_csv(path, encoding="ISO-8859-1")
            elif fn.endswith(".json"):
                dfs[fn] = pd.read_json(path)
        except Exception as e:
            print(f"[Load error] {fn}: {e}")
    return dfs

def analyze_table_relationships(dfs: Dict[str, pd.DataFrame]):
    prompt = (
        "You are a data analysis assistant. Only reply TRUE if all tables "
        "are semantically connected so they can be jointly processed; "
        "else reply FALSE.\n\n"
    )
    for name, df in dfs.items():
        prompt += describe_table(name, df) + "\n"

    resp_stream = feas_client.chat.completions.create(
        model="deepseek-ai/deepseek-r1",
        messages=[
            {"role": "system", "content": "You are a helpful data analysis assistant."},
            {"role": "user",   "content": prompt}
        ],
        temperature=0.6,
        top_p=0.7,
        max_tokens=512,
        stream=True
    )

    result = ""
    for chunk in resp_stream:
        content = chunk.choices[0].delta.content
        if content:
            print(content, end="")
            result += content
    print()
    # return result.strip().lower().startswith("true")
    return result

def run_feasibility(input_dir: str) -> bool:
    print(f"⏳ Loading files from {input_dir} …")
    tables = load_tables_from_folder(input_dir)
    print(f"⚙️  Loaded {len(tables)} tables")
    if not tables:
        print("✋ No tables found; aborting feasibility check.")
        return False

    print("🔍 Running semantic connectivity check …")
    try:
        ok = analyze_table_relationships(tables)
        print(f"✅ Feasibility: {ok}")
        return ok
    except Exception as e:
        print(f"❌ Feasibility check failed: {e}")
        return False


#
# 3) CLEANING & QC (Code 2)
#
""" cleaning_agent = ChatNVIDIA(
    model="mistralai/mistral-small-24b-instruct",
    api_key=CLEANING_KEY,
    temperature=0.2,
    top_p=0.7,
    max_tokens=2048
) """
cleaning_agent = ChatNVIDIA(
    model="mistralai/mistral-small-24b-instruct",
    api_key=CLEANING_KEY,
    temperature=0.2,
    top_p=0.7,
    max_tokens=2048
)


#qc_client = OpenAI(base_url=BASE_URL, api_key=QC_KEY)
#qc_client = OpenAI(base_url=BASE_URL, api_key=FEASIBILITY_KEY)


def ask_cleaning_agent(prompt: str) -> str:
    out = ""
    try:
        for chunk in cleaning_agent.stream([{"role": "user", "content": prompt}]):
            out += chunk.content
        if not out.strip():
            raise ValueError("empty")
    except Exception as e:
        print(f"[Cleaning Agent Error] {e}")
        return ""
    return out

def clean_phone_number(phone: str) -> str:
    d = re.sub(r"\D", "", phone)
    if len(d) == 10:
        return f"{d[:3]}-{d[3:6]}-{d[6:]}"
    return d or "unknown"

def basic_data_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col].fillna(df[col].mean(), inplace=True)
        else:
            df[col].fillna("unknown", inplace=True)
            lc = col.lower()
            if lc == "email":
                pass
            elif lc == "job_id":
                df[col] = df[col].astype(str).str.strip()
            elif lc == "phone_number":
                df[col] = df[col].astype(str).apply(clean_phone_number)
            else:
                df[col] = (
                    df[col]
                    .astype(str)
                    .apply(lambda x: re.sub(r"[^\w\s@.-]", "", x))
                    .str.strip()
                )
    return df.drop_duplicates()

def process_with_agent(df: pd.DataFrame) -> pd.DataFrame:
    sample = df.head(5).to_csv(index=False)
    prompt = f"""
You are a Python data cleaning expert. Clean the pandas DataFrame df according to:
1. Preserve col types.
2. Fill numeric NaNs with mean; others with "unknown".
3. Remove duplicates.
4. Keep underscores in JOB_ID.
5. Keep '@' and '.' in EMAIL.
6. Format PHONE_NUMBER digits only, XXX-XXX-XXXX.
7. Do not drop rows or cols.
8. Strip whitespace.
9. Keep date strings.

Data sample:
{sample}

Return only Python lines mutating df. No imports/explanation.
"""
    code = ask_cleaning_agent(prompt)
    if not code:
        print("⚠️ using fallback cleaner")
        return basic_data_cleaning(df)
    code = re.sub(r"```.*?```", "", code, flags=re.DOTALL).strip()
    env = {"df": df.copy(), "pd": pd, "re": re, "np": np}
    try:
        exec(code, env)
        return env["df"]
    except Exception as e:
        print(f"[Exec error]: {e}; fallback cleaner")
        return basic_data_cleaning(df)

def quality_check(df: pd.DataFrame) -> (bool, str):
    csv = df.to_csv(index=False)
    prompt = f"""
You are a data quality checker. Examine this CSV and report:
- Usability?
- Data loss?
- Missing/null/malformed?
- Required cols present?

Data:
{csv}

Return: GOOD or BAD plus one‐paragraph explanation.
"""
    try:
        """ res = qc_client.chat.completions.create(
            model="mistralai/mistral-small-24b-instruct",
            messages=[
                {"role":"system","content":"You are a strict data quality checker."},
                {"role":"user","content":prompt}
            ],
            temperature=0.6,
            top_p=0.95,
            max_tokens=512
        ) """

        res = feas_client.chat.completions.create(
            model="deepseek-ai/deepseek-r1",
            messages=[
                {"role": "system", "content": "You are a helpful data analysis assistant."},
                {"role": "user",   "content": prompt}
            ],
            temperature=0.6,
            top_p=0.7,
            max_tokens=512,
            #stream=True
        )

        ans = res.choices[0].message.content
        print("[QC] ", ans)
        return ans.lower().startswith("good"), ans
    except Exception as e:
        print(f"[QC Error] {e}")
        return False, f"QC failed: {e}"

def process_file(path: str, out_dir: str) -> (str, bool):
    fn = os.path.basename(path)
    try:
        if fn.endswith(".csv"):
            df = pd.read_csv(path)
        elif fn.endswith((".xls", ".xlsx")):
            df = pd.read_excel(path)
        elif fn.endswith(".json"):
            df = pd.read_json(path)
        else:
            raise ValueError("unsupported format")
        df_clean = process_with_agent(df)
        ok, _ = quality_check(df_clean)
        out_path = os.path.join(out_dir, f"cleaned_{fn}")
        df_clean.to_csv(out_path, index=False)
        return out_path, ok
    except Exception as e:
        print(f"[Error] {fn}: {e}")
        return "", False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir",  default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    if not run_feasibility(args.input_dir):
        print("✋ stopping; data not feasible.")
        return

    os.makedirs(args.output_dir, exist_ok=True)
    for fn in os.listdir(args.input_dir):
        src = os.path.join(args.input_dir, fn)
        if (not os.path.isfile(src)
            or not fn.lower().endswith((".csv", ".xls", ".xlsx", ".json"))):
            continue
        print(f"\n▶️  Processing {fn}")
        out, ok = process_file(src, args.output_dir)
        print(f"✔️  Saved to {out}")
        # print(f"✔️  Saved to {out}; QC verdict={'GOOD' if ok else 'BAD'}")

if __name__ == "__main__":
    main()
