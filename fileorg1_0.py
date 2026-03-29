from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import hashlib
import os
import shutil
import json
import logging
from datetime import datetime
import sys
import threading

# ⚡ FRESH START: Wipe the old undo history every time the app opens
if os.path.exists("undo.log"):
    try:
        os.remove("undo.log")
    except Exception:
        pass

CURRENT_ARGS = None
folder_path = None
LOGGER = None
observer = None
watch_running = False

IGNORE_FILES = {"organizer.log", "rules.json", "main.py", "undo.log", "seen_hashes.txt", "gui.py", "gui.exe"}

EXPLICITLY_UNDONE = set()
LAST_EVENT_TIME = 0

STATE_LOCK = threading.Lock()

# -------- LONG TERM MEMORY --------
def load_hashes():
    if os.path.exists("seen_hashes.txt"):
        with open("seen_hashes.txt", "r") as f:
            return set(line.strip() for line in f.readlines() if line.strip())
    return set()

SEEN_HASHES = load_hashes()

def save_hash(file_hash):
    with STATE_LOCK:
        with open("seen_hashes.txt", "a") as f:
            f.write(f"{file_hash}\n")

def rewrite_hashes():
    with STATE_LOCK:
        with open("seen_hashes.txt", "w") as f:
            for h in SEEN_HASHES:
                f.write(f"{h}\n")
# ----------------------------------

def log_undo(original, new):
    clean_original = os.path.normpath(os.path.abspath(original))
    clean_new = os.path.normpath(os.path.abspath(new))
    with STATE_LOCK:
        with open("undo.log", "a") as f:
            f.write(f"{clean_new}|{clean_original}\n")

def get_file_hash(path):
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()   

def undo_operations():
    global LOGGER, EXPLICITLY_UNDONE, SEEN_HASHES

    with STATE_LOCK:
        if not os.path.exists("undo.log"):
            if LOGGER: LOGGER("No undo log found.")
            return
        with open("undo.log", "r") as f:
            lines = f.readlines()

    if not lines:
        if LOGGER: LOGGER("Nothing to undo.")
        return

    last_session = []
    for line in reversed(lines):
        if line.strip() == "===SESSION===":
            break
        last_session.append(line)

    if not last_session:
        if LOGGER: LOGGER("No recent session to undo.")
        return

    hash_removed = False

    for line in last_session:
        try:
            new, original = line.strip().split("|")
            clean_new = os.path.normpath(os.path.abspath(new))
            clean_original = os.path.normpath(os.path.abspath(original))

            if os.path.exists(clean_new):
                file_hash = get_file_hash(clean_new)
                if file_hash in SEEN_HASHES:
                    SEEN_HASHES.remove(file_hash)
                    hash_removed = True

                os.makedirs(os.path.dirname(clean_original), exist_ok=True)
                
                EXPLICITLY_UNDONE.add(clean_original)
                shutil.move(clean_new, clean_original)

                if LOGGER: LOGGER(f"Restored: {os.path.basename(clean_original)}")
                logging.info(f"Undid move: Restored '{clean_original}'")

        except Exception as e:
            if LOGGER: LOGGER(f"Error undoing: {line} → {e}")
            logging.error(f"Error undoing {line} -> {e}")

    if hash_removed:
        rewrite_hashes()

    remaining_lines = lines[:-(len(last_session) + 1)]
    with STATE_LOCK:
        with open("undo.log", "w") as f:
            f.writelines(remaining_lines)

    if LOGGER: LOGGER("Last session undone.")


