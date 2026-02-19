import os
import shutil
import json
import argparse
import logging
from datetime import datetime


# ---------------- LOGGING SETUP ----------------
logging.basicConfig(
    filename="organizer.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ---------------- ARGUMENT PARSER ----------------
parser = argparse.ArgumentParser(description="Smart File Organizer")
parser.add_argument("path", help="Folder path to organize")
parser.add_argument("--dry-run", action="store_true", help="Preview changes without moving files")
args = parser.parse_args()

folder_path = args.path

if not os.path.exists(folder_path):
    print("❌ Folder does not exist.")
    exit()

# ---------------- LOAD RULES ----------------
with open("rules.json", "r") as f:
    FILE_TYPES = json.load(f)



# ---------------- ORGANIZE FILES ----------------
for file in os.listdir(folder_path):
    file_path = os.path.join(folder_path, file)

    if os.path.isdir(file_path):
        continue

    # Get modified date
    modified_time = os.path.getmtime(file_path)
    date = datetime.fromtimestamp(modified_time)
    year = str(date.year)
    month = date.strftime("%B")

    _, extension = os.path.splitext(file.lower())

    for folder, extensions in FILE_TYPES.items():
        if extension in extensions:
            category = folder
            break
    else:
        category = "Others"

    destination_dir = os.path.join(
        folder_path, category, year, month
    )
    os.makedirs(destination_dir, exist_ok=True)

    destination = os.path.join(destination_dir, file)

    if args.dry_run:
        print(f"[DRY RUN] {file} → {category}/{year}/{month}")
    else:
        shutil.move(file_path, destination)
        logging.info(
            f"Moved '{file}' → '{destination_dir}'"
        )


print("✅ Organization complete.")
