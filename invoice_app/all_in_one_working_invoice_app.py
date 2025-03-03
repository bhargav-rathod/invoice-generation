import sqlite3
import sys
import os
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from tkcalendar import Calendar
from tkinter import filedialog
from io import BytesIO
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image
from reportlab.lib.units import inch

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except ImportError:
    print("Warning: Tkinter is not available. Running in non-GUI mode.")
    tk = None

# Constants
storage_dir = os.path.join(os.path.expanduser("~"), "Desktop", "Invoices")
os.makedirs(storage_dir, exist_ok=True)
db_path = os.path.join(storage_dir, "invoices.db")
FONT = ("Calibri", 12)
HEADER_FONT = ("Calibri", 14, "bold")
BUTTON_FONT = ("Calibri", 12)
BACKGROUND_COLOR = "#f0f0f0"
BUTTON_COLOR = "#814caf"
BUTTON_HOVER_COLOR = "#5d9ce3"
TEXT_COLOR = "#333333"
ENTRY_BG = "#ffffff"
TREEVIEW_BG = "#ffffff"
TREEVIEW_HEADER_BG = "#4CAF50"
TREEVIEW_HEADER_FG = "#ffffff"

# Initialize Database
def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS invoices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        customer TEXT,
                        total REAL,
                        invoice_number TEXT,
                        date_time TEXT,
                        invoice_date TEXT,  -- New column for invoice date
                        customer_email TEXT,  -- New column for customer email
                        customer_contact TEXT -- New column for customer contact
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

# Refresh Invoice List
def refresh_invoice_list():
    for row in history_tree.get_children():
        history_tree.delete(row)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, invoice_number, customer, total, invoice_date, customer_email, customer_contact FROM invoices")
    invoices = cursor.fetchall()
    conn.close()
    
    for invoice in invoices:
        history_tree.insert("", "end", values=invoice)

# Save Organization Info
def save_org_info():
    org_name = org_name_entry.get()
    if not org_name:
        messagebox.showerror("Error", "Organization Name is required!")
        return
    
    gst_number = gst_entry.get()
    tin_number = tin_entry.get()
    org_address = org_address_text.get("1.0", tk.END).strip()
    org_email = org_email_entry.get().strip()
    org_contact = org_contact_entry.get().strip()
    org_logo = org_logo_blob if 'org_logo_blob' in globals() else None  # Get the logo binary data
    date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO organization_info 
                      (org_name, gst_number, tin_number, org_address, org_email, org_contact, org_logo, date_time) 
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                   (org_name, gst_number, tin_number, org_address, org_email, org_contact, org_logo, date_time))
    conn.commit()
    conn.close()
    messagebox.showinfo("Success", "Organization Info Saved Successfully!")
    load_org_info()

# Load Latest Organization Info
def load_org_info():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT org_name, gst_number, tin_number, org_address, org_email, org_contact, org_logo FROM organization_info ORDER BY date_time DESC LIMIT 1")
    org_info = cursor.fetchone()
    conn.close()
    
    if org_info:
        # Ensure org_info has at least 7 elements (fill with None if missing)
        org_info = list(org_info) + [None] * (7 - len(org_info))
        
        org_name_entry.delete(0, tk.END)
        org_name_entry.insert(0, org_info[0])
        gst_entry.delete(0, tk.END)
        gst_entry.insert(0, org_info[1])
        tin_entry.delete(0, tk.END)
        tin_entry.insert(0, org_info[2])
        org_address_text.delete("1.0", tk.END)
        org_address_text.insert("1.0", org_info[3])
        
        # Optional fields (org_email, org_contact, org_logo)
        org_email_entry.delete(0, tk.END)
        if org_info[4]:  # org_email
            org_email_entry.insert(0, org_info[4])
        
        org_contact_entry.delete(0, tk.END)
        if org_info[5]:  # org_contact
            org_contact_entry.insert(0, org_info[5])
        
        # Load logo (if available)
        if org_info[6]:  # org_logo
            global org_logo_blob
            org_logo_blob = org_info[6]  # Store the binary data globally
            org_logo_entry.delete(0, tk.END)
            org_logo_entry.insert(0, "Logo Uploaded")

# Reset Invoice Tab
def reset_invoice_tab():
    # Reset customer fields
    customer_entry.delete(0, tk.END)
    customer_email_entry.delete(0, tk.END)
    customer_contact_entry.delete(0, tk.END)
    
    # Reset product fields
    product_entry.delete(0, tk.END)
    quantity_entry.delete(0, tk.END)
    price_entry.delete(0, tk.END)
    
    # Reset product tree
    for item in product_tree.get_children():
        product_tree.delete(item)
    
    # Reset total amount
    total_label.config(text="Total: ₹0.00")
    
    # Reset calendar to current date
    invoice_date_var.set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# Save Invoice
