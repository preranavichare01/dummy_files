import os
import re
import pandas as pd

def process_file(fn, out_dir):
    # Read the input file
    df = pd.read_csv(fn)

    # Clean up the data (replace this with your actual cleaning logic)
    df_clean = df.dropna()

    # Sanitize filename for Excel compatibility
    safe_fn = re.sub(r'[\\/*?:"<>|]', "_", os.path.basename(fn))
    out_path = os.path.join(out_dir, f"cleaned_{os.path.splitext(safe_fn)[0]}.xlsx")

    # Save as Excel with openpyxl engine
    df_clean.to_excel(out_path, index=False, engine='openpyxl')
