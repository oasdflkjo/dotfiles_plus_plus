#!/usr/bin/env python
import os
import json
import time
import threading
from datetime import datetime
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy, QHBoxLayout
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QEvent

from widgets.base_widget import BaseWidget, HAS_WIN32_MODULES

# Import IMAP client for Gmail
from imapclient import IMAPClient

class EmailFetcher(QObject):
    """Background worker to fetch emails without blocking the UI"""
    email_count_updated = pyqtSignal(int)
    
    def __init__(self, email=None, password=None):
        super().__init__()
        self.email = email or os.environ.get("GMAIL")
        self.password = password or os.environ.get("GMAIL_APP_PASSWORD")
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the email checking thread"""
        if self.thread is not None and self.thread.is_alive():
            return  # Already running
            
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the email checking thread"""
        self.running = False
        if self.thread is not None:
            self.thread.join(timeout=1.0)
            self.thread = None
    
    def _run(self):
        """Main email checking loop"""
        while self.running:
            try:
                if not self.email or not self.password:
                    print("Error: Gmail credentials not available")
                    self.email_count_updated.emit(0)
                    time.sleep(30)  # Wait longer if no credentials
                    continue
                
                with IMAPClient("imap.gmail.com") as client:
                    client.login(self.email, self.password)
                    
                    # Initial update
                    count = self._get_unread_count(client)
                    self.email_count_updated.emit(count)
                    
                    # IDLE mode to wait for updates
                    while self.running:
                        client.idle()
                        responses = client.idle_check(timeout=10)  # Check every 10 seconds max
                        client.idle_done()
                        
                        # Update unread count if still running
                        if self.running:
                            count = self._get_unread_count(client)
                            self.email_count_updated.emit(count)
                
            except Exception as e:
                print(f"Email connection error: {e}")
                time.sleep(5)  # Wait before retry
    
    def _get_unread_count(self, client):
        """Get unread email count from the inbox"""
        try:
            client.select_folder("INBOX")
            messages = client.search(["UNSEEN"])
            return len(messages)
        except Exception as e:
            print(f"Error fetching unread count: {e}")
            return 0