def save_invoice():
    customer = customer_entry.get()
    if not customer:
        messagebox.showerror("Error", "Customer name is required!")
        return
    
    invoice_number = f"INV-{int(datetime.timestamp(datetime.now()))}"
    invoice_date = invoice_date_var.get()  # Get the selected invoice date
    
    # Optional fields
    customer_email = customer_email_entry.get().strip()
    customer_contact = customer_contact_entry.get().strip()
    
    total = 0
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Insert into invoices table with new fields
    cursor.execute('''INSERT INTO invoices 
                      (customer, total, invoice_number, date_time, invoice_date, customer_email, customer_contact) 
                      VALUES (?, ?, ?, ?, ?, ?, ?)''',
                   (customer, total, invoice_number, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                    invoice_date, customer_email, customer_contact))
    
    invoice_id = cursor.lastrowid
    
    # Insert invoice items
    for item in product_tree.get_children():
        values = product_tree.item(item, "values")
        quantity, price = int(values[1]), float(values[2])
        item_total = quantity * price
        total += item_total
        cursor.execute("INSERT INTO invoice_items (invoice_id, product, quantity, price) VALUES (?, ?, ?, ?)", 
                       (invoice_id, values[0], quantity, price))
    
    # Update total in the invoice
    cursor.execute("UPDATE invoices SET total = ? WHERE id = ?", (total, invoice_id))
    conn.commit()
    conn.close()
    
    # Generate PDF
    generate_pdf(invoice_id, customer, total, invoice_number, invoice_date, customer_email, customer_contact)
    
    messagebox.showinfo("Success", "Invoice Saved Successfully!")
    
    # Clear input fields
    reset_invoice_tab()
    refresh_invoice_list()

# Generate PDF
def generate_pdf(invoice_id, customer, total, invoice_number, date_time, customer_email="", customer_contact=""):
    filename = f"invoice_{invoice_number}.pdf"
    pdf_path = os.path.join(storage_dir, filename)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT product, quantity, price FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
    items = cursor.fetchall()
    cursor.execute("SELECT org_name, gst_number, tin_number, org_address, org_email, org_contact, org_logo FROM organization_info ORDER BY date_time DESC LIMIT 1")
    org_info = cursor.fetchone()
    conn.close()
    
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Function to add header (logo) to every page
    def add_header(canvas, doc):
        if org_info and org_info[6]:  # Check if org_logo exists
            logo_image = Image(BytesIO(org_info[6]), width=1.5*inch, height=0.75*inch)  # Adjust size as needed
            logo_image.drawOn(canvas, doc.width + doc.leftMargin - 1.5*inch, doc.height + doc.topMargin - 0.25*inch)

    # Add "TAX/INVOICE" at the top center
    tax_invoice_style = styles["Title"]
    tax_invoice_style.fontSize = 14
    elements.append(Paragraph("TAX/INVOICE", tax_invoice_style))
    elements.append(Spacer(1, 12))
    
    # Add Organization Info
    if org_info:
        org_name, gst_number, tin_number, org_address, org_email, org_contact, org_logo = org_info
        org_name_paragraph = Paragraph(f"<b>{org_name}</b>", styles["Normal"])
        elements.append(org_name_paragraph)
        
        if gst_number:
            elements.append(Paragraph(f"GST Number: {gst_number}", styles["Normal"]))
        if tin_number:
            elements.append(Paragraph(f"TIN Number: {tin_number}", styles["Normal"]))
        if org_address:
            elements.append(Paragraph(f"Address: {org_address}", styles["Normal"]))
        if org_email:
            elements.append(Paragraph(f"Email: {org_email}", styles["Normal"]))
        if org_contact:
            elements.append(Paragraph(f"Contact: {org_contact}", styles["Normal"]))
        
        elements.append(Spacer(1, 12))
    
    # Add Invoice Details
    invoice_style = styles["Heading2"]
    invoice_style.fontSize = 10
    invoice_text = f"Invoice Number: {invoice_number}<br/>Customer: {customer}<br/>"
    
    # Add optional fields if provided
    if customer_email:
        invoice_text += f"Email: {customer_email}<br/>"
    if customer_contact:
        invoice_text += f"Contact: {customer_contact}<br/>"
    
    invoice_text += f"<align right>Date: {date_time}</align>"
    elements.append(Paragraph(invoice_text, invoice_style))
    elements.append(Spacer(1, 12))
    
    # Add Items Table
    table_data = [["Product", "Quantity", "Price", "Total"]]
    for product, quantity, price in items:
        table_data.append([product, str(quantity), f"{price:.2f}", f"{quantity * price:.2f}"])
    
    table_data.append(["", "", "Total Amount:", f"{total:.2f}"])
    
    col_widths = [200, 80, 80, 80]
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('SPAN', (0, -1), (2, -1)),
        ('ALIGN', (0, -1), (-1, -1), 'RIGHT'),
    ]))
    elements.append(table)
    
    # Build the PDF with the header
    doc.build(elements, onFirstPage=add_header, onLaterPages=add_header)
    
    if tk:
        messagebox.showinfo("PDF Generated", f"Invoice saved as {filename}")
        os.startfile(pdf_path)
    else:
        print(f"Invoice saved as {filename}")


