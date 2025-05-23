import os
import pandas as pd

def process_file(path: str, out_dir: str) -> (str, bool):
    fn = os.path.basename(path)
    try:
        # Read file based on extension
        if fn.endswith(".csv"):
            df = pd.read_csv(path)
        elif fn.endswith((".xls", ".xlsx")):
            df = pd.read_excel(path, engine='openpyxl')  # safer
        elif fn.endswith(".json"):
            df = pd.read_json(path)
        else:
            raise ValueError("Unsupported format")

        # Clean the data
        df_clean = process_with_agent(df)

        # Run quality check
        ok, _ = quality_check(df_clean)

        # Output path with same format
        out_path = os.path.join(out_dir, f"cleaned_{fn}")

        # Save in same format
        if fn.endswith(".csv"):
            df_clean.to_csv(out_path, index=False)
        elif fn.endswith((".xls", ".xlsx")):
            df_clean.to_excel(out_path, index=False, engine='openpyxl')
        elif fn.endswith(".json"):
            df_clean.to_json(out_path, orient="records", lines=False)

        return out_path, ok

    except Exception as e:
        print(f"[Error] {fn}: {e}")
        return "", False
