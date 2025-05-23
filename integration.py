import os
import pandas as pd

def process_file(path: str, out_dir: str) -> (str, bool):
    fn = os.path.basename(path)
    try:
        # Read the file safely
        if fn.endswith(".csv"):
            try:
                df = pd.read_csv(path, encoding='utf-8')  # Try UTF-8 first
            except UnicodeDecodeError:
                df = pd.read_csv(path, encoding='latin1')  # Fallback if UTF-8 fails
        elif fn.endswith(".xls"):
            df = pd.read_excel(path, engine='xlrd')  # .xls uses xlrd
        elif fn.endswith(".xlsx"):
            df = pd.read_excel(path, engine='openpyxl')  # .xlsx uses openpyxl
        elif fn.endswith(".json"):
            df = pd.read_json(path)
        else:
            raise ValueError("Unsupported format")

        # Your cleaning logic
        df_clean = process_with_agent(df)

        # Your quality check logic
        ok, _ = quality_check(df_clean)

        # Set up output path
        out_path = os.path.join(out_dir, f"cleaned_{fn}")

        # Save the cleaned file based on format
        if fn.endswith(".csv"):
            df_clean.to_csv(out_path, index=False, encoding='utf-8-sig')  # utf-8-sig helps Excel read correctly
        elif fn.endswith((".xls", ".xlsx")):
            df_clean.to_excel(out_path, index=False, engine='openpyxl')
        elif fn.endswith(".json"):
            df_clean.to_json(out_path, orient="records", lines=False)

        return out_path, ok

    except Exception as e:
        print(f"[Error] {fn}: {e}")
        return "", False