# Add Product with Validation
def add_product():
    product = product_entry.get()
    quantity = quantity_entry.get()
    price = price_entry.get()
    
    if not product or not quantity or not price:
        messagebox.showerror("Error", "All product fields are required!")
        return
    
    try:
        quantity = int(quantity)
        if quantity <= 0:
            raise ValueError("Quantity must be a positive integer.")
    except ValueError:
        messagebox.showerror("Error", "Quantity must be a positive integer.")
        return
    
    try:
        price = float(price)
        if price <= 0:
            raise ValueError("Price must be a positive number.")
    except ValueError:
        messagebox.showerror("Error", "Price must be a valid number.")
        return
    
    product_tree.insert("", "end", values=(product, quantity, price))
    product_entry.delete(0, tk.END)
    quantity_entry.delete(0, tk.END)
    price_entry.delete(0, tk.END)
    product_entry.focus()
    update_total()

# Update Total in Create Invoice Tab
def update_total():
    total = 0
    for item in product_tree.get_children():
        values = product_tree.item(item, "values")
        quantity, price = int(values[1]), float(values[2])
        total += quantity * price
    total_label.config(text=f"Total: ₹{total:.2f}")

# Open Invoice PDF
def open_invoice_pdf(event):
    selected_item = history_tree.selection()
    if not selected_item:
        return
    invoice_data = history_tree.item(selected_item, "values")
    invoice_number = invoice_data[1]
    pdf_path = os.path.join(storage_dir, f"invoice_{invoice_number}.pdf")
    if os.path.exists(pdf_path):
        os.startfile(pdf_path)
    else:
        messagebox.showerror("Error", "Invoice PDF not found!")

# Add Edit Product Functionality
def edit_product():
    selected_item = product_tree.selection()
    if not selected_item:
        messagebox.showerror("Error", "Please select an item to edit.")
        return
    item_values = product_tree.item(selected_item, "values")
    product_entry.delete(0, tk.END)
    product_entry.insert(0, item_values[0])
    quantity_entry.delete(0, tk.END)
    quantity_entry.insert(0, item_values[1])
    price_entry.delete(0, tk.END)
    price_entry.insert(0, item_values[2])
    product_tree.delete(selected_item)
    update_total()

# Add Delete Product Functionality
def delete_product():
    selected_item = product_tree.selection()
    if not selected_item:
        messagebox.showerror("Error", "Please select an item to delete.")
        return
    product_tree.delete(selected_item)
    update_total()

# Add Filter Functionality
def filter_invoices():
    invoice_number = invoice_number_filter_entry.get().strip()
    customer = customer_filter_entry.get().strip()
    total = total_filter_entry.get().strip()
    date = date_filter_entry.get().strip()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Base query
    query = "SELECT id, invoice_number, customer, total, date_time FROM invoices WHERE 1=1"
    
    # Add filters based on input
    if invoice_number:
        query += f" AND invoice_number LIKE '%{invoice_number}%'"
    if customer:
        query += f" AND customer LIKE '%{customer}%'"
    if total:
        query += f" AND total = {float(total)}"
    if date:
        query += f" AND date_time LIKE '%{date}%'"
    
    cursor.execute(query)
    invoices = cursor.fetchall()
    conn.close()
    
    # Clear existing rows in the treeview
    for row in history_tree.get_children():
        history_tree.delete(row)
    
    # Insert filtered rows
    for invoice in invoices:
        history_tree.insert("", "end", values=invoice)

