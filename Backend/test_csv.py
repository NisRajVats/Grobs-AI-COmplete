import pandas as pd
import os

BASE_DIR = r"f:\GrobsAI-Complete\Backend"
DATA_DIR = os.path.join(BASE_DIR, "data")
file_path = os.path.join(DATA_DIR, "Software Questions.csv")

def check_file(filename):
    file_path = os.path.join(DATA_DIR, filename)
    print(f"\nChecking file: {filename}")
    print(f"Exists: {os.path.exists(file_path)}")
    if not os.path.exists(file_path): return
    
    try:
        df = pd.read_csv(file_path)
        print(f"Successfully read CSV with default (UTF-8). Shape: {df.shape}")
    except Exception as e:
        print(f"Error reading with UTF-8: {e}")
        try:
            df = pd.read_csv(file_path, encoding='cp1252')
            print(f"Successfully read with cp1252. Shape: {df.shape}")
        except Exception as e2:
            print(f"Error reading with cp1252: {e2}")

check_file("Software Questions.csv")
check_file("ai_resume_screening (1).csv")
check_file("Resume.csv")
check_file("postings.csv")
