def process_file(path: str, out_dir: str) -> (str, bool):
    fn = os.path.basename(path)
    name, ext = os.path.splitext(fn)
    ext = ext.lower()
    try:
        if ext == ".csv":
            df = pd.read_csv(path)
        elif ext in [".xls", ".xlsx"]:
            df = pd.read_excel(path)
        elif ext == ".json":
            df = pd.read_json(path)
        else:
            raise ValueError("Unsupported file format")

        df_clean = process_with_agent(df)
        ok, _ = quality_check(df_clean)

        # Choose output format matching input
        out_path = os.path.join(out_dir, f"{name}_cleaned{ext}")
        if ext == ".csv":
            df_clean.to_csv(out_path, index=False)
        elif ext in [".xls", ".xlsx"]:
            df_clean.to_excel(out_path, index=False)
        elif ext == ".json":
            df_clean.to_json(out_path, orient="records", lines=True)
        else:
            raise ValueError("Unsupported output format")

        return out_path, ok
    except Exception as e:
        print(f"[Error] {fn}: {e}")
        return "", False