# Archive Data Functionality
def archive_data(period):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get current timestamp for the archive
    archive_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Debugging: Print the archive timestamp
    print(f"Archive timestamp: {archive_timestamp}")
    
    # Determine the date limit based on the period
    if period == "last_year":
        date_limit = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    elif period == "last_6_months":
        date_limit = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
    elif period == "last_1_month":
        date_limit = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    elif period == "all_data":
        date_limit = None
    else:
        messagebox.showerror("Error", "Invalid period specified!")
        return
    
    # Debugging: Print the date limit
    print(f"Date limit for {period}: {date_limit}")
    
    # Move data to archived_invoices table based on the date limit
    if date_limit:
        cursor.execute(f'''INSERT INTO archived_invoices (customer, total, invoice_number, invoice_date, archive_timestamp)
                          SELECT customer, total, invoice_number, invoice_date, ? FROM invoices
                          WHERE invoice_date <= ?''',
                      (archive_timestamp, date_limit))
    else:
        cursor.execute(f'''INSERT INTO archived_invoices (customer, total, invoice_number, invoice_date, archive_timestamp)
                          SELECT customer, total, invoice_number, invoice_date, ? FROM invoices''',
                      (archive_timestamp,))
    
    # Debugging: Check how many rows are being archived
    cursor.execute("SELECT COUNT(*) FROM invoices WHERE invoice_date <= ?", (date_limit,)) if date_limit else cursor.execute("SELECT COUNT(*) FROM invoices")
    rows_archived = cursor.fetchone()[0]
    print(f"Rows to be archived: {rows_archived}")
    
    # Delete data from invoices table based on the date limit
    if date_limit:
        cursor.execute("DELETE FROM invoices WHERE invoice_date <= ?", (date_limit,))
    else:
        cursor.execute("DELETE FROM invoices")
    
    # Debugging: Check how many rows are left in the invoices table
    cursor.execute("SELECT COUNT(*) FROM invoices")
    rows_left = cursor.fetchone()[0]
    print(f"Rows left in invoices table: {rows_left}")
    
    # Save archive metadata
    cursor.execute("INSERT INTO archive_backups (archive_timestamp) VALUES (?)", (archive_timestamp,))
    
    conn.commit()
    conn.close()
    
    messagebox.showinfo("Success", f"Data archived successfully for {period.replace('_', ' ')}!")
    refresh_invoice_list()

# Refresh Backup List in View Archived Tab
def refresh_backup_list():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT archive_timestamp FROM archive_backups ORDER BY id DESC")
    backups = cursor.fetchall()
    conn.close()
    
    # Clear existing options in the dropdown
    backup_dropdown['values'] = [backup[0] for backup in backups]
    
    # Select the first backup by default (if available)
    if backups:
        backup_dropdown.set(backups[0][0])
        view_archived_data(backups[0][0])  # Show entries for the first backup

# View Archived Data for Selected Backup
def view_archived_data(archive_timestamp):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Fetch archived invoices for the selected timestamp
    cursor.execute("SELECT id, invoice_number, customer, total, invoice_date FROM archived_invoices WHERE archive_timestamp = ?", (archive_timestamp,))
    archived_invoices = cursor.fetchall()
    conn.close()
    
    # Clear existing rows in the treeview
    for row in archived_tree.get_children():
        archived_tree.delete(row)
    
    # Insert archived rows
    for invoice in archived_invoices:
        archived_tree.insert("", "end", values=invoice)

# Reset Search Filters in Invoice History Tab
def reset_filters():
    invoice_number_filter_entry.delete(0, tk.END)
    customer_filter_entry.delete(0, tk.END)
    total_filter_entry.delete(0, tk.END)
    date_filter_entry.delete(0, tk.END)
    refresh_invoice_list()

def fetch_non_archived_data():
    conn = sqlite3.connect(db_path)
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

# Plot Total Sales (Month-wise and Year-wise)
def plot_total_sales():
    invoices_df, _ = fetch_non_archived_data()
    
    # Convert date_time to datetime
    invoices_df["date_time"] = pd.to_datetime(invoices_df["date_time"])
    
    # Extract month and year
    invoices_df["month"] = invoices_df["date_time"].dt.to_period("M")
    invoices_df["year"] = invoices_df["date_time"].dt.to_period("Y")
    
    # Group by month and year
    monthly_sales = invoices_df.groupby("month")["total"].sum()
    yearly_sales = invoices_df.groupby("year")["total"].sum()
    
    # Plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    monthly_sales.plot(kind="bar", ax=ax1, color="skyblue")
    ax1.set_title("Monthly Sales")
    ax1.set_xlabel("Month")
    ax1.set_ylabel("Total Sales")
    
    yearly_sales.plot(kind="bar", ax=ax2, color="lightgreen")
    ax2.set_title("Yearly Sales")
    ax2.set_xlabel("Year")
    ax2.set_ylabel("Total Sales")
    
    plt.tight_layout()
    plt.show()

# Plot Total Amount of Selling (Item-wise)
def plot_item_wise_sales():
    _, items_df = fetch_non_archived_data()
    
    # Calculate total amount for each product
    items_df["total_amount"] = items_df["quantity"] * items_df["price"]
    item_wise_sales = items_df.groupby("product")["total_amount"].sum()
    
    # Plot
    plt.figure(figsize=(8, 5))
    item_wise_sales.plot(kind="bar", color="orange")
    plt.title("Item-wise Sales")
    plt.xlabel("Product")
    plt.ylabel("Total Amount")
    plt.tight_layout()
    plt.show()

