import os
import sys
from windows.main_window import MainWindow

if __name__ == "__main__":
    if getattr(sys, "frozen", False):
        os.environ["PYTHONVERBOSE"] = "0"
        os.environ["PYTHONOPTIMIZE"] = "2"

    app = MainWindow()
    app.mainloop()
