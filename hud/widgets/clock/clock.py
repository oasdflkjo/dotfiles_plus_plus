#!/usr/bin/env python
import sys
import os
import json
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QSizePolicy
from PyQt5.QtGui import QFont, QFontDatabase, QColor, QPainter, QPen, QFontMetrics
from PyQt5.QtCore import Qt, QTimer, QEvent, QRect

from widgets.base_widget import BaseWidget, HAS_WIN32_MODULES

class ClockWidget(BaseWidget):
    """A minimalist clock widget displaying time and date"""
    
    def __init__(self, parent=None):
        # Default configuration
        default_config = {
            "clock_font_size": 100,
            "date_font_size": 18,
            "font_color": "#5D5D5D",
            "font_opacity": 1.0,
            "clock_is_bold": False,
            "show_seconds": False,
            "time_format": "%H:%M",
            "date_format": "%A, %d %B %Y",
            "update_interval": 1.0,
            "vertical_spacing": 20,
            "bg_color": "black",
            "bg_opacity": 0.01
        }
        
        # Initialize the base widget
        super().__init__("clock.json", default_config, parent)
        
        # Install event filter on self
        self.installEventFilter(self)
        
        # Load font and setup UI
        self.load_font()
        self.setup_ui()
        
        # Text content that will be painted
        self.time_text = ""
        self.date_text = ""
        
        # Create update timer and do initial update
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(int(self.config["update_interval"] * 1000))
        self.update_time()
    
    def setup_ui(self):
        """Setup minimal UI with just a content area"""
        # Create central widget
        self.content_widget = QWidget()
        self.setCentralWidget(self.content_widget)
        self.content_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Create minimal layout
        layout = QVBoxLayout(self.content_widget)
        layout.setContentsMargins(8, 8, 8, 8)  # Small padding
        
        # Create the custom widget that will paint the clock
        self.clock_canvas = ClockCanvas(self.font_name, self.config)
        
        # Add the canvas to the layout
        layout.addWidget(self.clock_canvas)
    
    def update_time(self):
        """Update time and date text"""
        now = datetime.now()
        
        # Format time using configured format
        time_format = "%H:%M:%S" if self.config["show_seconds"] else self.config["time_format"]
        self.time_text = now.strftime(time_format)
        
        # Format date using configured format
        self.date_text = now.strftime(self.config["date_format"])
        
        # Update the canvas with new text
        self.clock_canvas.set_text(self.time_text, self.date_text)
        self.clock_canvas.update()  # Force repaint
    
    def apply_config(self):
        """Apply configuration changes"""
        if hasattr(self, 'clock_canvas'):
            # Update the canvas config
            self.clock_canvas.update_config(self.config)
            
            # Update timer interval
            self.timer.stop()
            self.timer.start(int(self.config["update_interval"] * 1000))
            
            # Update immediately
            self.update_time()


class ClockCanvas(QWidget):
    """Custom widget that directly paints text for precise control"""
    
    def __init__(self, font_name, config, parent=None):
        super().__init__(parent)
        self.font_name = font_name
        self.config = config
        self.time_text = ""
        self.date_text = ""
        
        # Set transparent background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        # Create fonts
        self.update_fonts()
    
    def update_config(self, config):
        """Update configuration and fonts"""
        self.config = config
        self.update_fonts()
        self.update_size()
        self.update()  # Force repaint
    
    def update_fonts(self):
        """Update fonts based on config"""
        # Create clock font
        self.clock_font = QFont(self.font_name, self.config["clock_font_size"])
        if self.config["clock_is_bold"]:
            self.clock_font.setWeight(QFont.Weight.Bold)
        
        # Create date font
        self.date_font = QFont(self.font_name, self.config["date_font_size"])
        
        # Create font metrics for measurements
        self.clock_fm = QFontMetrics(self.clock_font)
        self.date_fm = QFontMetrics(self.date_font)
    
    def set_text(self, time_text, date_text):
        """Set the text to display"""
        self.time_text = time_text
        self.date_text = date_text
        self.update_size()
    
    def update_size(self):
        """Update the widget size based on text content"""
        if not self.time_text and not self.date_text:
            return
        
        # Calculate time text dimensions using tight bounding rect
        time_rect = self.clock_fm.tightBoundingRect(self.time_text)
        time_width = time_rect.width()
        time_height = time_rect.height()
        
        # Calculate date text dimensions using tight bounding rect
        date_rect = self.date_fm.tightBoundingRect(self.date_text)
        date_width = date_rect.width()
        date_height = date_rect.height()
        
        # Get spacing from config
        spacing = self.config.get("vertical_spacing", 0)
        
        # Calculate total size needed
        width = max(time_width, date_width) + 20  # Add some padding
        # Very important: calculate height precisely
        height = time_height + date_height + spacing + 16  # Add padding
        
        # Set widget size
        self.setFixedSize(width, height)
    
    def paintEvent(self, event):
        """Paint the clock and date text directly"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        
        # Get color and opacity from config
        bg_color = self.config.get("bg_color", "black")
        bg_opacity = self.config.get("bg_opacity", 0.9)
        
        # Create and set background color with opacity
        painter.setPen(Qt.PenStyle.NoPen)
        bg_qcolor = QColor(bg_color)
        bg_qcolor.setAlphaF(bg_opacity)
        painter.setBrush(bg_qcolor)
        
        # Draw rounded rectangle background
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 8, 8)
        
        # Get font color and opacity
        font_color = self.config.get("font_color", "#5D5D5D")
        font_opacity = self.config.get("font_opacity", 1.0)
        
        # Create and set text color with opacity
        text_qcolor = QColor(font_color)
        text_qcolor.setAlphaF(font_opacity)
        
        # Get tight bounding rectangles
        time_rect = self.clock_fm.tightBoundingRect(self.time_text)
        date_rect = self.date_fm.tightBoundingRect(self.date_text)
        
        # Get vertical spacing
        spacing = self.config.get("vertical_spacing", 0)
        
        # Calculate x positions to center text
        time_x = (self.width() - time_rect.width()) // 2
        date_x = (self.width() - date_rect.width()) // 2
        
        # Calculate y positions for text
        # For time, position from top plus its ascent to align properly
        time_y = 10 + time_rect.height()
        
        # For date, position relative to time with spacing
        # Adding date_rect.height() ensures we're positioning at the baseline
        date_y = time_y + spacing + date_rect.height()
        
        # Draw time text
        painter.setFont(self.clock_font)
        painter.setPen(QPen(text_qcolor))
        painter.drawText(time_x, time_y, self.time_text)
        
        # Draw date text
        painter.setFont(self.date_font)
        painter.setPen(QPen(text_qcolor))
        painter.drawText(date_x, date_y, self.date_text) 