import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont

class ModernUIKit:
    def __init__(self):
        self.setup_styles()
    
    def setup_styles(self):
        """Setup modern styles for ttk widgets"""
        style = ttk.Style()
        
        # Configure theme
        style.theme_use('clam')
        
        # Color scheme
        self.colors = {
            'primary': '#2E86AB',      # Blue
            'secondary': '#A23B72',    # Purple
            'success': '#F18F01',      # Orange
            'danger': '#C73E1D',       # Red
            'warning': '#F77F00',      # Amber
            'info': '#06A77D',         # Teal
            'light': '#F8F9FA',        # Light gray
            'dark': '#212529',         # Dark gray
            'white': '#FFFFFF',
            'gray': '#6C757D',
            'border': '#DEE2E6'
        }
        
        # Configure styles
        self.configure_button_styles(style)
        self.configure_frame_styles(style)
        self.configure_treeview_styles(style)
        self.configure_notebook_styles(style)
        self.configure_label_styles(style)
    
    def configure_button_styles(self, style):
        """Configure button styles"""
        # Primary button
        style.configure('Primary.TButton',
                       background=self.colors['primary'],
                       foreground=self.colors['white'],
                       borderwidth=0,
                       focuscolor='none',
                       padding=(10, 8))
        
        style.map('Primary.TButton',
                 background=[('active', '#1E6B8A'),
                           ('pressed', '#155E75')])
        
        # Success button
        style.configure('Success.TButton',
                       background=self.colors['success'],
                       foreground=self.colors['white'],
                       borderwidth=0,
                       focuscolor='none',
                       padding=(10, 8))
        
        style.map('Success.TButton',
                 background=[('active', '#D17A00'),
                           ('pressed', '#B86600')])
        
        # Danger button
        style.configure('Danger.TButton',
                       background=self.colors['danger'],
                       foreground=self.colors['white'],
                       borderwidth=0,
                       focuscolor='none',
                       padding=(10, 8))
        
        style.map('Danger.TButton',
                 background=[('active', '#A62E1A'),
                           ('pressed', '#8B2515')])
        
        # Secondary button
        style.configure('Secondary.TButton',
                       background=self.colors['secondary'],
                       foreground=self.colors['white'],
                       borderwidth=0,
                       focuscolor='none',
                       padding=(10, 8))
        
        style.map('Secondary.TButton',
                 background=[('active', '#8B2E5A'),
                           ('pressed', '#74254A')])
        
        # Info button
        style.configure('Info.TButton',
                       background=self.colors['info'],
                       foreground=self.colors['white'],
                       borderwidth=0,
                       focuscolor='none',
                       padding=(10, 8))
        
        style.map('Info.TButton',
                 background=[('active', '#058A6B'),
                           ('pressed', '#047A5B')])
    
    def configure_frame_styles(self, style):
        """Configure frame styles"""
        # Main frame
        style.configure('Main.TFrame',
                       background=self.colors['white'],
                       relief='flat')
        
        # Card frame
        style.configure('Card.TFrame',
                       background=self.colors['white'],
                       relief='raised',
                       borderwidth=1)
        
        # Header frame
        style.configure('Header.TFrame',
                       background=self.colors['primary'],
                       relief='flat')
    
    def configure_treeview_styles(self, style):
        """Configure treeview styles"""
        # Treeview
        style.configure('Modern.Treeview',
                       background=self.colors['white'],
                       foreground=self.colors['dark'],
                       fieldbackground=self.colors['white'],
                       borderwidth=1,
                       relief='solid')
        
        # Treeview headings
        style.configure('Modern.Treeview.Heading',
                       background=self.colors['light'],
                       foreground=self.colors['dark'],
                       borderwidth=1,
                       relief='solid',
                       font=('Segoe UI', 9, 'bold'))
        
        # Treeview selection
        style.map('Modern.Treeview',
                 background=[('selected', self.colors['primary'])],
                 foreground=[('selected', self.colors['white'])])
        
        # Treeview alternating rows
        style.configure('Modern.Treeview',
                       rowheight=25)
    
    def configure_notebook_styles(self, style):
        """Configure notebook styles"""
        # Notebook
        style.configure('Modern.TNotebook',
                       background=self.colors['white'],
                       borderwidth=0)
        
        # Notebook tab
        style.configure('Modern.TNotebook.Tab',
                       background=self.colors['light'],
                       foreground=self.colors['dark'],
                       padding=(15, 10),
                       font=('Segoe UI', 9))
        
        # Selected tab
        style.map('Modern.TNotebook.Tab',
                 background=[('selected', self.colors['white']),
                           ('active', self.colors['light'])],
                 foreground=[('selected', self.colors['primary']),
                           ('active', self.colors['dark'])])
    
    def configure_label_styles(self, style):
        """Configure label styles"""
        # Title label
        style.configure('Title.TLabel',
                       background=self.colors['white'],
                       foreground=self.colors['dark'],
                       font=('Segoe UI', 16, 'bold'))
        
        # Heading label
        style.configure('Heading.TLabel',
                       background=self.colors['white'],
                       foreground=self.colors['dark'],
                       font=('Segoe UI', 12, 'bold'))
        
        # Status label
        style.configure('Status.TLabel',
                       background=self.colors['white'],
                       foreground=self.colors['gray'],
                       font=('Segoe UI', 9))
        
        # Success status
        style.configure('Success.TLabel',
                       background=self.colors['white'],
                       foreground=self.colors['success'],
                       font=('Segoe UI', 9, 'bold'))
        
        # Error status
        style.configure('Error.TLabel',
                       background=self.colors['white'],
                       foreground=self.colors['danger'],
                       font=('Segoe UI', 9, 'bold'))
    
    def create_modern_button(self, parent, text, style='Primary.TButton', command=None):
        """Create a modern styled button"""
        return ttk.Button(parent, text=text, style=style, command=command)
    
    def create_modern_frame(self, parent, style='Main.TFrame'):
        """Create a modern styled frame"""
        return ttk.Frame(parent, style=style)
    
    def create_modern_treeview(self, parent, columns, style='Modern.Treeview'):
        """Create a modern styled treeview"""
        tree = ttk.Treeview(parent, columns=columns, show='headings', style=style)
        
        # Configure columns
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor='center')
        
        return tree
    
    def create_modern_notebook(self, parent, style='Modern.TNotebook'):
        """Create a modern styled notebook"""
        return ttk.Notebook(parent, style=style)
    
    def create_modern_label(self, parent, text, style='Title.TLabel'):
        """Create a modern styled label"""
        return ttk.Label(parent, text=text, style=style)
    
    def get_colors(self):
        """Get color scheme"""
        return self.colors

# Global UI kit instance
ui_kit = ModernUIKit()
