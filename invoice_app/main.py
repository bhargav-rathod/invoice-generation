from gui import start_gui
from database import init_db

if __name__ == "__main__":
    init_db()
    start_gui()