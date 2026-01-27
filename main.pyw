import pystray
import ctypes
myappid = 'TheBearOfJare.gemini.newsfeed.1.0' # arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

from PIL import Image, ImageDraw
from gemini import updateFeed
from widget import DashboardWidget
import datetime
import json
import os
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QIcon
import threading

# Determine paths
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app 
    # path into variable _MEIPASS.
    BASE_DIR = sys._MEIPASS
    # The executable folder (where the user put the exe)
    EXE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    EXE_DIR = BASE_DIR

CACHE_FILE = os.path.join(EXE_DIR, "news_cache.json")
feedInterval = datetime.timedelta(seconds=60 * 60)

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                data = json.load(f)
                data['time'] = datetime.datetime.fromisoformat(data['time'])
                return data
        except Exception:
            return None
    return None

def save_cache(content, timestamp):
    with open(CACHE_FILE, "w") as f:
        json.dump({"content": content, "time": timestamp.isoformat()}, f)

app = None
# widget_instance moved to MainController
feedTime = None
content = None
icon = None

class Communicate(QObject):
    update_ui = pyqtSignal(str)
    toggle_visibility = pyqtSignal()

comm = Communicate()

class MainController(QObject):
    def __init__(self):
        super().__init__()
        self.widget_instance = None

    def show_widget(self, content_text):
        print("Showing feed...")
        if self.widget_instance is None:
            self.widget_instance = DashboardWidget(content_text)
        else:
            self.widget_instance.update_content(content_text)
        
        self.widget_instance.show()
        self.widget_instance.raise_() # Bring to front
        self.widget_instance.activateWindow()

    def handle_toggle(self):
        # Check if widget is visible and close it if so
        if self.widget_instance and self.widget_instance.isVisible():
            print("Hiding feed...")
            self.widget_instance.close()
        else:
            # Otherwise start the fetch process
            threading.Thread(target=background_fetch, daemon=True).start()

def background_fetch(override_cache=False):
    global feedTime
    global content

    if datetime.datetime.now() - feedTime > feedInterval or not content or override_cache:
        try:
            print("Fetching new content from Gemini...")
            # Ideally updateFeed shouldn't be too long, or we're blocking this worker thread 
            # (which is better than blocking the tray thread)
            new_content = updateFeed(EXE_DIR)
            content = new_content
            feedTime = datetime.datetime.now()
            save_cache(content, feedTime)
        except Exception as e:
            print(f"Error updating feed: {e}")
            if not content:
                content = "Could not fetch news. Please check your connection and API limits."
    
    comm.update_ui.emit(content)

# Removed handle_toggle function, moved to MainController

def on_clicked(icon, item):
    global app
    if str(item) == "Show/Hide":
        # Signal the main thread to toggle the widget
        comm.toggle_visibility.emit()

    elif str(item) == "Exit":
        icon.stop()
        if app:
            app.quit()

    elif str(item) == "Refresh":
        background_fetch(override_cache=True)
        

def main():
    global app, feedTime, content, icon

    # Init cache
    cache = load_cache()
    if cache:
        feedTime = cache['time']
        content = cache['content']
    else:
        feedTime = datetime.datetime.now() - datetime.timedelta(seconds=60 * 60)
        content = ""

    # Init Qt App
    app = QApplication(sys.argv)
    icon_path = os.path.join(BASE_DIR, "icon.png")
    app.setWindowIcon(QIcon(icon_path))
    app.setQuitOnLastWindowClosed(False) # Keep app running when window is closed
    
    # Init Tray Icon
    image = Image.open(icon_path)
    icon = pystray.Icon("GeminiDash", image, menu=pystray.Menu(
        pystray.MenuItem("Show", on_clicked, default=True),
        pystray.MenuItem("Refresh", on_clicked),
        pystray.MenuItem("Exit", on_clicked)
    ))

    # Initialize Controller and Signals
    # Important: Create controller after app is created to ensure thread affinity with Main Thread
    controller = MainController()
    comm.update_ui.connect(controller.show_widget)
    comm.toggle_visibility.connect(controller.handle_toggle)
    
    # Run pystray in a separate thread
    threading.Thread(target=icon.run, daemon=True).start()

    # Run Qt event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    main()