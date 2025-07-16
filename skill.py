import pandas as pd
from openai import OpenAI
import os

# ✅ Initialize NVIDIA/OpenAI-compatible client
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",  # Groq/Mistral-compatible endpoint
    api_key="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"  # Replace with your actual API key
)

# ✅ Extract skills from a single job description
def extract_skills_from_text(text):
    prompt = f"""
Extract only relevant skills from the following job description.
Do not include technologies like OpenAI, API details, or irrelevant text.
Return only the skills as a comma-separated list.

Job Description:
{text}
"""
    try:
        response = client.chat.completions.create(
            model="mistralai/mistral-small-24b-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("Error:", e)
        return ""

# ✅ Main function to process CSV and add 'skills' column
def extract_skills(file_path):
    try:
        df = pd.read_csv(file_path)
        if 'Description' not in df.columns:
            print("❌ Column 'Description' not found in CSV.")
            return
        print("🔁 Extracting skills from descriptions...")
        df['skills'] = df['Description'].apply(extract_skills_from_text)

        output_path = "barclays_full_with_skills_llm.xlsx"
        df.to_excel(output_path, index=False)
        print(f"✅ Skills extracted and saved to {output_path}")
    except Exception as e:
        print("❌ Failed to process file:", e)

# ✅ Run this part if executing directly
if __name__ == "__main__":
    extract_skills("barclays_full.csv")
