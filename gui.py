import fileorg1_0
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
import sys

base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

# -------- APPEARANCE SETTINGS --------
ctk.set_appearance_mode("System")  
ctk.set_default_color_theme("blue") 

# -------- STATE VARIABLES --------
is_log_expanded = True

# -------- FUNCTIONS --------
def select_folder():
    folder = filedialog.askdirectory()
    if folder:
        path_var.set(folder)

def run_organizer():
    path = path_var.get()
    if not path:
        messagebox.showerror("Error", "Please select a folder")
        return
    
    log_box.delete("1.0", "end")
    def update_log(message):
        log_box.insert("end", message + "\n")
        log_box.see("end")

    threading.Thread(
        target=fileorg1_0.main,
        args=(path, dry_run_var.get(), watch_var.get(), False, update_log),
        daemon=True
    ).start()

def run_undo():
    path = path_var.get()
    if not path:
        messagebox.showerror("Error", "Please select a folder")
        return
    log_box.delete("1.0", "end")

    def update_log(message):
        log_box.insert("end", message + "\n")
        log_box.see("end")

    threading.Thread(
        target=fileorg1_0.main,
        args=(path, False, False, True, update_log),
        daemon=True
    ).start()

def stop_watch():
    def update_log(message):
        log_box.insert("end", message + "\n")
        log_box.see("end")
    fileorg1_0.stop_watch_mode(update_log)

def on_closing():
    if fileorg1_0.watch_running:
        fileorg1_0.stop_watch_mode() 
    root.destroy() 
    os._exit(0) 

# ⚡ UPGRADED: Physically resizes the window!
def toggle_log():
    global is_log_expanded
    if is_log_expanded:
        log_box.pack_forget() # Hide the box
        toggle_btn.configure(text="▶ Show Activity Log")
        root.geometry("600x440") # ⚡ Shrink the window
        is_log_expanded = False
    else:
        root.geometry("600x650") # ⚡ Expand the window
        log_box.pack(fill="both", expand=True) # Show the box
        toggle_btn.configure(text="▼ Hide Activity Log")
        is_log_expanded = True

# -------- UI --------
root = ctk.CTk() 
root.title("Sortify")
root.geometry("600x650") 
root.protocol("WM_DELETE_WINDOW", on_closing)

# ⚡ NEW: Load the custom icon for the window and taskbar
icon_path = os.path.join(base_path, "icon.ico")
if os.path.exists(icon_path):
    root.iconbitmap(icon_path)

path_var = ctk.StringVar()
dry_run_var = ctk.BooleanVar()
watch_var = ctk.BooleanVar()

# --- HEADER ---
header_frame = ctk.CTkFrame(root, fg_color="transparent")
header_frame.pack(pady=(25, 15))

ctk.CTkLabel(header_frame, text="Smart File Organizer", font=ctk.CTkFont(size=26, weight="bold")).pack()

# --- MAIN DASHBOARD CARD ---
card = ctk.CTkFrame(root, corner_radius=15)
card.pack(fill="x", padx=40, pady=10)

# 1. Folder Selection
folder_frame = ctk.CTkFrame(card, fg_color="transparent")
folder_frame.pack(fill="x", padx=20, pady=(20, 10))

ctk.CTkLabel(folder_frame, text="Target Directory", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 5))

input_row = ctk.CTkFrame(folder_frame, fg_color="transparent")
input_row.pack(fill="x")

path_entry = ctk.CTkEntry(input_row, textvariable=path_var, height=35, placeholder_text="Select a folder to organize...")
path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

browse_btn = ctk.CTkButton(input_row, text="📂 Browse", width=90, height=35, font=ctk.CTkFont(weight="bold"), command=select_folder)
browse_btn.pack(side="left")

# 2. Toggle Settings (iOS Style)
settings_frame = ctk.CTkFrame(card, fg_color="transparent")
settings_frame.pack(fill="x", padx=20, pady=(10, 20))

ctk.CTkSwitch(settings_frame, text="Dry Run (Test Only)", variable=dry_run_var, font=ctk.CTkFont(size=13)).pack(side="left", padx=(0, 30))
ctk.CTkSwitch(settings_frame, text="Watch Mode (Auto-Organize)", variable=watch_var, font=ctk.CTkFont(size=13)).pack(side="left")

# --- CONTROL DECK (Action Buttons) ---
button_card = ctk.CTkFrame(root, fg_color="transparent")
button_card.pack(fill="x", padx=40, pady=10)

button_card.columnconfigure(0, weight=1)
button_card.columnconfigure(1, weight=1)

organize_btn = ctk.CTkButton(button_card, text="🚀 Organize Files", height=45, fg_color="#10B981", hover_color="#059669", font=ctk.CTkFont(size=15, weight="bold"), command=run_organizer)
organize_btn.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

undo_btn = ctk.CTkButton(button_card, text="↩️ Undo Last", height=40, fg_color="#EF4444", hover_color="#DC2626", font=ctk.CTkFont(weight="bold"), command=run_undo)
undo_btn.grid(row=1, column=0, sticky="ew", padx=(0, 5))

stop_btn = ctk.CTkButton(button_card, text="🛑 Stop Watch", height=40, fg_color="#4B5563", hover_color="#374151", font=ctk.CTkFont(weight="bold"), command=stop_watch)
stop_btn.grid(row=1, column=1, sticky="ew", padx=(5, 0))

# --- TERMINAL / LOG OUTPUT ---
log_frame = ctk.CTkFrame(root, fg_color="transparent")
log_frame.pack(fill="both", expand=True, padx=40, pady=(10, 25))

# The clickable toggle button
toggle_btn = ctk.CTkButton(log_frame, text="▼ Hide Activity Log", fg_color="transparent", hover_color="#374151", text_color=("black", "white"), font=ctk.CTkFont(size=14, weight="bold"), anchor="w", command=toggle_log)
toggle_btn.pack(fill="x", pady=(0, 5))

# The log box (Scrollbar appears automatically when text overflows!)
log_box = ctk.CTkTextbox(log_frame, corner_radius=10, font=ctk.CTkFont(family="Consolas", size=12))
log_box.pack(fill="both", expand=True)

root.mainloop()