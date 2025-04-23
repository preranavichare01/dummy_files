import spacy
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

# Load SpaCy model
nlp = spacy.load('en_core_web_sm')

# Function to process user input
def process_input(user_input):
    # Use SpaCy's NLP model to analyze user input
    
    doc = nlp(user_input.lower())
    if "remove missing" in user_input:
        return "remove_missing"
    elif "impute" in user_input:
        return "impute"
    elif "normalize" in user_input:
        return "normalize"
    elif "remove duplicates" in user_input:
        return "remove_duplicates"
    else:
        return "unknown"

# Preprocessing functions
def preprocess_data(df, action):
    if action == "remove_missing":
        df.dropna(axis=0, how='any', inplace=True)
    elif action == "impute":
        imputer = SimpleImputer(strategy='mean')
        df = pd.DataFrame(imputer.fit_transform(df), columns=df.columns)
    elif action == "normalize":
        scaler = StandardScaler()
        df[df.select_dtypes(include=['float64', 'int64']).columns] = scaler.fit_transform(df[df.select_dtypes(include=['float64', 'int64']).columns])
    elif action == "remove_duplicates":
        df.drop_duplicates(inplace=True)
    return df

# File processing based on user input
def load_data(file_path, file_type):
    if file_type == 'csv':
        df = pd.read_csv(file_path)
    elif file_type == 'excel':
        df = pd.read_excel(file_path)
    elif file_type == 'json':
        df = pd.read_json(file_path)
    return df

# Full processing flow
def process_file(file_path, file_type, user_input):
    df = load_data(file_path, file_type)
    action = process_input(user_input)
    if action != "unknown":
        df = preprocess_data(df, action)
        return df
    else:
        return "Unknown action. Please specify a valid preprocessing task."

# Example usage
file_path = 'user_data.csv'
file_type = 'csv'
user_input = "Remove missing values and normalize data"
processed_df = process_file(file_path, file_type, user_input)
print(processed_df.head())