# Plot Highest and Lowest Amount
def plot_highest_lowest():
    invoices_df, _ = fetch_non_archived_data()
    
    # Find highest and lowest sales
    highest = invoices_df["total"].max()
    lowest = invoices_df["total"].min()
    
    # Plot
    plt.figure(figsize=(6, 4))
    plt.bar(["Highest", "Lowest"], [highest, lowest], color=["green", "red"])
    plt.title("Highest and Lowest Sales")
    plt.ylabel("Amount")
    plt.tight_layout()
    plt.show()

# Plot Monthly Increase in Sales
def plot_monthly_increase():
    invoices_df, _ = fetch_non_archived_data()
    
    # Convert date_time to datetime
    invoices_df["date_time"] = pd.to_datetime(invoices_df["date_time"])
    
    # Extract month
    invoices_df["month"] = invoices_df["date_time"].dt.to_period("M")
    
    # Group by month
    monthly_sales = invoices_df.groupby("month")["total"].sum()
    
    # Calculate monthly increase
    monthly_increase = monthly_sales.diff().fillna(0)
    
    # Plot
    plt.figure(figsize=(8, 5))
    monthly_increase.plot(kind="bar", color="purple")
    plt.title("Monthly Increase in Sales")
    plt.xlabel("Month")
    plt.ylabel("Increase in Sales")
    plt.tight_layout()
    plt.show()

# Upload Logo
def upload_logo():
    file_path = filedialog.askopenfilename(
        title="Select Organization Logo",
        filetypes=[("Image Files", "*.jpg *.jpeg *.png *svg")]
    )
    if file_path:
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
        if file_size > 2:
            messagebox.showerror("Error", "File size must be less than 2 MB!")
            return
        with open(file_path, "rb") as file:
            global org_logo_blob
            org_logo_blob = file.read()  # Store the binary data globally
        
        # Display the file name in the org_logo_entry widget
        org_logo_entry.config(state="normal")
        org_logo_entry.delete(0, tk.END)
        org_logo_entry.insert(0, os.path.basename(file_path))  # Show only the file name
        org_logo_entry.config(state="readonly")