# ---------------- LOGGING SETUP ----------------
logging.basicConfig(
    filename="organizer.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ---------------- LOAD RULES ----------------
base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
rules_path = os.path.join(base_path, "rules.json")

try:
    with open(rules_path, "r") as f:
        FILE_TYPES = json.load(f)
except FileNotFoundError:
    FILE_TYPES = {}

# ---------------- ORGANIZE FILES ----------------
def organize_file(file_path):
    try:
        clean_path = os.path.normpath(os.path.abspath(file_path))
        file = os.path.basename(clean_path)

        if os.path.isdir(clean_path) or file in IGNORE_FILES:
            return
        
        if clean_path in EXPLICITLY_UNDONE:
            # ⚡ Silently return without writing spam to the log!
            return
        
        file_hash = get_file_hash(clean_path)
        if file_hash in SEEN_HASHES:
            return
            
        modified_time = os.path.getmtime(clean_path)
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

        destination_dir = os.path.join(folder_path, category, year, month)
        os.makedirs(destination_dir, exist_ok=True)

        destination = os.path.join(destination_dir, file)

        if getattr(CURRENT_ARGS, 'dry_run', False):
            LOGGER(f"[DRY RUN] {file} → {category}/{year}/{month}")
            logging.info(f"[DRY RUN] Would move '{clean_path}' -> '{destination}'") 
        else:
            SEEN_HASHES.add(file_hash)
            
            moved = False
            for _ in range(10): 
                try:
                    if os.path.exists(destination):
                        os.remove(destination) 
                        
                    shutil.move(clean_path, destination)
                    moved = True
                    break
                except PermissionError:
                    time.sleep(0.5) 
            
            if moved:
                save_hash(file_hash)
                log_undo(clean_path, destination)
                if LOGGER: LOGGER(f"Moved '{file}' -> '{category}/{year}/{month}'")
                logging.info(f"Moved '{clean_path}' -> '{destination}'") 
            else:
                SEEN_HASHES.remove(file_hash)
                if LOGGER: LOGGER(f"[ERROR] Could not move '{file}' - File is locked.")
                logging.error(f"Failed to move '{clean_path}' - File locked.") 

    except Exception as e:
        logging.error(f"Error processing {file_path}: {e}")


class WatchHandler(FileSystemEventHandler):
    def on_created(self, event):
        try:
            global LAST_EVENT_TIME
            if not event.is_directory:
                current_time = time.time()
                if current_time - LAST_EVENT_TIME > 2:
                    with STATE_LOCK:
                        with open("undo.log", "a") as f:
                            f.write("===SESSION===\n")
                LAST_EVENT_TIME = current_time
                time.sleep(1) 
                organize_file(event.src_path)
        except Exception as e:
            logging.error(f"Watchdog crash prevented: {e}")

class Args:
    def __init__(self, path, dry_run, watch, undo):
        self.path = path
        self.dry_run = dry_run
        self.watch = watch
        self.undo = undo

def stop_watch_mode(callback=None):
    global watch_running
    if watch_running:
        watch_running = False
    else:
        if callback: callback("[INFO] No watch mode running")

def main(path, dry_run=False, watch=False, undo=False, callback=None):
    global CURRENT_ARGS, folder_path, LOGGER, observer, watch_running, EXPLICITLY_UNDONE

    def log(message):
        if callback: callback(message)
    LOGGER = log

    CURRENT_ARGS = Args(path, dry_run, watch, undo)
    folder_path = os.path.normpath(os.path.abspath(path))

    if not os.path.exists(folder_path):
        log("Folder does not exist.")
        return

    if undo:
        undo_operations()
        return

    EXPLICITLY_UNDONE.clear()

    with STATE_LOCK:
        with open("undo.log", "a") as f:
            f.write("===SESSION===\n")

    for file in os.listdir(folder_path):
        organize_file(os.path.join(folder_path, file))

    log("Organization complete.")

    if watch:
        if watch_running:
            log("[INFO] Watch mode is already running.")
        else:
            watch_running = True
            event_handler = WatchHandler()
            observer = Observer()
            observer.schedule(event_handler, folder_path, recursive=False)
            observer.start()
            log("Watching folder for new files...")

            try:
                while watch_running:
                    time.sleep(0.5) 
            finally:
                if observer:
                    observer.stop()
                    observer.join()
                    observer = None
                watch_running = False
                log("[STOPPED] Watch mode stopped")