import pandas as pd
from datetime import datetime
import os

def mark_attendance(name):

    folder = "attendance"
    os.makedirs(folder, exist_ok=True)

    file_path = os.path.join(os.getcwd(), folder, "attendance.csv")

    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    # -------------------------------
    # CREATE FILE IF NOT EXISTS
    # -------------------------------
    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=["Name", "Date", "Time"])
        df.to_csv(file_path, index=False)

    # -------------------------------
    # LOAD FILE
    # -------------------------------
    df = pd.read_csv(file_path)

    # -------------------------------
    # 🔥 FIX OLD CSV (BEFORE USING df["Date"])
    # -------------------------------
    if "Name" not in df.columns:
        df["Name"] = ""

    if "Date" not in df.columns:
        df["Date"] = ""

    if "Time" not in df.columns:
        df["Time"] = ""

    # Save if structure changed
    df.to_csv(file_path, index=False)

    # -------------------------------
    # NOW SAFE TO USE df["Date"]
    # -------------------------------
    if not ((df["Name"] == name) & (df["Date"] == date)).any():

        new_row = pd.DataFrame([[name, date, time]],
                               columns=["Name", "Date", "Time"])

        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(file_path, index=False)

        print("Saved successfully!")

    else:
        print("Already marked today")
        exit(1)