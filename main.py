from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import pandas as pd
import os
import requests  # For sending requests to Groq API
from io import BytesIO

# Your Groq API key
GROQ_API_KEY = "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"

# Groq API URL
GROQ_API_URL = "https://api.groq.com/v1/completions"
MAX_FILE_SIZE = 1024 * 1024 * 100
# Initialize FastAPI app
app = FastAPI()

# Folder to save processed data temporarily
TEMP_DIR = "./processed_data"

# Ensure the directory exists
os.makedirs(TEMP_DIR, exist_ok=True)

# Function to process the command using Groq API
def parse_command_with_groq(command: str):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Send the command to Groq API for processing
    payload = {
        "model": "groq-v1",  # Specify the model to use, adjust if necessary
        "prompt": f"Translate the following instruction into a structured JSON format for data preprocessing: {command}",
        "max_tokens": 100,
        "temperature": 0.5
    }

    response = requests.post(GROQ_API_URL, headers=headers, json=payload)
    
    if response.status_code == 200:
        parsed_command = response.json().get("choices")[0].get("text").strip()
        return parsed_command
    else:
        return None

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
    df = pd.read_excel(file_location)
    
    # Parse the command using Groq
    parsed_command = parse_command_with_groq(command)
    
    if not parsed_command:
        return {"error": "Failed to process the command. Please try again."}
    
    try:
        # Convert the parsed command to a dictionary for easier execution
        command_dict = eval(parsed_command)  # Be cautious when using eval, or you can use a safer alternative
        
        if command_dict.get("clean"):
            df.dropna(inplace=True)  # Clean the data by dropping missing values
        
        if command_dict.get("preprocess"):
            # Example preprocessing steps like filling NaNs with the mean
            df.fillna(df.mean(), inplace=True)
        
        # Save the cleaned and processed data to a new file
        processed_file = f"{TEMP_DIR}/processed_{file.filename}"
        df.to_excel(processed_file, index=False)
        
        return {
            "message": "Data processed successfully!",
            "rows": len(df),
            "columns": len(df.columns),
            "command_used": command,
            "download_url": f"/download/{processed_file.split('/')[-1]}"
        }
    except Exception as e:
        return {"error": f"Failed to process the data: {str(e)}"}

@app.get("/download/{file_name}")
async def download_file(file_name: str):
    # Ensure that the file exists
    full_file_path = os.path.join(TEMP_DIR, file_name)
    
    if os.path.exists(full_file_path):
        return FileResponse(full_file_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=file_name)
    else:
        return {"error": "File not found."}
