from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import pandas as pd
import os
from transformers import pipeline
from io import BytesIO

# Initialize FastAPI app
app = FastAPI()

# Set up Hugging Face pipeline
pipe = pipeline("text-generation", model="EleutherAI/gpt-neo-2.7B")

# Folder to save processed data temporarily
TEMP_DIR = "./processed_data"
os.makedirs(TEMP_DIR, exist_ok=True)

MAX_FILE_SIZE = 1024 * 1024 * 100  # 100MB

# Function to process command
def process_command(command: str):
    response = pipe(command, max_length=100, num_return_sequences=1)
    return response[0]['generated_text']

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), command: str = ""):
    # Check file size
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds the maximum limit (100MB).")

    # Save the uploaded file temporarily
    file_location = f"{TEMP_DIR}/{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())

    # Read the dataset using pandas
    try:
        df = pd.read_excel(file_location)
    except Exception as e:
        return {"error": f"Failed to read file: {str(e)}"}

    # Process the command using Hugging Face model
    processed_command = process_command(command)

    # Example of how we could handle different commands
    if "clean" in processed_command:
        df.dropna(inplace=True)  # Drop missing values
    if "preprocess" in processed_command:
        df.fillna(df.mean(), inplace=True)  # Fill NaN with mean

    # Save the processed file
    processed_file = f"{TEMP_DIR}/processed_{file.filename}"
    df.to_excel(processed_file, index=False)

    return {
        "message": "Data processed successfully!",
        "rows": len(df),
        "columns": len(df.columns),
        "command_used": processed_command,
        "download_url": f"/download/{processed_file.split('/')[-1]}"
    }

@app.get("/download/{file_name}")
async def download_file(file_name: str):
    # Ensure that the file exists
    full_file_path = os.path.join(TEMP_DIR, file_name)
    
    if os.path.exists(full_file_path):
        return FileResponse(full_file_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=file_name)
    else:
        raise HTTPException(status_code=404, detail="File not found.")
