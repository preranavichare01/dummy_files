import pandas as pd
import os

class DataAgent:
    def process(self, file_path: str, command: str):
        ext = os.path.splitext(file_path)[1]

        try:
            if ext == ".csv":
                df = pd.read_csv(file_path)
            elif ext in [".xls", ".xlsx"]:
                df = pd.read_excel(file_path)
            else:
                return {"error": "Unsupported file format"}

            if "clean" in command.lower():
                df = df.dropna()

            return {
                "message": "Data processed successfully!",
                "rows": len(df),
                "columns": len(df.columns),
                "command_used": command
            }

        except Exception as e:
            return {"error": str(e)}
