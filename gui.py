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
    # Dynamically update the text when clicked
    if dry_run_var.get():
        dry_run_switch.configure(text="Dry Run: ON")
    else:
        dry_run_switch.configure(text="Dry Run: OFF")

def toggle_watch():
    path = path_var.get()
    
    if watch_var.get(): # If turned ON
        if not path:
            messagebox.showerror("Error", "Please select a folder first.")
            watch_var.set(False) # Revert the switch
            watch_switch.configure(text="Watch Mode: OFF")
            return
        
        watch_switch.configure(text="Watch Mode: ON")
        organize_btn.configure(state="disabled") # ⚡ Gray out manual button!
        
        def update_log(message):
            log_box.insert("end", message + "\n")
            log_box.see("end")
            
        # Start watching immediately
        threading.Thread(
            target=fileorg1_0.main,
            args=(path, dry_run_var.get(), True, False, update_log),
            daemon=True
        ).start()
        
    else: # If turned OFF
        watch_switch.configure(text="Watch Mode: OFF")
        organize_btn.configure(state="normal") # ⚡ Re-enable manual button
        
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

    # Manual organize (watch is forced False here)
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

# Load the custom icon
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

# 2. Toggle Settings (Now heavily integrated!)
settings_frame = ctk.CTkFrame(card, fg_color="transparent")
settings_frame.pack(fill="x", padx=20, pady=(10, 20))

# ⚡ Added onvalue/offvalue and hooked them to commands
dry_run_switch = ctk.CTkSwitch(settings_frame, text="Dry Run: OFF", variable=dry_run_var, onvalue=True, offvalue=False, command=toggle_dry_run, font=ctk.CTkFont(size=13))
dry_run_switch.pack(side="left", padx=(0, 30))

watch_switch = ctk.CTkSwitch(settings_frame, text="Watch Mode: OFF", variable=watch_var, onvalue=True, offvalue=False, command=toggle_watch, font=ctk.CTkFont(size=13))
watch_switch.pack(side="left")

# --- CONTROL DECK (Action Buttons) ---
button_card = ctk.CTkFrame(root, fg_color="transparent")
button_card.pack(fill="x", padx=40, pady=10)

button_card.columnconfigure(0, weight=1)

# The stop button has been completely removed!
organize_btn = ctk.CTkButton(button_card, text="🚀 Organize Files", height=45, fg_color="#10B981", hover_color="#059669", font=ctk.CTkFont(size=15, weight="bold"), command=run_organizer)
organize_btn.grid(row=0, column=0, sticky="ew", pady=(0, 10))

undo_btn = ctk.CTkButton(button_card, text="↩️ Undo Last", height=40, fg_color="#EF4444", hover_color="#DC2626", font=ctk.CTkFont(weight="bold"), command=run_undo)
undo_btn.grid(row=1, column=0, sticky="ew")

# --- TERMINAL / LOG OUTPUT ---
log_frame = ctk.CTkFrame(root, fg_color="transparent")
log_frame.pack(fill="both", expand=True, padx=40, pady=(10, 25))

toggle_btn = ctk.CTkButton(log_frame, text="▼ Hide Activity Log", fg_color="transparent", hover_color="#374151", text_color=("black", "white"), font=ctk.CTkFont(size=14, weight="bold"), anchor="w", command=toggle_log)
toggle_btn.pack(fill="x", pady=(0, 5))

log_box = ctk.CTkTextbox(log_frame, corner_radius=10, font=ctk.CTkFont(family="Consolas", size=12))
log_box.pack(fill="both", expand=True)

root.mainloop()