import sqlite3
import tkinter as tk
from tkinter import messagebox
from utils import DB_PATH
import os
from datetime import datetime, timedelta
from tkinter import filedialog

def save_org_info(org_name_entry, gst_entry, tin_entry, org_address_text, org_email_entry, org_contact_entry):
    org_name = org_name_entry.get()
    if not org_name:
        messagebox.showerror("Error", "Organization Name is required!")
        return
    
    gst_number = gst_entry.get()
    tin_number = tin_entry.get()
    org_address = org_address_text.get("1.0", tk.END).strip()
    org_email = org_email_entry.get().strip()
    org_contact = org_contact_entry.get().strip()
    org_logo = org_logo_blob if 'org_logo_blob' in globals() else None
    date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO organization_info 
                      (org_name, gst_number, tin_number, org_address, org_email, org_contact, org_logo, date_time) 
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                   (org_name, gst_number, tin_number, org_address, org_email, org_contact, org_logo, date_time))
    conn.commit()
    conn.close()
    messagebox.showinfo("Success", "Organization Info Saved Successfully!")
    load_org_info(org_name_entry, gst_entry, tin_entry, org_address_text, org_email_entry, org_contact_entry)

def load_org_info(org_name_entry, gst_entry, tin_entry, org_address_text, org_email_entry, org_contact_entry):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT org_name, gst_number, tin_number, org_address, org_email, org_contact, org_logo FROM organization_info ORDER BY date_time DESC LIMIT 1")
    org_info = cursor.fetchone()
    conn.close()
    
    if org_info:
        org_info = list(org_info) + [None] * (7 - len(org_info))
        
        org_name_entry.delete(0, tk.END)
        org_name_entry.insert(0, org_info[0])
        gst_entry.delete(0, tk.END)
        gst_entry.insert(0, org_info[1])
        tin_entry.delete(0, tk.END)
        tin_entry.insert(0, org_info[2])
        org_address_text.delete("1.0", tk.END)
        org_address_text.insert("1.0", org_info[3])
        
        org_email_entry.delete(0, tk.END)
        if org_info[4]:
            org_email_entry.insert(0, org_info[4])
        
        org_contact_entry.delete(0, tk.END)
        if org_info[5]:
            org_contact_entry.insert(0, org_info[5])
        
        if org_info[6]:
            global org_logo_blob
            org_logo = org_info[6]
            org_logo.delete(0, tk.END)
            org_logo.insert(0, "Logo Uploaded")

def upload_logo(org_logo_entry):
    file_path = filedialog.askopenfilename(
        title="Select Organization Logo",
        filetypes=[("Image Files", "*.jpg *.jpeg *.png *svg")]
    )
    if file_path:
        file_size = os.path.getsize(file_path) / (1024 * 1024)
        if file_size > 2:
            messagebox.showerror("Error", "File size must be less than 2 MB!")
            return
        with open(file_path, "rb") as file:
            global org_logo_blob
            org_logo_blob = file.read()
        
        org_logo_entry.config(state="normal")
        org_logo_entry.delete(0, tk.END)
        org_logo_entry.insert(0, os.path.basename(file_path))
        org_logo_entry.config(state="readonly")