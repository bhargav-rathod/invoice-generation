import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from database import init_db
from invoice_operations import save_invoice, reset_invoice_tab, add_product, edit_product, delete_product, update_total, open_invoice_pdf, filter_invoices, reset_filters, archive_data, refresh_backup_list, view_archived_data
from organization_operations import save_org_info, load_org_info, upload_logo
from analysis import plot_total_sales, plot_item_wise_sales, plot_highest_lowest, plot_monthly_increase
from utils import STORAGE_DIR, DB_PATH, FONT, HEADER_FONT, BUTTON_FONT, BACKGROUND_COLOR, BUTTON_COLOR, BUTTON_HOVER_COLOR, TEXT_COLOR, ENTRY_BG, TREEVIEW_BG, TREEVIEW_HEADER_BG, TREEVIEW_HEADER_FG
from datetime import datetime, timedelta
from tkcalendar import Calendar

def start_gui():
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
    
    # Organization Info Tab
    org_frame = tk.Frame(tab_org_info, bg=BACKGROUND_COLOR)
    org_frame.pack(fill="both", padx=20, pady=20)

    tk.Label(org_frame, text="Organization Name*:", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).grid(row=0, column=0, padx=5, pady=5, sticky="w")
    org_name_entry = tk.Entry(org_frame, width=50, font=FONT, bg=ENTRY_BG)
    org_name_entry.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(org_frame, text="GST Number:", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).grid(row=1, column=0, padx=5, pady=5, sticky="w")
    gst_entry = tk.Entry(org_frame, width=50, font=FONT, bg=ENTRY_BG)
    gst_entry.grid(row=1, column=1, padx=5, pady=5)

    tk.Label(org_frame, text="TIN Number:", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).grid(row=2, column=0, padx=5, pady=5, sticky="w")
    tin_entry = tk.Entry(org_frame, width=50, font=FONT, bg=ENTRY_BG)
    tin_entry.grid(row=2, column=1, padx=5, pady=5)

    tk.Label(org_frame, text="Organization Address:", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).grid(row=3, column=0, padx=5, pady=5, sticky="w")
    org_address_text = tk.Text(org_frame, width=50, height=5, font=FONT, bg=ENTRY_BG)
    org_address_text.grid(row=3, column=1, padx=5, pady=5)

    tk.Label(org_frame, text="Organization Email ID:", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).grid(row=4, column=0, padx=5, pady=5, sticky="w")
    org_email_entry = tk.Entry(org_frame, width=50, font=FONT, bg=ENTRY_BG)
    org_email_entry.grid(row=4, column=1, padx=5, pady=5)

    tk.Label(org_frame, text="Organization Contact Number:", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).grid(row=5, column=0, padx=5, pady=5, sticky="w")
    org_contact_entry = tk.Entry(org_frame, width=50, font=FONT, bg=ENTRY_BG)
    org_contact_entry.grid(row=5, column=1, padx=5, pady=5)

    tk.Label(org_frame, text="Organization Logo:", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).grid(row=6, column=0, padx=5, pady=5, sticky="w")
    org_logo_entry = tk.Entry(org_frame, width=50, font=FONT, bg=ENTRY_BG, state="readonly")
    org_logo_entry.grid(row=6, column=1, padx=5, pady=5)
    tk.Button(org_frame, text="Upload Logo", command=lambda: upload_logo(org_logo_entry), bg="#6eaaf0", fg="white", font=BUTTON_FONT, activebackground=BUTTON_HOVER_COLOR).grid(row=6, column=2, padx=5, pady=5)

    tk.Button(org_frame, text="Save Organization Info", command=lambda: save_org_info(org_name_entry, gst_entry, tin_entry, org_address_text, org_email_entry, org_contact_entry), bg=BUTTON_COLOR, fg="white", font=BUTTON_FONT, activebackground=BUTTON_HOVER_COLOR).grid(row=7, column=1, padx=5, pady=10, sticky="e")
    load_org_info(org_name_entry, gst_entry, tin_entry, org_address_text, org_email_entry, org_contact_entry)
    
    tk.Label(org_frame, text="* Required Fields", bg=BACKGROUND_COLOR, font=FONT, fg="red").grid(row=9, column=0, padx=5, pady=5, sticky="w")

    # Create Invoice Tab
    customer_frame = tk.Frame(tab_invoice, bg=BACKGROUND_COLOR)
    customer_frame.pack(fill="x", padx=20, pady=10)
    
    tk.Label(customer_frame, text="Customer Name*:", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).pack(side="left", padx=5)
    customer_entry = tk.Entry(customer_frame, width=50, font=FONT, bg=ENTRY_BG)
    customer_entry.pack(side="left", padx=5, fill="x", expand=True)

    tk.Label(customer_frame, text="Invoice Date:", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).pack(side="left", padx=5)
    invoice_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    invoice_date_entry = tk.Entry(customer_frame, textvariable=invoice_date_var, width=20, font=FONT, bg=ENTRY_BG)
    invoice_date_entry.pack(side="left", padx=5)

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
    
    tk.Button(product_frame, text="Add Product", command=lambda: add_product(product_entry, quantity_entry, price_entry, product_tree, total_label), bg=BUTTON_COLOR, fg="white", font=BUTTON_FONT, activebackground=BUTTON_HOVER_COLOR).grid(row=1, column=3, padx=5)
    
    product_tree = ttk.Treeview(tab_invoice, columns=("Product", "Quantity", "Price"), show="headings", height=10)
    product_tree.heading("Product", text="Product")
    product_tree.heading("Quantity", text="Quantity")
    product_tree.heading("Price", text="Price")
    product_tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
    button_frame = tk.Frame(tab_invoice, bg=BACKGROUND_COLOR)
    button_frame.pack(fill="x", padx=20, pady=10)
    
    tk.Button(button_frame, text="Edit", command=lambda: edit_product(product_tree, product_entry, quantity_entry, price_entry, total_label), bg="#FFA500", fg="white", font=BUTTON_FONT, activebackground="#FF8C00").pack(side="left", padx=5)
    tk.Button(button_frame, text="Delete", command=lambda: delete_product(product_tree, total_label), bg="#FF0000", fg="white", font=BUTTON_FONT, activebackground="#CC0000").pack(side="left", padx=5)
    
    total_label = tk.Label(button_frame, text="Total: ₹0.00", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR)
    total_label.pack(side="right", padx=10)
    
    button_frame = tk.Frame(tab_invoice, bg=BACKGROUND_COLOR)
    button_frame.pack(pady=10)

    tk.Button(button_frame, text="Reset", command=lambda: reset_invoice_tab(customer_entry, customer_email_entry, customer_contact_entry, product_entry, quantity_entry, price_entry, product_tree, total_label, invoice_date_var), bg="#6eaaf0", fg="white", font=BUTTON_FONT, activebackground="#CC0000").pack(side="left", padx=5)
    tk.Button(button_frame, text="Save Invoice", command=lambda: save_invoice(customer_entry, customer_email_entry, customer_contact_entry, product_tree, invoice_date_var, total_label, product_entry, quantity_entry, price_entry), bg=BUTTON_COLOR, fg="white", font=BUTTON_FONT, activebackground=BUTTON_HOVER_COLOR).pack(side="left", padx=5)
    
    # Invoice History Tab
    history_frame = tk.Frame(tab_history, bg=BACKGROUND_COLOR)
    history_frame.pack(fill="both", padx=20, pady=20)
    
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
    
    tk.Button(filter_frame, text="Search", command=lambda: filter_invoices(invoice_number_filter_entry, customer_filter_entry, total_filter_entry, date_filter_entry, history_tree), bg=BUTTON_COLOR, fg="white", font=BUTTON_FONT, activebackground=BUTTON_HOVER_COLOR).grid(row=0, column=8, padx=5, pady=5)
    tk.Button(filter_frame, text="Reset", command=lambda: reset_filters(invoice_number_filter_entry, customer_filter_entry, total_filter_entry, date_filter_entry, history_tree), bg="#6eaaf0", fg="white", font=BUTTON_FONT, activebackground="#CC0000").grid(row=0, column=9, padx=5, pady=5)
    
    history_tree = ttk.Treeview(history_frame, columns=("ID", "Invoice Number", "Customer", "Total", "Invoice Date", "Customer Email", "Customer Contact"), show="headings", height=15)
    history_tree.heading("ID", text="ID")
    history_tree.heading("Invoice Number", text="Invoice Number")
    history_tree.heading("Customer", text="Customer")
    history_tree.heading("Total", text="Total")
    history_tree.heading("Invoice Date", text="Invoice Date")
    history_tree.heading("Customer Email", text="Customer Email")
    history_tree.heading("Customer Contact", text="Customer Contact")
    history_tree.pack(fill="both", expand=True, padx=10, pady=10)
    
    history_tree.bind("<Double-1>", lambda event: open_invoice_pdf(history_tree))
    
    # Operations Tab
    operations_frame = tk.Frame(tab_operations, bg=BACKGROUND_COLOR)
    operations_frame.pack(fill="both", padx=20, pady=20)
    
    tk.Label(operations_frame, text="Archive Data:", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).pack(pady=10)
    
    tk.Button(operations_frame, text="Archive Last Year Data", command=lambda: archive_data("last_year", history_tree), bg=BUTTON_COLOR, fg="white", font=BUTTON_FONT, activebackground=BUTTON_HOVER_COLOR).pack(fill="x", padx=20, pady=5)
    tk.Button(operations_frame, text="Archive Last 6 Months Data", command=lambda: archive_data("last_6_months", history_tree), bg=BUTTON_COLOR, fg="white", font=BUTTON_FONT, activebackground=BUTTON_HOVER_COLOR).pack(fill="x", padx=20, pady=5)
    tk.Button(operations_frame, text="Archive Last 1 Month Data", command=lambda: archive_data("last_1_month", history_tree), bg=BUTTON_COLOR, fg="white", font=BUTTON_FONT, activebackground=BUTTON_HOVER_COLOR).pack(fill="x", padx=20, pady=5)
    tk.Button(operations_frame, text="Archive All Data", command=lambda: archive_data("all_data", history_tree), bg=BUTTON_COLOR, fg="white", font=BUTTON_FONT, activebackground=BUTTON_HOVER_COLOR).pack(fill="x", padx=20, pady=5)
    
    # View Archived Tab
    view_archived_frame = tk.Frame(tab_view_archived, bg=BACKGROUND_COLOR)
    view_archived_frame.pack(fill="both", padx=20, pady=20)
    
    backup_dropdown_frame = tk.Frame(view_archived_frame, bg=BACKGROUND_COLOR)
    backup_dropdown_frame.pack(fill="x", padx=10, pady=10)
    
    tk.Label(backup_dropdown_frame, text="Select Backup:", bg=BACKGROUND_COLOR, font=FONT, fg=TEXT_COLOR).pack(side="left", padx=5)
    
    backup_dropdown = ttk.Combobox(backup_dropdown_frame, font=FONT, state="readonly")
    backup_dropdown.pack(side="left", padx=5, fill="x", expand=True)
    backup_dropdown.bind("<<ComboboxSelected>>", lambda event: view_archived_data(backup_dropdown.get(), archived_tree))
    
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