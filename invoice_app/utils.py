import os

# Constants
STORAGE_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "Invoices")
os.makedirs(STORAGE_DIR, exist_ok=True)
DB_PATH = os.path.join(STORAGE_DIR, "invoices.db")
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