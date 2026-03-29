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

def toggle_dry_run():
    if dry_run_var.get():
        dry_run_switch.configure(text="Dry Run: ON")
    else:
        dry_run_switch.configure(text="Dry Run: OFF")

def toggle_watch():
    path = path_var.get()
    
    # Check the actual backend state to see if we are starting or stopping
    if not fileorg1_0.watch_running: 
        if not path:
            messagebox.showerror("Error", "Please select a folder first.")
            return
        
        # UI Changes: Turn into a "Stop" button and disable manual organize
        watch_btn.configure(text="🛑 Stop Watch Mode", fg_color="#EF4444", hover_color="#DC2626")
        watch_desc.configure(text="Actively monitoring folder...")
        organize_btn.configure(state="disabled") 
        
        def update_log(message):
            log_box.insert("end", message + "\n")
            log_box.see("end")
            
        threading.Thread(
            target=fileorg1_0.main,
            args=(path, dry_run_var.get(), True, False, update_log),
            daemon=True
        ).start()
        
    else: 
        # UI Changes: Revert back to a "Start" button
        watch_btn.configure(text="👁️ Start Watch Mode", fg_color="#3B82F6", hover_color="#2563EB")
        watch_desc.configure(text="Auto-sorts newly added files.")
        organize_btn.configure(state="normal") 
        
        def update_log(message):
            log_box.insert("end", message + "\n")
            log_box.see("end")
            
        fileorg1_0.stop_watch_mode(update_log)

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
        args=(path, dry_run_var.get(), False, False, update_log),
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

def on_closing():
    if fileorg1_0.watch_running:
        fileorg1_0.stop_watch_mode() 
    root.destroy() 
    os._exit(0) 

def toggle_log():
    global is_log_expanded
    if is_log_expanded:
        log_box.pack_forget() 
        toggle_btn.configure(text="▶ Show Activity Log")
        root.geometry("600x440") 
        is_log_expanded = False
    else:
        root.geometry("600x650") 
        log_box.pack(fill="both", expand=True) 
        toggle_btn.configure(text="▼ Hide Activity Log")
        is_log_expanded = True

# -------- UI --------
root = ctk.CTk() 
root.title("Sortify") 
root.geometry("600x650") 
root.protocol("WM_DELETE_WINDOW", on_closing)

icon_path = os.path.join(base_path, "icon.ico")
if os.path.exists(icon_path):
    root.iconbitmap(icon_path)

path_var = ctk.StringVar()
dry_run_var = ctk.BooleanVar()

# --- HEADER ---
header_frame = ctk.CTkFrame(root, fg_color="transparent")
header_frame.pack(pady=(25, 10))
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

# 2. Toggle Settings (Only Dry Run remains here!)
settings_frame = ctk.CTkFrame(card, fg_color="transparent")
settings_frame.pack(fill="x", padx=20, pady=(10, 20))

dry_run_switch = ctk.CTkSwitch(settings_frame, text="Dry Run: OFF", variable=dry_run_var, onvalue=True, offvalue=False, command=toggle_dry_run, font=ctk.CTkFont(size=13))
dry_run_switch.pack(side="left")


# --- CONTROL DECK (Action Buttons) ---
button_card = ctk.CTkFrame(root, fg_color="transparent")
button_card.pack(fill="x", padx=40, pady=5)

button_card.columnconfigure(0, weight=1)
button_card.columnconfigure(1, weight=1)

# Action 1: Manual Organize
organize_btn = ctk.CTkButton(button_card, text="🚀 Organize Now", height=45, fg_color="#10B981", hover_color="#059669", font=ctk.CTkFont(size=15, weight="bold"), command=run_organizer)
organize_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=(0, 2))

# Action 2: Watch Mode
watch_btn = ctk.CTkButton(button_card, text="👁️ Start Watch Mode", height=45, fg_color="#3B82F6", hover_color="#2563EB", font=ctk.CTkFont(size=15, weight="bold"), command=toggle_watch)
watch_btn.grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=(0, 2))

# Helpful Descriptions
org_desc = ctk.CTkLabel(button_card, text="One-time instant cleanup.", font=ctk.CTkFont(size=11), text_color="gray")
org_desc.grid(row=1, column=0, sticky="n", pady=(0, 15))

watch_desc = ctk.CTkLabel(button_card, text="Auto-sorts newly added files.", font=ctk.CTkFont(size=11), text_color="gray")
watch_desc.grid(row=1, column=1, sticky="n", pady=(0, 15))

# Action 3: Undo
undo_btn = ctk.CTkButton(button_card, text="↩️ Undo Last Action", height=40, fg_color="#6B7280", hover_color="#4B5563", font=ctk.CTkFont(weight="bold"), command=run_undo)
undo_btn.grid(row=2, column=0, columnspan=2, sticky="ew")


# --- TERMINAL / LOG OUTPUT ---
log_frame = ctk.CTkFrame(root, fg_color="transparent")
log_frame.pack(fill="both", expand=True, padx=40, pady=(10, 25))

toggle_btn = ctk.CTkButton(log_frame, text="▼ Hide Activity Log", fg_color="transparent", hover_color="#374151", text_color=("black", "white"), font=ctk.CTkFont(size=14, weight="bold"), anchor="w", command=toggle_log)
toggle_btn.pack(fill="x", pady=(0, 5))

log_box = ctk.CTkTextbox(log_frame, corner_radius=10, font=ctk.CTkFont(family="Consolas", size=12))
log_box.pack(fill="both", expand=True)

root.mainloop()