import sqlite3
import os
from datetime import datetime
from utils import STORAGE_DIR, DB_PATH
import pandas as pd

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS invoices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        customer TEXT,
                        total REAL,
                        invoice_number TEXT,
                        date_time TEXT,
                        invoice_date TEXT,
                        customer_email TEXT,
                        customer_contact TEXT
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS invoice_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        invoice_id INTEGER,
                        product TEXT,
                        quantity INTEGER,
                        price REAL,
                        FOREIGN KEY(invoice_id) REFERENCES invoices(id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS organization_info (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        org_name TEXT,
                        gst_number TEXT,
                        tin_number TEXT,
                        org_address TEXT,
                        org_email TEXT,
                        org_contact TEXT,
                        org_logo BLOB,
                        date_time TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS archived_invoices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        customer TEXT,
                        total REAL,
                        invoice_number TEXT,
                        invoice_date TEXT,
                        customer_email TEXT,
                        customer_contact TEXT,
                        archive_timestamp TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS archive_backups (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        archive_timestamp TEXT)''')
    
    # Add default organization info if the table is empty
    cursor.execute("SELECT COUNT(*) FROM organization_info")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''INSERT INTO organization_info (org_name, gst_number, tin_number, org_address, org_email, org_contact, date_time)
                          VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      ("My Organization", "GST123456789", "TIN987654321", "123 Main St, City, Country \nMain Region \nZip Code - 00 00 00", "contact@my_organization.com", "(+00) 000 000 0000", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    conn.commit()
    conn.close()

def fetch_non_archived_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Fetch invoices and invoice items
    cursor.execute("SELECT id, date_time, total FROM invoices")
    invoices = cursor.fetchall()
    
    cursor.execute("SELECT invoice_id, product, quantity, price FROM invoice_items")
    items = cursor.fetchall()
    
    conn.close()
    
    # Convert to pandas DataFrame
    invoices_df = pd.DataFrame(invoices, columns=["id", "date_time", "total"])
    items_df = pd.DataFrame(items, columns=["invoice_id", "product", "quantity", "price"])
    
    return invoices_df, items_df
