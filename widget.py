from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QApplication
from PyQt6.QtCore import Qt

class DashboardWidget(QWidget):
    def __init__(self, content):
        super().__init__()
        self.setWindowTitle("My Feed")
        
        # Position and resize logic will be handled at the end
        
        # 1. Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 2. Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 3. Content Widget (Container inside ScrollArea)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        
        # 4. Header
        self.header = QLabel("<h1>My Feed</h1>")
        self.header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.header)
        
        # 5. Body
        self.body = QLabel(content)
        self.body.setWordWrap(True)
        self.body.setTextFormat(Qt.TextFormat.MarkdownText)
        self.body.setOpenExternalLinks(True)
        self.body.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content_layout.addWidget(self.body)
        
        # Add stretch to keep content at the top
        self.content_layout.addStretch()
        
        # 6. Set widget to scroll area and add to main layout
        self.scroll_area.setWidget(self.content_widget)
        self.main_layout.addWidget(self.scroll_area)
        
        # 7. Position Top-Right
        self.position_top_right()

    def position_top_right(self):
        screen = QApplication.primaryScreen()
        if screen:
            available_rect = screen.availableGeometry()
            width = 400  # Fixed width
            height = 700 # Initial height
            
            # accessible right edge - width
            x = available_rect.x() + available_rect.width() - width
            y = available_rect.top()
            
            self.setGeometry(x, y, width, height)
        else:
            self.resize(400, 700)

    def update_content(self, content):
        self.body.setText(content)