class EmailWidget(BaseWidget):
    """A minimalist email widget showing unread count"""
    
    def __init__(self, parent=None):
        # Initialize force_hidden before BaseWidget init which might trigger eventFilter
        self.force_hidden = False
        self.unread_count = 0
        
        # Default configuration
        default_config = {
            "font_size": 16,            # Single font size for all text
            "font_color": "#FFFFFF",    # Bright white text
            "font_opacity": 1.0,
            "update_interval": 60.0,    # Seconds between forced refreshes
            "spacing": 8,               # Spacing between count and label
            "bg_color": "#2A2A2A",      # Darker background
            "bg_opacity": 0.5,          # More visible background
            # Padding settings
            "padding_x": 25, 
            "padding_y": 12,
            # Border radius
            "border_radius": 6,         # Rounded corners
            # Credentials (best to use env vars)
            "email": "",                # Will use env var GMAIL if empty
            "password": ""              # Will use env var GMAIL_APP_PASSWORD if empty
        }
        
        # Initialize the base widget
        super().__init__("gmail.json", default_config, parent)
        
        # Install event filter on self
        self.installEventFilter(self)
        
        # Load font and setup UI
        self.load_font()
        self.setup_ui()
        
        # Create email fetcher
        self.email_fetcher = EmailFetcher(
            email=self.config.get("email", ""),
            password=self.config.get("password", "")
        )
        self.email_fetcher.email_count_updated.connect(self.update_email_count)
        self.email_fetcher.start()
        
        # Update display with current unread count (initially 0)
        self.update_display_text()
        
        # Create refresh timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_email_count)
        self.timer.start(int(self.config["update_interval"] * 1000))
    
    def setup_ui(self):
        """Create the widget layout"""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Create a main vertical layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        
        # Create a horizontal layout for the single line display
        container = QWidget()
        container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(self.config.get("spacing", 8))
        h_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create a single label for all content - Use config label_text
        label_text = self.config.get('label_text', 'unread mails')
        self.label = QLabel(f"0 {label_text}")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Set fixed size policy
        size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.label.setSizePolicy(size_policy)
        
        # Set font
        font_size = self.config["font_size"]
        label_font = QFont(self.font_name, font_size)
        self.label.setFont(label_font)
        
        # Add the label to the layout
        h_layout.addWidget(self.label)
        
        # Add the container to the main layout
        main_layout.addWidget(container)
        
        # Apply styles
        self.apply_styles()
    
    def apply_styles(self):
        """Apply stylesheet based on configuration"""
        # Background color as QColor
        bg_color = self.config.get("bg_color", "#2A2A2A")
        bg_opacity = self.config.get("bg_opacity", 0.5)
        
        # Font color and opacity
        font_color = self.config.get("font_color", "#FFFFFF")
        font_opacity = self.config.get("font_opacity", 1.0)
        
        # Border radius
        border_radius = self.config.get("border_radius", 6)
        
        # Create border radius style
        radius_style = f"border-radius: {border_radius}px;"
        
        # Padding for the whole container
        padding_x = self.config.get("padding_x", 25)
        padding_y = self.config.get("padding_y", 12)
        
        # Apply to label - use direct RGBA color with opacity
        label_style = f"""
            color: rgba({QColor(font_color).red()}, 
                        {QColor(font_color).green()}, 
                        {QColor(font_color).blue()}, 
                        {font_opacity});
            background-color: transparent;
        """
        
        self.label.setStyleSheet(label_style)
        
        # Create padding for the container - ensure min size when text is empty
        min_width = 30 if not self.label.text() else 0
        min_height = 20 if not self.label.text() else 0
        
        container_style = f"""
            padding: {padding_y}px {padding_x}px;
            background-color: rgba({QColor(bg_color).red()}, 
                                  {QColor(bg_color).green()}, 
                                  {QColor(bg_color).blue()}, 
                                  {bg_opacity});
            {radius_style}
            min-width: {min_width}px;
            min-height: {min_height}px;
        """
        
        # Apply to container widget (the one with the horizontal layout)
        self.centralWidget().findChild(QWidget).setStyleSheet(container_style)
        
        # Ensure proper sizing
        self._fix_label_sizing()
    
    def update_display_text(self):
        """UPDATE THE DISPLAYED TEXT - this is the only place label text should be set"""
        # First, check if we need to hide the entire widget
        if self.unread_count == 0:
            # Completely hide the widget when zero emails
            self.force_hidden = True
            self.setVisible(False)
            return
        else:
            # Make sure widget is visible for non-zero counts
            self.force_hidden = False
            self.setVisible(True)
        
        # Now handle text formatting for visible widget
        if self.unread_count == 1:
            # Handle singular form
            display_text = "1 unread mail"
        else:
            # Get label text from config (default to "unread mails" if not found)
            label_text = self.config.get('label_text', 'unread mails')
            display_text = f"{self.unread_count} {label_text}"
        
        # Set the text on the label
        self.label.setText(display_text)
        
        # Update sizing to fit the text
        self._fix_label_sizing()
    
    def update_email_count(self, count):
        """Update the unread email count and display"""
        self.unread_count = count
        self.update_display_text()
    
    def refresh_email_count(self):
        """Force refresh of email count (called by timer)"""
        # Just to check if the background thread is still running
        if not self.email_fetcher.thread or not self.email_fetcher.thread.is_alive():
            self.email_fetcher.start()
    
    def apply_config(self):
        """Apply configuration changes"""
        # Apply font
        font_size = self.config["font_size"]
        label_font = QFont(self.font_name, font_size)
        self.label.setFont(label_font)
        
        # Update displayed text with current count but new config text
        self.update_display_text()
        
        # Update spacing
        h_layout = self.centralWidget().findChild(QWidget).layout()
        h_layout.setSpacing(self.config.get("spacing", 8))
        
        # Apply styles
        self.apply_styles()
        
        # Force a complete recalculation of sizes
        self._fix_label_sizing()
        
        # Make sure container adjusts properly
        container = self.centralWidget().findChild(QWidget)
        container.adjustSize()
        self.adjustSize()
        
        # Check if we need to update email fetcher credentials
        new_email = self.config.get("email", "")
        new_password = self.config.get("password", "")
        
        if (new_email != self.email_fetcher.email or 
            new_password != self.email_fetcher.password):
            
            # Stop the current fetcher
            self.email_fetcher.stop()
            
            # Create a new one with updated credentials
            self.email_fetcher = EmailFetcher(
                email=new_email,
                password=new_password
            )
            self.email_fetcher.email_count_updated.connect(self.update_email_count)
            self.email_fetcher.start()
        
        # Update timer interval
        self.timer.stop()
        self.timer.start(int(self.config["update_interval"] * 1000))
    
    def _fix_label_sizing(self):
        """Fix label sizing to prevent layout shifts"""
        # Get text metrics for the label
        text = self.label.text()
        
        if not text:
            # For empty text, set a minimal size but keep the widget visible
            self.label.setFixedSize(10, 10)
        else:
            # Normal sizing for text
            width = self.label.fontMetrics().horizontalAdvance(text)
            height = self.label.fontMetrics().height()
            
            # Set fixed dimensions for the label
            self.label.setFixedSize(width, height)
        
        # Make sure the widget adjusts to the content
        self.adjustSize()
    
    def closeEvent(self, event):
        """Handle application close by stopping the email fetcher"""
        self.email_fetcher.stop()
        super().closeEvent(event)

    # Override visibility methods to respect force_hidden setting
    def _restore_visibility(self):
        """Override to respect force_hidden setting"""
        if not self.force_hidden:
            # Only restore visibility if not force hidden
            super()._restore_visibility()
    
    def eventFilter(self, obj, event):
        """Override to respect force_hidden setting"""
        if obj == self and self.force_hidden and (event.type() == QEvent.Show or event.type() == QEvent.WindowStateChange):
            # Prevent showing when force hidden
            self.setVisible(False)
            return True
        return super().eventFilter(obj, event)
    
    def showEvent(self, event):
        """Override to respect force_hidden setting"""
        if self.force_hidden:
            # Don't process show events when force hidden
            self.setVisible(False)
            return
        super().showEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = EmailWidget()
    widget.show()
    sys.exit(app.exec_()) 