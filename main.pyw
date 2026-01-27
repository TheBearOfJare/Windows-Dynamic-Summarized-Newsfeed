import sys
import os
import datetime
import json
import ctypes
import threading
from PIL import Image

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtCore import QObject, pyqtSignal, QThread, Qt
from PyQt6.QtGui import QIcon, QAction

from gemini import updateFeed
from widget import DashboardWidget

# --- Constants & Paths ---
myappid = 'TheBearOfJare.gemini.newsfeed.1.0'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
    EXE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    EXE_DIR = BASE_DIR

CACHE_FILE = os.path.join(EXE_DIR, "news_cache.json")
ICON_PATH = os.path.join(BASE_DIR, "icon.png")
FEED_INTERVAL = datetime.timedelta(hours=1)

# --- Cache Management ---
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
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump({"content": content, "time": timestamp.isoformat()}, f)
    except Exception as e:
        print(f"Failed to save cache: {e}")

# --- Worker for Background Tasks ---
class NewsWorker(QObject):
    finished = pyqtSignal(str, datetime.datetime)
    error = pyqtSignal(str)

    def __init__(self, override_cache=False):
        super().__init__()
        self.override_cache = override_cache

    def run(self):
        # We can implement specific checking logic here if needed, 
        # but for 'Refresh' we usually just want to force update.
        try:
            print("Fetching new content from GenAI...")
            new_content = updateFeed(EXE_DIR)
            timestamp = datetime.datetime.now()
            save_cache(new_content, timestamp)
            self.finished.emit(new_content, timestamp)
        except Exception as e:
            self.error.emit(str(e))

# --- Main Application Controller ---
class SystemTrayApp(QObject):
    def __init__(self, app):
        super().__init__()
        self.app = app
        
        # Data State
        self.content = "Loading..."
        self.feed_time = None
        
        # Load Cache
        cache = load_cache()
        if cache:
            self.feed_time = cache['time']
            self.content = cache['content']
        else:
            self.feed_time = datetime.datetime.min
            self.content = "No news yet. Click Refresh."

        # UI Components
        self.widget = None
        self.tray_icon = QSystemTrayIcon(QIcon(ICON_PATH), self.app)
        self.setup_tray()
        
        # Threading
        self.thread = None
        self.worker = None

        # Auto-refresh if stale on startup
        if datetime.datetime.now() - self.feed_time > FEED_INTERVAL:
            self.refresh_news()

    def setup_tray(self):
        menu = QMenu()
        
        # Actions
        self.show_action = QAction("Show/Hide", self)
        self.show_action.triggered.connect(self.toggle_widget)
        menu.addAction(self.show_action)

        self.refresh_action = QAction("Refresh", self)
        self.refresh_action.triggered.connect(self.force_refresh)
        menu.addAction(self.refresh_action)

        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(self.quit_app)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)
        
        # Handle clicking the icon itself
        self.tray_icon.activated.connect(self.on_tray_activated)
        
        self.tray_icon.show()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_widget()

    def toggle_widget(self):
        if self.widget and self.widget.isVisible():
            self.widget.hide()
        else:
            self.show_widget()

    def show_widget(self):
        if not self.widget:
            self.widget = DashboardWidget(self.content)
        
        # Always update content before showing, just in case
        self.widget.update_content(self.content)
        
        # Position logic can be handled by the widget itself or here,
        # but usually the widget has its own geometry logic.
        self.widget.show()
        self.widget.raise_()
        self.widget.activateWindow()

    def force_refresh(self):
        print("Manual refresh triggered")
        if self.widget:
            self.widget.update_content("Refreshing news...")
            if not self.widget.isVisible():
                self.show_widget() # Optional: show widget to show loading state
        self.refresh_news(override=True)

    def refresh_news(self, override=False):
        # Prevent multiple concurrent fetches
        if self.thread and self.thread.isRunning():
            print("Fetch already in progress.")
            return

        self.thread = QThread()
        self.worker = NewsWorker(override_cache=override)
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_fetch_finished)
        self.worker.error.connect(self.on_fetch_error)
        
        # Cleanup
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error.connect(self.thread.quit)
        self.worker.error.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        
        self.thread.start()

    def on_fetch_finished(self, content, timestamp):
        print("Fetch complete.")
        self.content = content
        self.feed_time = timestamp
        if self.widget:
            self.widget.update_content(self.content)

    def on_fetch_error(self, error_msg):
        print(f"Fetch error: {error_msg}")
        self.content = f"Error fetching news: {error_msg}"
        if self.widget:
            self.widget.update_content(self.content)

    def quit_app(self):
        self.tray_icon.hide()
        self.app.quit()

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # Ensure icon exists or fallback to avoid crash
    if not os.path.exists(ICON_PATH):
        print(f"Warning: Icon not found at {ICON_PATH}")

    controller = SystemTrayApp(app)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()