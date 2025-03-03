import sqlite3
import os
import tkinter as tk
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image
from reportlab.lib.units import inch
from tkinter import messagebox
from utils import STORAGE_DIR, DB_PATH

def save_invoice(customer_entry, customer_email_entry, customer_contact_entry, product_tree, invoice_date_var, total_label, product_entry, quantity_entry, price_entry):
    customer = customer_entry.get()
    if not customer:
        messagebox.showerror("Error", "Customer name is required!")
        return
    
    invoice_number = f"INV-{int(datetime.timestamp(datetime.now()))}"
    invoice_date = invoice_date_var.get()
    
    customer_email = customer_email_entry.get().strip()
    customer_contact = customer_contact_entry.get().strip()
    
    total = 0
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''INSERT INTO invoices 
                      (customer, total, invoice_number, date_time, invoice_date, customer_email, customer_contact) 
                      VALUES (?, ?, ?, ?, ?, ?, ?)''',
                   (customer, total, invoice_number, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                    invoice_date, customer_email, customer_contact))
    
    invoice_id = cursor.lastrowid
    
    for item in product_tree.get_children():
        values = product_tree.item(item, "values")
        quantity, price = int(values[1]), float(values[2])
        item_total = quantity * price
        total += item_total
        cursor.execute("INSERT INTO invoice_items (invoice_id, product, quantity, price) VALUES (?, ?, ?, ?)", 
                       (invoice_id, values[0], quantity, price))
    
    cursor.execute("UPDATE invoices SET total = ? WHERE id = ?", (total, invoice_id))
    conn.commit()
    conn.close()
    
    generate_pdf(invoice_id, customer, total, invoice_number, invoice_date, customer_email, customer_contact)
    
    messagebox.showinfo("Success", "Invoice Saved Successfully!")
    reset_invoice_tab(customer_entry, customer_email_entry, customer_contact_entry, product_entry, quantity_entry, price_entry, product_tree, total_label, invoice_date_var)

def generate_pdf(invoice_id, customer, total, invoice_number, date_time, customer_email="", customer_contact=""):
    filename = f"invoice_{invoice_number}.pdf"
    pdf_path = os.path.join(STORAGE_DIR, filename)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT product, quantity, price FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
    items = cursor.fetchall()
    cursor.execute("SELECT org_name, gst_number, tin_number, org_address, org_email, org_contact, org_logo FROM organization_info ORDER BY date_time DESC LIMIT 1")
    org_info = cursor.fetchone()
    conn.close()
    
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    def add_header(canvas, doc):
        if org_info and org_info[6]:
            logo_image = Image(BytesIO(org_info[6]), width=1.5*inch, height=0.75*inch)
            logo_image.drawOn(canvas, doc.width + doc.leftMargin - 1.5*inch, doc.height + doc.topMargin - 0.25*inch)

    tax_invoice_style = styles["Title"]
    tax_invoice_style.fontSize = 14
    elements.append(Paragraph("TAX/INVOICE", tax_invoice_style))
    elements.append(Spacer(1, 12))
    
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
    
    invoice_style = styles["Heading2"]
    invoice_style.fontSize = 10
    invoice_text = f"Invoice Number: {invoice_number}<br/>Customer: {customer}<br/>"
    
    if customer_email:
        invoice_text += f"Email: {customer_email}<br/>"
    if customer_contact:
        invoice_text += f"Contact: {customer_contact}<br/>"
    
    invoice_text += f"<align right>Date: {date_time}</align>"
    elements.append(Paragraph(invoice_text, invoice_style))
    elements.append(Spacer(1, 12))
    
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
    
    doc.build(elements, onFirstPage=add_header, onLaterPages=add_header)
    
    messagebox.showinfo("PDF Generated", f"Invoice saved as {filename}")
    os.startfile(pdf_path)

def add_product(product_entry, quantity_entry, price_entry, product_tree, total_label):
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
    update_total(product_tree, total_label)

def edit_product(product_tree, product_entry, quantity_entry, price_entry, total_label):
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
    update_total(product_tree, total_label)

def delete_product(product_tree, total_label):
    selected_item = product_tree.selection()
    if not selected_item:
        messagebox.showerror("Error", "Please select an item to delete.")
        return
    product_tree.delete(selected_item)
    update_total(product_tree, total_label)

def update_total(product_tree, total_label):
    total = 0
    for item in product_tree.get_children():
        values = product_tree.item(item, "values")
        quantity, price = int(values[1]), float(values[2])
        total += quantity * price
    total_label.config(text=f"Total: ₹{total:.2f}")

def open_invoice_pdf(history_tree):
    selected_item = history_tree.selection()
    if not selected_item:
        return
    invoice_data = history_tree.item(selected_item, "values")
    invoice_number = invoice_data[1]
    pdf_path = os.path.join(STORAGE_DIR, f"invoice_{invoice_number}.pdf")
    if os.path.exists(pdf_path):
        os.startfile(pdf_path)
    else:
        messagebox.showerror("Error", "Invoice PDF not found!")

def filter_invoices(invoice_number_filter_entry, customer_filter_entry, total_filter_entry, date_filter_entry, history_tree):
    invoice_number = invoice_number_filter_entry.get().strip()
    customer = customer_filter_entry.get().strip()
    total = total_filter_entry.get().strip()
    date = date_filter_entry.get().strip()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = "SELECT id, invoice_number, customer, total, date_time FROM invoices WHERE 1=1"
    
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
    
    for row in history_tree.get_children():
        history_tree.delete(row)
    
    for invoice in invoices:
        history_tree.insert("", "end", values=invoice)

def refresh_invoice_list(history_tree):
    for row in history_tree.get_children():
        history_tree.delete(row)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, invoice_number, customer, total, invoice_date, customer_email, customer_contact FROM invoices")
    invoices = cursor.fetchall()
    conn.close()
    
    for invoice in invoices:
        history_tree.insert("", "end", values=invoice)


def reset_filters(invoice_number_filter_entry, customer_filter_entry, total_filter_entry, date_filter_entry, history_tree):
    invoice_number_filter_entry.delete(0, tk.END)
    customer_filter_entry.delete(0, tk.END)
    total_filter_entry.delete(0, tk.END)
    date_filter_entry.delete(0, tk.END)
    refresh_invoice_list(history_tree)

def archive_data(period, history_tree):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    archive_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
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
    
    if date_limit:
        cursor.execute(f'''INSERT INTO archived_invoices (customer, total, invoice_number, invoice_date, archive_timestamp)
                          SELECT customer, total, invoice_number, invoice_date, ? FROM invoices
                          WHERE invoice_date <= ?''',
                      (archive_timestamp, date_limit))
    else:
        cursor.execute(f'''INSERT INTO archived_invoices (customer, total, invoice_number, invoice_date, archive_timestamp)
                          SELECT customer, total, invoice_number, invoice_date, ? FROM invoices''',
                      (archive_timestamp,))
    
    if date_limit:
        cursor.execute("DELETE FROM invoices WHERE invoice_date <= ?", (date_limit,))
    else:
        cursor.execute("DELETE FROM invoices")
    
    cursor.execute("INSERT INTO archive_backups (archive_timestamp) VALUES (?)", (archive_timestamp,))
    
    conn.commit()
    conn.close()
    
    messagebox.showinfo("Success", f"Data archived successfully for {period.replace('_', ' ')}!")
    refresh_invoice_list(history_tree)

def refresh_backup_list(backup_dropdown):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT archive_timestamp FROM archive_backups ORDER BY id DESC")
    backups = cursor.fetchall()
    conn.close()
    
    backup_dropdown['values'] = [backup[0] for backup in backups]
    
    if backups:
        backup_dropdown.set(backups[0][0])
        view_archived_data(backups[0][0], tk.archived_tree)

def view_archived_data(archive_timestamp, archived_tree):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, invoice_number, customer, total, invoice_date FROM archived_invoices WHERE archive_timestamp = ?", (archive_timestamp,))
    archived_invoices = cursor.fetchall()
    conn.close()
    
    for row in archived_tree.get_children():
        archived_tree.delete(row)
    
    for invoice in archived_invoices:
        archived_tree.insert("", "end", values=invoice)

def reset_invoice_tab(customer_entry, customer_email_entry, customer_contact_entry, product_entry, quantity_entry, price_entry, product_tree, total_label, invoice_date_var):
    customer_entry.delete(0, tk.END)
    customer_email_entry.delete(0, tk.END)
    customer_contact_entry.delete(0, tk.END)
    
    product_entry.delete(0, tk.END)
    quantity_entry.delete(0, tk.END)
    price_entry.delete(0, tk.END)
    
    for item in product_tree.get_children():
        product_tree.delete(item)
    
    total_label.config(text="Total: ₹0.00")
    invoice_date_var.set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))