# GUI Setup
if tk:
    root = tk.Tk()
    root.title("Invoice Generator")
    root.geometry("1200x800")
    root.configure(bg=BACKGROUND_COLOR)
    
    init_db()
    
    tab_control = ttk.Notebook(root)
    tab_org_info = ttk.Frame(tab_control)
    tab_invoice = ttk.Frame(tab_control)
    tab_history = ttk.Frame(tab_control)
    tab_operations = ttk.Frame(tab_control)
    tab_view_archived = ttk.Frame(tab_control)
    tab_analysis = ttk.Frame(tab_control)
    tab_control.add(tab_org_info, text="Organization Info")
    tab_control.add(tab_invoice, text="Create Invoice")
    tab_control.add(tab_history, text="Invoice History")
    tab_control.add(tab_operations, text="Operations")
    tab_control.add(tab_view_archived, text="View Archived")
    tab_control.add(tab_analysis, text="Analysis")
    tab_control.pack(expand=1, fill="both")
    
    # Make selected tab bold
    def on_tab_changed(event):
        selected_tab = tab_control.select()
        # for tab in tab_control.tabs():
        #     tab_control.tab(tab, font=("Arial", 10))  # Reset font for all tabs
        # tab_control.tab(selected_tab, font=("Arial", 10, "bold"))  # Bold selected tab
        
        if selected_tab == tab_view_archived._w:
            refresh_backup_list()
        elif selected_tab == tab_history._w:
            refresh_invoice_list()
        elif selected_tab == tab_org_info._w:
            load_org_info()  # Load organization info when the tab is opened
    
    tab_control.bind("<<NotebookTabChanged>>", on_tab_changed)
    
    # Organization Info Tab (Centered Controls)
    org_frame = tk.Frame(tab_org_info, bg=BACKGROUND_COLOR)
    org_frame.pack(fill="both", padx=20, pady=20)

    # Organization Name
    tk.Label(org_frame, text="Organization Name*:", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).grid(row=0, column=0, padx=5, pady=5, sticky="w")
    org_name_entry = tk.Entry(org_frame, width=50, font=FONT, bg=ENTRY_BG)
    org_name_entry.grid(row=0, column=1, padx=5, pady=5)

    # GST Number
    tk.Label(org_frame, text="GST Number:", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).grid(row=1, column=0, padx=5, pady=5, sticky="w")
    gst_entry = tk.Entry(org_frame, width=50, font=FONT, bg=ENTRY_BG)
    gst_entry.grid(row=1, column=1, padx=5, pady=5)

    # TIN Number
    tk.Label(org_frame, text="TIN Number:", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).grid(row=2, column=0, padx=5, pady=5, sticky="w")
    tin_entry = tk.Entry(org_frame, width=50, font=FONT, bg=ENTRY_BG)
    tin_entry.grid(row=2, column=1, padx=5, pady=5)

    # Organization Address
    tk.Label(org_frame, text="Organization Address:", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).grid(row=3, column=0, padx=5, pady=5, sticky="w")
    org_address_text = tk.Text(org_frame, width=50, height=5, font=FONT, bg=ENTRY_BG)
    org_address_text.grid(row=3, column=1, padx=5, pady=5)

    # Organization Email ID
    tk.Label(org_frame, text="Organization Email ID:", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).grid(row=4, column=0, padx=5, pady=5, sticky="w")
    org_email_entry = tk.Entry(org_frame, width=50, font=FONT, bg=ENTRY_BG)
    org_email_entry.grid(row=4, column=1, padx=5, pady=5)

    # Organization Contact Number
    tk.Label(org_frame, text="Organization Contact Number:", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).grid(row=5, column=0, padx=5, pady=5, sticky="w")
    org_contact_entry = tk.Entry(org_frame, width=50, font=FONT, bg=ENTRY_BG)
    org_contact_entry.grid(row=5, column=1, padx=5, pady=5)

    # Organization Logo
    tk.Label(org_frame, text="Organization Logo:", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).grid(row=6, column=0, padx=5, pady=5, sticky="w")
    org_logo_entry = tk.Entry(org_frame, width=50, font=FONT, bg=ENTRY_BG, state="readonly")
    org_logo_entry.grid(row=6, column=1, padx=5, pady=5)
    tk.Button(org_frame, text="Upload Logo", command=upload_logo, bg="#6eaaf0", fg="white", font=BUTTON_FONT, activebackground=BUTTON_HOVER_COLOR).grid(row=6, column=2, padx=5, pady=5)

    # Save Organization Info Button
    tk.Button(org_frame, text="Save Organization Info", command=save_org_info, bg=BUTTON_COLOR, fg="white", font=BUTTON_FONT, activebackground=BUTTON_HOVER_COLOR).grid(row=7, column=1, padx=5, pady=10, sticky="e")
    load_org_info()
    
    # Required Field Label
    tk.Label(org_frame, text="* Required Fields", bg=BACKGROUND_COLOR, font=FONT, fg="red").grid(row=9, column=0, padx=5, pady=5, sticky="w")
    

    # Create Invoice Tab
    customer_frame = tk.Frame(tab_invoice, bg=BACKGROUND_COLOR)
    customer_frame.pack(fill="x", padx=20, pady=10)
    
    # Customer Name
    tk.Label(customer_frame, text="Customer Name*:", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).pack(side="left", padx=5)
    customer_entry = tk.Entry(customer_frame, width=50, font=FONT, bg=ENTRY_BG)
    customer_entry.pack(side="left", padx=5, fill="x", expand=True)

    # Calendar for Invoice Date
    tk.Label(customer_frame, text="Invoice Date:", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).pack(side="left", padx=5)
    invoice_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))  # Default to current date and time
    invoice_date_entry = tk.Entry(customer_frame, textvariable=invoice_date_var, width=20, font=FONT, bg=ENTRY_BG)
    invoice_date_entry.pack(side="left", padx=5)

    # Calendar Button
    def open_calendar():
        def set_date():
            selected_date = cal.selection_get()
            invoice_date_var.set(selected_date.strftime("%Y-%m-%d %H:%M:%S"))
            top.destroy()

        top = tk.Toplevel(root)
        top.title("Select Invoice Date")
        cal = Calendar(top, selectmode="day", date_pattern="yyyy-mm-dd")
        cal.pack(padx=10, pady=10)
        tk.Button(top, text="OK", command=set_date, bg=BUTTON_COLOR, fg="white", font=BUTTON_FONT).pack(pady=10)

    tk.Button(customer_frame, text="📅", command=open_calendar, bg="#f0f0f0", fg="black", font=BUTTON_FONT).pack(side="left", padx=5)

    # Optional Fields (Customer Email and Contact Number)
    optional_frame = tk.Frame(tab_invoice, bg=BACKGROUND_COLOR)
    optional_frame.pack(fill="x", padx=20, pady=10)
    
    tk.Label(optional_frame, text="Customer Email:", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).pack(side="left", padx=5)
    customer_email_entry = tk.Entry(optional_frame, width=90, font=FONT, bg=ENTRY_BG)
    customer_email_entry.pack(side="left", padx=5)

    tk.Label(optional_frame, text="Customer Contact:", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).pack(side="left", padx=5)
    customer_contact_entry = tk.Entry(optional_frame, width=30, font=FONT, bg=ENTRY_BG)
    customer_contact_entry.pack(side="left", padx=5)

    product_frame = tk.Frame(tab_invoice, bg=BACKGROUND_COLOR)
    product_frame.pack(fill="x", padx=20, pady=10)
    
    tk.Label(product_frame, text="Product", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).grid(row=0, column=0, padx=5)
    tk.Label(product_frame, text="Quantity", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).grid(row=0, column=1, padx=5)
    tk.Label(product_frame, text="Price", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).grid(row=0, column=2, padx=5)
    
    product_entry = tk.Entry(product_frame, width=50, font=FONT, bg=ENTRY_BG)
    product_entry.grid(row=1, column=0, padx=5)
    quantity_entry = tk.Entry(product_frame, width=10, font=FONT, bg=ENTRY_BG)
    quantity_entry.grid(row=1, column=1, padx=5)
    price_entry = tk.Entry(product_frame, width=10, font=FONT, bg=ENTRY_BG)
    price_entry.grid(row=1, column=2, padx=5)
    
    tk.Button(product_frame, text="Add Product", command=add_product, bg=BUTTON_COLOR, fg="white", font=BUTTON_FONT, activebackground=BUTTON_HOVER_COLOR).grid(row=1, column=3, padx=5)
    
    product_tree = ttk.Treeview(tab_invoice, columns=("Product", "Quantity", "Price"), show="headings", height=10)
    product_tree.heading("Product", text="Product")
    product_tree.heading("Quantity", text="Quantity")
    product_tree.heading("Price", text="Price")
    product_tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
    button_frame = tk.Frame(tab_invoice, bg=BACKGROUND_COLOR)
    button_frame.pack(fill="x", padx=20, pady=10)
    
    tk.Button(button_frame, text="Edit", command=edit_product, bg="#FFA500", fg="white", font=BUTTON_FONT, activebackground="#FF8C00").pack(side="left", padx=5)
    tk.Button(button_frame, text="Delete", command=delete_product, bg="#FF0000", fg="white", font=BUTTON_FONT, activebackground="#CC0000").pack(side="left", padx=5)
    
    total_label = tk.Label(button_frame, text="Total: ₹0.00", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR)
    total_label.pack(side="right", padx=10)
    
    # Create a frame to hold the buttons in the same row
    button_frame = tk.Frame(tab_invoice, bg=BACKGROUND_COLOR)
    button_frame.pack(pady=10)

    # Add Reset button to the frame
    tk.Button(button_frame, text="Reset", command=reset_invoice_tab, bg="#6eaaf0", fg="white", font=BUTTON_FONT, activebackground="#CC0000").pack(side="left", padx=5)

    # Add Save Invoice button to the frame
    tk.Button(button_frame, text="Save Invoice", command=save_invoice, bg=BUTTON_COLOR, fg="white", font=BUTTON_FONT, activebackground=BUTTON_HOVER_COLOR).pack(side="left", padx=5)
    
    # Invoice History Tab
    history_frame = tk.Frame(tab_history, bg=BACKGROUND_COLOR)
    history_frame.pack(fill="both", padx=20, pady=20)
    
    # Filter Section
    filter_frame = tk.Frame(history_frame, bg=BACKGROUND_COLOR)
    filter_frame.pack(fill="x", padx=10, pady=10)
    
    tk.Label(filter_frame, text="Invoice Number:", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).grid(row=0, column=0, padx=5, pady=5)
    invoice_number_filter_entry = tk.Entry(filter_frame, width=20, font=FONT, bg=ENTRY_BG)
    invoice_number_filter_entry.grid(row=0, column=1, padx=5, pady=5)
    
    tk.Label(filter_frame, text="Customer:", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).grid(row=0, column=2, padx=5, pady=5)
    customer_filter_entry = tk.Entry(filter_frame, width=20, font=FONT, bg=ENTRY_BG)
    customer_filter_entry.grid(row=0, column=3, padx=5, pady=5)
    
    tk.Label(filter_frame, text="Total:", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).grid(row=0, column=4, padx=5, pady=5)
    total_filter_entry = tk.Entry(filter_frame, width=10, font=FONT, bg=ENTRY_BG)
    total_filter_entry.grid(row=0, column=5, padx=5, pady=5)
    
    tk.Label(filter_frame, text="Date:", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).grid(row=0, column=6, padx=5, pady=5)
    date_filter_entry = tk.Entry(filter_frame, width=15, font=FONT, bg=ENTRY_BG)
    date_filter_entry.grid(row=0, column=7, padx=5, pady=5)
    
    tk.Button(filter_frame, text="Search", command=filter_invoices, bg=BUTTON_COLOR, fg="white", font=BUTTON_FONT, activebackground=BUTTON_HOVER_COLOR).grid(row=0, column=8, padx=5, pady=5)
    tk.Button(filter_frame, text="Reset", command=reset_filters, bg="#6eaaf0", fg="white", font=BUTTON_FONT, activebackground="#CC0000").grid(row=0, column=9, padx=5, pady=5)
    
    # Invoice History Treeview
    history_tree = ttk.Treeview(history_frame, columns=("ID", "Invoice Number", "Customer", "Total", "Invoice Date", "Customer Email", "Customer Contact"), show="headings", height=15)
    history_tree.heading("ID", text="ID")
    history_tree.heading("Invoice Number", text="Invoice Number")
    history_tree.heading("Customer", text="Customer")
    history_tree.heading("Total", text="Total")
    history_tree.heading("Invoice Date", text="Invoice Date")
    history_tree.heading("Customer Email", text="Customer Email")
    history_tree.heading("Customer Contact", text="Customer Contact")
    history_tree.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Bind double-click event to open PDF
    history_tree.bind("<Double-1>", open_invoice_pdf)
    
    # Operations Tab
    operations_frame = tk.Frame(tab_operations, bg=BACKGROUND_COLOR)
    operations_frame.pack(fill="both", padx=20, pady=20)
    
    tk.Label(operations_frame, text="Archive Data:", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).pack(pady=10)
    
    tk.Button(operations_frame, text="Archive Last Year Data", command=lambda: archive_data("last_year"), bg=BUTTON_COLOR, fg="white", font=BUTTON_FONT, activebackground=BUTTON_HOVER_COLOR).pack(fill="x", padx=20, pady=5)
    tk.Button(operations_frame, text="Archive Last 6 Months Data", command=lambda: archive_data("last_6_months"), bg=BUTTON_COLOR, fg="white", font=BUTTON_FONT, activebackground=BUTTON_HOVER_COLOR).pack(fill="x", padx=20, pady=5)
    tk.Button(operations_frame, text="Archive Last 1 Month Data", command=lambda: archive_data("last_1_month"), bg=BUTTON_COLOR, fg="white", font=BUTTON_FONT, activebackground=BUTTON_HOVER_COLOR).pack(fill="x", padx=20, pady=5)
    tk.Button(operations_frame, text="Archive All Data", command=lambda: archive_data("all_data"), bg=BUTTON_COLOR, fg="white", font=BUTTON_FONT, activebackground=BUTTON_HOVER_COLOR).pack(fill="x", padx=20, pady=5)
    
    # View Archived Tab
    view_archived_frame = tk.Frame(tab_view_archived, bg=BACKGROUND_COLOR)
    view_archived_frame.pack(fill="both", padx=20, pady=20)
    
    # Dropdown for Archived Backups
    backup_dropdown_frame = tk.Frame(view_archived_frame, bg=BACKGROUND_COLOR)
    backup_dropdown_frame.pack(fill="x", padx=10, pady=10)
    
    tk.Label(backup_dropdown_frame, text="Select Backup:", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).pack(side="left", padx=5)
    
    backup_dropdown = ttk.Combobox(backup_dropdown_frame, font=FONT, state="readonly")
    backup_dropdown.pack(side="left", padx=5, fill="x", expand=True)
    backup_dropdown.bind("<<ComboboxSelected>>", lambda event: view_archived_data(backup_dropdown.get()))
    
    # Archived Invoices Treeview
    archived_tree = ttk.Treeview(view_archived_frame, columns=("ID", "Invoice Number", "Customer", "Total", "Date"), show="headings", height=15)
    archived_tree.heading("ID", text="ID")
    archived_tree.heading("Invoice Number", text="Invoice Number")
    archived_tree.heading("Customer", text="Customer")
    archived_tree.heading("Total", text="Total")
    archived_tree.heading("Date", text="Date")
    archived_tree.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Analysis Tab
    analysis_frame = tk.Frame(tab_analysis, bg=BACKGROUND_COLOR)
    analysis_frame.pack(fill="both", padx=20, pady=20)
    
    tk.Button(analysis_frame, text="Total Sales (Month-wise and Year-wise)", command=plot_total_sales, bg=BUTTON_COLOR, fg="white", font=BUTTON_FONT, activebackground=BUTTON_HOVER_COLOR).pack(fill="x", padx=20, pady=5)
    tk.Button(analysis_frame, text="Total Amount of Selling (Item-wise)", command=plot_item_wise_sales, bg=BUTTON_COLOR, fg="white", font=BUTTON_FONT, activebackground=BUTTON_HOVER_COLOR).pack(fill="x", padx=20, pady=5)
    tk.Button(analysis_frame, text="Highest and Lowest Amount", command=plot_highest_lowest, bg=BUTTON_COLOR, fg="white", font=BUTTON_FONT, activebackground=BUTTON_HOVER_COLOR).pack(fill="x", padx=20, pady=5)
    tk.Button(analysis_frame, text="Monthly Increase in Sales", command=plot_monthly_increase, bg=BUTTON_COLOR, fg="white", font=BUTTON_FONT, activebackground=BUTTON_HOVER_COLOR).pack(fill="x", padx=20, pady=5)

    root.mainloop()
else:
    init_db()
    print("Running in non-GUI mode. Use database functions directly.")