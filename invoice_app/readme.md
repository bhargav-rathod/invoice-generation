# Structure

    invoice_app/
    │
    ├── main.py                     # Entry point of the application
    ├── database.py                 # Handles database operations
    ├── gui.py                      # Handles GUI setup and layout
    ├── invoice_operations.py       # Handles invoice-related operations
    ├── organization_operations.py  # Handles organization-related operations
    ├── analysis.py                 # Handles data analysis and plotting
    ├── utils.py                    # Utility functions and constants
    └── storage/                    # Directory for storing invoices and database
        ├── invoices.db             # Database
        └── invoices/               # File Storage

# How to Run the Application
Ensure you have Python installed.

## Install the required libraries:

    - pip install tkinter sqlite3 reportlab matplotlib pandas tkcalendar
    - Place all the files in the invoice_app directory.

## Run the main.py file:
    
    - python main.py
