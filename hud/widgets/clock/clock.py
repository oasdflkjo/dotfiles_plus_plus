#!/usr/bin/env python
import sys
import os
import json
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QSizePolicy
from PyQt5.QtGui import QFont, QFontDatabase, QColor
from PyQt5.QtCore import Qt, QTimer, QMargins, QEvent

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
            "bg_opacity": 0.01,
            # Individual padding settings
            "clock_padding_x": 15,
            "clock_padding_y": 20,
            "date_padding_x": 10,
            "date_padding_y": 15,
            # Size controls
            "clock_width": 0,  # 0 = auto
            "clock_height": 0, # 0 = auto
            "date_width": 0,   # 0 = auto
            "date_height": 0,  # 0 = auto
            # Additional styling options
            "clock_bg_color": "transparent",
            "date_bg_color": "transparent",
            "clock_opacity": 1.0,
            "date_opacity": 1.0,
            # Border radius settings
            "clock_border_radius": 0,
            "date_border_radius": 0
        }
        
        # Initialize the base widget
        super().__init__("clock.json", default_config, parent)
        
        # Install event filter on self
        self.installEventFilter(self)
        
        # Load font and setup UI
        self.load_font()
        self.setup_ui()
        
        # Create update timer and do initial update
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(int(self.config["update_interval"] * 1000))
        self.update_time()
    
    def setup_ui(self):
        """Create the widget layout"""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Create layout with center alignment
        layout = QVBoxLayout(central_widget)
        # Use 0 margins for the overall container
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(max(0, self.config["vertical_spacing"]))
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)  # Center horizontally
        
        # Create clock label with tight size policy
        self.clock_label = QLabel()
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Set fixed size policy for maximum control
        size_policy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.clock_label.setSizePolicy(size_policy)
        
        clock_font = QFont(self.font_name, self.config["clock_font_size"])
        if self.config["clock_is_bold"]:
            clock_font.setWeight(QFont.Weight.Bold)
        self.clock_label.setFont(clock_font)
        
        # Create date label
        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Set fixed size policy for the date label too
        self.date_label.setSizePolicy(size_policy)
        
        date_font = QFont(self.font_name, self.config["date_font_size"])
        self.date_label.setFont(date_font)
        
        # Add to layout and apply styles
        layout.addWidget(self.clock_label, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.date_label, 0, Qt.AlignmentFlag.AlignHCenter)
        self.apply_styles()
    
    def apply_styles(self):
        """Apply stylesheet based on configuration"""
        # For negative spacing, use negative margin on the date label
        margin_top = min(0, self.config["vertical_spacing"])
        
        # Get single background color and opacity for both elements
        bg_color = self.config.get("bg_color", "black")
        bg_opacity = self.config.get("bg_opacity", 0.9)
        
        # Get single font color and opacity for both elements
        font_color = self.config.get("font_color", "#5D5D5D")
        font_opacity = self.config.get("font_opacity", 1.0)
        
        # Get border radius settings
        clock_radius = self.config.get("clock_border_radius", 0)
        date_radius = self.config.get("date_border_radius", 0)
        
        # Apply clock specific styling
        clock_style = f"""
            background-color: {self.config.get('clock_bg_color', 'transparent')};
            color: {font_color};
            padding: {self.config['clock_padding_y']}px {self.config['clock_padding_x']}px;
            border-radius: {clock_radius}px;
            opacity: {self.config.get('clock_opacity', 1.0)};
        """
        self.clock_label.setStyleSheet(clock_style)
        
        # Apply date specific styling
        date_style = f"""
            background-color: {self.config.get('date_bg_color', 'transparent')};
            color: {font_color};
            padding: {self.config['date_padding_y']}px {self.config['date_padding_x']}px;
            border-radius: {date_radius}px;
            margin-top: {margin_top}px;
            opacity: {self.config.get('date_opacity', 1.0)};
        """
        self.date_label.setStyleSheet(date_style)
        
        # Apply global stylesheet to the central widget
        central_style = f"""
            background-color: rgba({QColor(bg_color).red()}, 
                                   {QColor(bg_color).green()}, 
                                   {QColor(bg_color).blue()}, 
                                   {bg_opacity});
        """
        self.centralWidget().setStyleSheet(central_style)
        
        # Fix spacing issues with set sizes
        self._fix_clock_box_spacing()
    
    def update_time(self):
        """Update time and date text"""
        now = datetime.now()
        
        # Format time using configured format
        time_format = "%H:%M:%S" if self.config["show_seconds"] else self.config["time_format"]
        time_text = now.strftime(time_format)
        self.clock_label.setText(time_text)
        
        # Format date using configured format
        date_text = now.strftime(self.config["date_format"])
        self.date_label.setText(date_text)
        
        # Fix spacing after text update
        self._fix_clock_box_spacing()
    
    def apply_config(self):
        """Apply configuration changes"""
        # Update fonts
        clock_font = QFont(self.font_name, self.config["clock_font_size"])
        if self.config["clock_is_bold"]:
            clock_font.setWeight(QFont.Weight.Bold)
        self.clock_label.setFont(clock_font)
        
        date_font = QFont(self.font_name, self.config["date_font_size"])
        self.date_label.setFont(date_font)
        
        # Apply spacing
        layout = self.centralWidget().layout()
        layout.setSpacing(max(0, self.config["vertical_spacing"]))
        
        # Apply styles
        self.apply_styles()
        
        # Set timer interval
        self.timer.stop()
        self.timer.start(int(self.config["update_interval"] * 1000))
        
        # Update immediately
        self.update_time()
    
    def _fix_clock_box_spacing(self):
        """Fix spacing issues with the clock text label"""
        # Get the current text
        clock_text = self.clock_label.text()
        date_text = self.date_label.text()
        
        # Get required width/height using font metrics
        clock_font_metrics = self.clock_label.fontMetrics()
        date_font_metrics = self.date_label.fontMetrics()
        
        # Calculate raw text dimensions
        clock_width = clock_font_metrics.horizontalAdvance(clock_text)
        clock_height = clock_font_metrics.height()
        
        date_width = date_font_metrics.horizontalAdvance(date_text)
        date_height = date_font_metrics.height()
        
        # Calculate final dimensions with padding
        final_clock_width = max(self.config["clock_width"] or 0, 
                               clock_width + 2*self.config["clock_padding_x"])
        
        final_clock_height = max(self.config["clock_height"] or 0, 
                                clock_height + 2*self.config["clock_padding_y"])
        
        final_date_width = max(self.config["date_width"] or 0, 
                              date_width + 2*self.config["date_padding_x"])
        
        final_date_height = max(self.config["date_height"] or 0, 
                               date_height + 2*self.config["date_padding_y"])
        
        # Apply dimensions with fixed sizes if configured
        if self.config["clock_width"]:
            self.clock_label.setFixedWidth(self.config["clock_width"])
        else:
            self.clock_label.setFixedWidth(final_clock_width)
            
        if self.config["clock_height"]:
            self.clock_label.setFixedHeight(self.config["clock_height"])
        else:
            self.clock_label.setFixedHeight(final_clock_height)
            
        if self.config["date_width"]:
            self.date_label.setFixedWidth(self.config["date_width"])
        else:
            self.date_label.setFixedWidth(final_date_width)
            
        if self.config["date_height"]:
            self.date_label.setFixedHeight(self.config["date_height"])
        else:
            self.date_label.setFixedHeight(final_date_height)
        
        # Adjust widget size to fit
        self.adjustSize() 