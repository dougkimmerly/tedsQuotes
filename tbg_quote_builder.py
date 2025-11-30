#!/usr/bin/env python3
"""
TBG Enterprises Quote Builder
A simple Mac app for creating professional home renovation quotes
and exporting to QuickBooks.
"""

# Suppress macOS Tk deprecation warning
import os
os.environ['TK_SILENCE_DEPRECATION'] = '1'

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import csv
import json
from pathlib import Path

# PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


# TBG Brand Colors
TBG_RED = HexColor("#C41E3A")
TBG_BLACK = HexColor("#1A1A1A")
TBG_GRAY = HexColor("#4A4A4A")
TBG_LIGHT_GRAY = HexColor("#F5F5F5")

# Company Info
COMPANY_ADDRESS = "4351 Latimer Cr, Burlington ON L7M 4R3"
COMPANY_EMAIL = "Ted@TBGEnterprises.com"
COMPANY_PHONE = "(416) 271-4341"


class TBGLogo:
    """TBG Logo as a Flowable for use in Platypus"""
    def __init__(self, width=120, height=50):
        self.width = width
        self.height = height
    
    def drawOn(self, canv, x, y, _sW=0):
        canv.saveState()
        canv.translate(x, y)
        self.draw(canv)
        canv.restoreState()
    
    def wrap(self, availWidth, availHeight):
        return (self.width, self.height)
    
    def draw(self, canv):
        # Red roof/chevron
        roof_width = 56
        roof_height = 14
        roof_x = (self.width - roof_width) / 2
        roof_y = self.height - roof_height - 2
        
        # Draw roof as filled polygon
        canv.setFillColor(TBG_RED)
        canv.setStrokeColor(TBG_RED)
        
        # Outer roof path
        path = canv.beginPath()
        path.moveTo(roof_x, roof_y)
        path.lineTo(roof_x + roof_width/2, roof_y + roof_height)
        path.lineTo(roof_x + roof_width, roof_y)
        path.lineTo(roof_x + roof_width - 6, roof_y)
        path.lineTo(roof_x + roof_width/2, roof_y + roof_height - 6)
        path.lineTo(roof_x + 6, roof_y)
        path.close()
        canv.drawPath(path, fill=1, stroke=0)
        
        # "TBG" text
        canv.setFillColor(TBG_BLACK)
        canv.setFont("Helvetica-Bold", 24)
        canv.drawCentredString(self.width/2, self.height - 38, "TBG")
        
        # "enterprises" text
        canv.setFillColor(TBG_RED)
        canv.setFont("Helvetica", 10)
        canv.drawCentredString(self.width/2, self.height - 50, "enterprises")


class LineItemFrame(ttk.Frame):
    """A single line item row"""
    def __init__(self, parent, categories, on_delete, on_update):
        super().__init__(parent)
        self.on_delete = on_delete
        self.on_update = on_update
        
        # Category dropdown
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(self, textvariable=self.category_var, 
                                           values=categories, width=15, state="readonly")
        self.category_combo.grid(row=0, column=0, padx=2, pady=2)
        self.category_combo.bind("<<ComboboxSelected>>", lambda e: self.on_update())
        
        # Description
        self.desc_var = tk.StringVar()
        self.desc_entry = ttk.Entry(self, textvariable=self.desc_var, width=35)
        self.desc_entry.grid(row=0, column=1, padx=2, pady=2)
        self.desc_entry.bind("<KeyRelease>", lambda e: self.on_update())
        
        # Quantity
        self.qty_var = tk.StringVar(value="1")
        self.qty_entry = ttk.Entry(self, textvariable=self.qty_var, width=8)
        self.qty_entry.grid(row=0, column=2, padx=2, pady=2)
        self.qty_entry.bind("<KeyRelease>", lambda e: self.on_update())
        
        # Unit
        self.unit_var = tk.StringVar(value="ea")
        self.unit_combo = ttk.Combobox(self, textvariable=self.unit_var,
                                       values=["ea", "hr", "sq ft", "ln ft", "day", "lot"],
                                       width=6, state="readonly")
        self.unit_combo.grid(row=0, column=3, padx=2, pady=2)
        
        # Rate
        self.rate_var = tk.StringVar(value="0.00")
        self.rate_entry = ttk.Entry(self, textvariable=self.rate_var, width=10)
        self.rate_entry.grid(row=0, column=4, padx=2, pady=2)
        self.rate_entry.bind("<KeyRelease>", lambda e: self.on_update())
        
        # Amount (calculated)
        self.amount_label = ttk.Label(self, text="$0.00", width=12, anchor="e")
        self.amount_label.grid(row=0, column=5, padx=2, pady=2)
        
        # Delete button
        self.delete_btn = ttk.Button(self, text="✕", width=3, command=self.delete_self)
        self.delete_btn.grid(row=0, column=6, padx=2, pady=2)
    
    def delete_self(self):
        self.on_delete(self)
    
    def get_amount(self):
        try:
            qty = float(self.qty_var.get() or 0)
            rate = float(self.rate_var.get().replace(",", "") or 0)
            return qty * rate
        except ValueError:
            return 0
    
    def update_amount_display(self):
        amount = self.get_amount()
        self.amount_label.config(text=f"${amount:,.2f}")
    
    def get_data(self):
        return {
            "category": self.category_var.get(),
            "description": self.desc_var.get(),
            "quantity": self.qty_var.get(),
            "unit": self.unit_var.get(),
            "rate": self.rate_var.get(),
            "amount": self.get_amount()
        }


class TBGQuoteBuilder(tk.Tk):
    """Main application window"""
    
    DEFAULT_CATEGORIES = [
        "Demo",
        "Framing", 
        "Electrical",
        "Plumbing",
        "HVAC",
        "Drywall",
        "Painting",
        "Flooring",
        "Tile",
        "Showers",
        "Cabinets",
        "Countertops",
        "Fixtures",
        "Trim/Finish",
        "Cleanup",
        "Materials",
        "Other"
    ]
    
    def __init__(self):
        super().__init__()
        
        self.title("TBG Enterprises - Quote Builder")
        self.geometry("950x850")
        self.configure(bg="#f0f0f0")
        
        # Load custom categories from file (if exists)
        self.categories = self.load_categories()
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure("Header.TLabel", font=("Helvetica", 14, "bold"))
        self.style.configure("Title.TLabel", font=("Helvetica", 18, "bold"), foreground="#C41E3A")
        self.style.configure("Total.TLabel", font=("Helvetica", 12, "bold"))
        
        self.line_items = []
        self.attachments = []  # List of file paths for attached plans/images
        self.quote_number = self.generate_quote_number()
        
        self.create_widgets()
        
        # Fix for macOS black window issue
        self.update_idletasks()
        self.after(100, self.lift)
    
    def get_config_path(self):
        """Get path to config file in user's home directory"""
        return os.path.join(str(Path.home()), '.tbg_quote_builder_config.json')
    
    def load_categories(self):
        """Load categories from config file, or use defaults"""
        config_path = self.get_config_path()
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    return config.get('categories', self.DEFAULT_CATEGORIES.copy())
        except:
            pass
        return self.DEFAULT_CATEGORIES.copy()
    
    def save_categories(self):
        """Save categories to config file"""
        config_path = self.get_config_path()
        try:
            config = {'categories': self.categories}
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Could not save categories: {str(e)}")
    
    def check_for_updates(self):
        """Check GitHub for updates and install if available"""
        import subprocess
        
        # Get the app directory
        app_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Check if this is a git repo
        git_dir = os.path.join(app_dir, '.git')
        if not os.path.exists(git_dir):
            messagebox.showinfo("Updates", 
                "This installation is not connected to GitHub.\n"
                "Updates must be downloaded manually.")
            return
        
        try:
            # Fetch from remote
            subprocess.run(['git', 'fetch', 'origin', 'main'], 
                          cwd=app_dir, capture_output=True, check=True)
            
            # Get local and remote commit hashes
            local = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                   cwd=app_dir, capture_output=True, text=True)
            remote = subprocess.run(['git', 'rev-parse', 'origin/main'], 
                                    cwd=app_dir, capture_output=True, text=True)
            
            if local.stdout.strip() == remote.stdout.strip():
                messagebox.showinfo("Updates", "✓ You're running the latest version!")
            else:
                # Ask user if they want to update
                if messagebox.askyesno("Update Available", 
                    "A new version is available!\n\n"
                    "Would you like to download and install it?\n\n"
                    "The app will restart after updating."):
                    
                    # Pull updates
                    result = subprocess.run(['git', 'pull', 'origin', 'main'], 
                                          cwd=app_dir, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        messagebox.showinfo("Update Complete", 
                            "✓ Update installed successfully!\n\n"
                            "Please restart the app to use the new version.")
                        self.quit()
                    else:
                        messagebox.showerror("Update Failed", 
                            f"Could not install update:\n{result.stderr}")
        
        except FileNotFoundError:
            messagebox.showerror("Error", 
                "Git is not installed.\n\n"
                "Please install Xcode Command Line Tools:\n"
                "Open Terminal and run: xcode-select --install")
        except Exception as e:
            messagebox.showerror("Error", f"Update check failed:\n{str(e)}")
    
    def generate_quote_number(self):
        """Generate a quote number based on date"""
        return f"TBG-{datetime.now().strftime('%Y%m%d-%H%M')}"
    
    def create_widgets(self):
        """Create all UI elements"""
        
        # Main container with scrollbar
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="TBG ENTERPRISES", style="Title.TLabel").pack(side=tk.LEFT)
        ttk.Label(header_frame, text="Home Renovation Quote Builder", 
                  font=("Helvetica", 10)).pack(side=tk.LEFT, padx=(10, 0))
        
        # Update button in top right
        ttk.Button(header_frame, text="⟳ Check for Updates", command=self.check_for_updates).pack(side=tk.RIGHT)
        
        # Quote Info Section
        info_frame = ttk.LabelFrame(main_frame, text="Quote Information", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Row 1: Quote # and Date
        row1 = ttk.Frame(info_frame)
        row1.pack(fill=tk.X, pady=2)
        
        ttk.Label(row1, text="Quote #:").pack(side=tk.LEFT)
        self.quote_num_var = tk.StringVar(value=self.quote_number)
        ttk.Entry(row1, textvariable=self.quote_num_var, width=20).pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(row1, text="Date:").pack(side=tk.LEFT)
        self.date_var = tk.StringVar(value=datetime.now().strftime("%m/%d/%Y"))
        ttk.Entry(row1, textvariable=self.date_var, width=12).pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(row1, text="Valid For:").pack(side=tk.LEFT)
        self.valid_days_var = tk.StringVar(value="30")
        ttk.Entry(row1, textvariable=self.valid_days_var, width=5).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(row1, text="days").pack(side=tk.LEFT, padx=(2, 0))
        
        # Row 2: Estimated weeks
        row2 = ttk.Frame(info_frame)
        row2.pack(fill=tk.X, pady=2)
        
        ttk.Label(row2, text="Estimated Duration:").pack(side=tk.LEFT)
        self.weeks_var = tk.StringVar(value="4")
        ttk.Entry(row2, textvariable=self.weeks_var, width=5).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(row2, text="weeks").pack(side=tk.LEFT, padx=(2, 0))
        
        # Customer Info Section
        cust_frame = ttk.LabelFrame(main_frame, text="Customer Information", padding=10)
        cust_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Customer name
        name_row = ttk.Frame(cust_frame)
        name_row.pack(fill=tk.X, pady=2)
        ttk.Label(name_row, text="Customer Name:", width=15).pack(side=tk.LEFT)
        self.cust_name_var = tk.StringVar()
        ttk.Entry(name_row, textvariable=self.cust_name_var, width=40).pack(side=tk.LEFT, padx=5)
        
        # Address
        addr_row = ttk.Frame(cust_frame)
        addr_row.pack(fill=tk.X, pady=2)
        ttk.Label(addr_row, text="Project Address:", width=15).pack(side=tk.LEFT)
        self.address_var = tk.StringVar()
        ttk.Entry(addr_row, textvariable=self.address_var, width=50).pack(side=tk.LEFT, padx=5)
        
        # City, State, Zip
        csz_row = ttk.Frame(cust_frame)
        csz_row.pack(fill=tk.X, pady=2)
        ttk.Label(csz_row, text="City:", width=15).pack(side=tk.LEFT)
        self.city_var = tk.StringVar()
        ttk.Entry(csz_row, textvariable=self.city_var, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Label(csz_row, text="State:").pack(side=tk.LEFT)
        self.state_var = tk.StringVar()
        ttk.Entry(csz_row, textvariable=self.state_var, width=5).pack(side=tk.LEFT, padx=5)
        ttk.Label(csz_row, text="ZIP:").pack(side=tk.LEFT)
        self.zip_var = tk.StringVar()
        ttk.Entry(csz_row, textvariable=self.zip_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # Phone and Email
        contact_row = ttk.Frame(cust_frame)
        contact_row.pack(fill=tk.X, pady=2)
        ttk.Label(contact_row, text="Phone:", width=15).pack(side=tk.LEFT)
        self.phone_var = tk.StringVar()
        ttk.Entry(contact_row, textvariable=self.phone_var, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Label(contact_row, text="Email:").pack(side=tk.LEFT)
        self.email_var = tk.StringVar()
        ttk.Entry(contact_row, textvariable=self.email_var, width=30).pack(side=tk.LEFT, padx=5)
        
        # Project Description
        proj_frame = ttk.LabelFrame(main_frame, text="Project Description", padding=10)
        proj_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.project_desc = tk.Text(proj_frame, height=3, width=80, wrap=tk.WORD)
        self.project_desc.pack(fill=tk.X)
        
        # Line Items Section
        items_frame = ttk.LabelFrame(main_frame, text="Line Items", padding=10)
        items_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Column headers
        header_row = ttk.Frame(items_frame)
        header_row.pack(fill=tk.X)
        
        ttk.Label(header_row, text="Category", width=17, font=("Helvetica", 9, "bold")).grid(row=0, column=0, padx=2)
        ttk.Label(header_row, text="Description", width=37, font=("Helvetica", 9, "bold")).grid(row=0, column=1, padx=2)
        ttk.Label(header_row, text="Qty", width=10, font=("Helvetica", 9, "bold")).grid(row=0, column=2, padx=2)
        ttk.Label(header_row, text="Unit", width=8, font=("Helvetica", 9, "bold")).grid(row=0, column=3, padx=2)
        ttk.Label(header_row, text="Rate", width=12, font=("Helvetica", 9, "bold")).grid(row=0, column=4, padx=2)
        ttk.Label(header_row, text="Amount", width=14, font=("Helvetica", 9, "bold")).grid(row=0, column=5, padx=2)
        
        # Scrollable line items container
        self.items_canvas = tk.Canvas(items_frame, height=200)
        scrollbar = ttk.Scrollbar(items_frame, orient="vertical", command=self.items_canvas.yview)
        self.items_container = ttk.Frame(self.items_canvas)
        
        self.items_canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.items_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas_frame = self.items_canvas.create_window((0, 0), window=self.items_container, anchor="nw")
        
        self.items_container.bind("<Configure>", self.on_frame_configure)
        self.items_canvas.bind("<Configure>", self.on_canvas_configure)
        
        # Add item button
        ttk.Button(items_frame, text="+ Add Line Item", command=self.add_line_item).pack(pady=5)
        
        # Totals Section
        totals_frame = ttk.Frame(main_frame)
        totals_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Right-align totals
        totals_inner = ttk.Frame(totals_frame)
        totals_inner.pack(side=tk.RIGHT)
        
        ttk.Label(totals_inner, text="Subtotal:", style="Total.TLabel").grid(row=0, column=0, sticky="e", padx=5)
        self.subtotal_label = ttk.Label(totals_inner, text="$0.00", style="Total.TLabel")
        self.subtotal_label.grid(row=0, column=1, sticky="e")
        
        ttk.Label(totals_inner, text="20% Deposit:", style="Total.TLabel").grid(row=1, column=0, sticky="e", padx=5)
        self.deposit_label = ttk.Label(totals_inner, text="$0.00", style="Total.TLabel")
        self.deposit_label.grid(row=1, column=1, sticky="e")
        
        ttk.Label(totals_inner, text="Weekly Payments:", style="Total.TLabel").grid(row=2, column=0, sticky="e", padx=5)
        self.weekly_label = ttk.Label(totals_inner, text="$0.00/week", style="Total.TLabel")
        self.weekly_label.grid(row=2, column=1, sticky="e")
        
        # Attachments Section (Plans, Images, PDFs)
        attach_frame = ttk.LabelFrame(main_frame, text="Attachments (Plans, Photos, PDFs)", padding=10)
        attach_frame.pack(fill=tk.X, pady=(0, 10))
        
        attach_btn_row = ttk.Frame(attach_frame)
        attach_btn_row.pack(fill=tk.X)
        
        ttk.Button(attach_btn_row, text="+ Add Images/PDFs", command=self.add_attachments).pack(side=tk.LEFT, padx=5)
        ttk.Button(attach_btn_row, text="Clear Attachments", command=self.clear_attachments).pack(side=tk.LEFT, padx=5)
        
        # Listbox to show attached files
        self.attachments_listbox = tk.Listbox(attach_frame, height=3, width=80)
        self.attachments_listbox.pack(fill=tk.X, pady=(5, 0))
        
        # Notes Section
        notes_frame = ttk.LabelFrame(main_frame, text="Notes / Terms", padding=10)
        notes_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.notes_text = tk.Text(notes_frame, height=3, width=80, wrap=tk.WORD)
        self.notes_text.pack(fill=tk.X)
        self.notes_text.insert("1.0", "• 20% deposit required to begin work\n• Remaining balance split evenly over project duration\n• Any changes to scope may affect pricing and timeline")
        
        # Action Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Generate PDF Quote", command=self.generate_pdf).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Export for QuickBooks Online (CSV)", command=self.export_qbo_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Export for QuickBooks Desktop (IIF)", command=self.export_qb_iif).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear All", command=self.clear_all).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="⚙ Categories", command=self.manage_categories).pack(side=tk.RIGHT, padx=5)
        
        # Add initial line item
        self.add_line_item()
    
    def on_frame_configure(self, event):
        self.items_canvas.configure(scrollregion=self.items_canvas.bbox("all"))
    
    def on_canvas_configure(self, event):
        self.items_canvas.itemconfig(self.canvas_frame, width=event.width)
    
    def add_line_item(self):
        """Add a new line item row"""
        item = LineItemFrame(self.items_container, self.categories, 
                            self.remove_line_item, self.update_totals)
        item.pack(fill=tk.X, pady=1)
        self.line_items.append(item)
        self.update_totals()
    
    def remove_line_item(self, item):
        """Remove a line item"""
        if len(self.line_items) > 1:
            self.line_items.remove(item)
            item.destroy()
            self.update_totals()
        else:
            messagebox.showwarning("Warning", "Must have at least one line item")
    
    def update_totals(self):
        """Recalculate and display totals"""
        subtotal = sum(item.get_amount() for item in self.line_items)
        
        # Update each line item's amount display
        for item in self.line_items:
            item.update_amount_display()
        
        deposit = subtotal * 0.20
        remaining = subtotal - deposit
        
        try:
            weeks = int(self.weeks_var.get() or 1)
            if weeks < 1:
                weeks = 1
        except ValueError:
            weeks = 1
        
        weekly_payment = remaining / weeks if weeks > 0 else remaining
        
        self.subtotal_label.config(text=f"${subtotal:,.2f}")
        self.deposit_label.config(text=f"${deposit:,.2f}")
        self.weekly_label.config(text=f"${weekly_payment:,.2f}/week × {weeks} weeks")
    
    def add_attachments(self):
        """Add image or PDF attachments"""
        files = filedialog.askopenfilenames(
            title="Select Plans, Photos, or PDFs",
            filetypes=[
                ("All supported", "*.jpg *.jpeg *.png *.pdf *.JPG *.JPEG *.PNG *.PDF"),
                ("Images", "*.jpg *.jpeg *.png *.JPG *.JPEG *.PNG"),
                ("PDFs", "*.pdf *.PDF"),
                ("All files", "*.*")
            ]
        )
        
        for filepath in files:
            if filepath not in self.attachments:
                self.attachments.append(filepath)
                # Show just the filename in the listbox
                filename = os.path.basename(filepath)
                self.attachments_listbox.insert(tk.END, filename)
    
    def clear_attachments(self):
        """Clear all attachments"""
        self.attachments = []
        self.attachments_listbox.delete(0, tk.END)
    
    def manage_categories(self):
        """Open dialog to manage categories"""
        dialog = tk.Toplevel(self)
        dialog.title("Manage Categories")
        dialog.geometry("400x500")
        dialog.transient(self)
        dialog.grab_set()
        
        # Instructions
        ttk.Label(dialog, text="Add, remove, or reorder categories:", 
                  font=("Helvetica", 10)).pack(pady=(10, 5))
        
        # Listbox with scrollbar
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        cat_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, 
                                  selectmode=tk.SINGLE, font=("Helvetica", 11))
        cat_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=cat_listbox.yview)
        
        # Populate listbox
        for cat in self.categories:
            cat_listbox.insert(tk.END, cat)
        
        # Entry for new category
        entry_frame = ttk.Frame(dialog)
        entry_frame.pack(fill=tk.X, padx=10, pady=5)
        
        new_cat_var = tk.StringVar()
        new_cat_entry = ttk.Entry(entry_frame, textvariable=new_cat_var, width=30)
        new_cat_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        def add_category():
            new_cat = new_cat_var.get().strip()
            if new_cat and new_cat not in self.categories:
                # Insert before "Other" if it exists, otherwise at end
                if "Other" in self.categories:
                    idx = self.categories.index("Other")
                    self.categories.insert(idx, new_cat)
                    cat_listbox.insert(idx, new_cat)
                else:
                    self.categories.append(new_cat)
                    cat_listbox.insert(tk.END, new_cat)
                new_cat_var.set("")
            elif new_cat in self.categories:
                messagebox.showwarning("Duplicate", "Category already exists", parent=dialog)
        
        ttk.Button(entry_frame, text="Add", command=add_category).pack(side=tk.LEFT)
        
        # Bind Enter key to add
        new_cat_entry.bind("<Return>", lambda e: add_category())
        
        # Action buttons
        action_frame = ttk.Frame(dialog)
        action_frame.pack(fill=tk.X, padx=10, pady=5)
        
        def move_up():
            sel = cat_listbox.curselection()
            if sel and sel[0] > 0:
                idx = sel[0]
                # Swap in list
                self.categories[idx], self.categories[idx-1] = self.categories[idx-1], self.categories[idx]
                # Update listbox
                cat_listbox.delete(idx)
                cat_listbox.insert(idx-1, self.categories[idx-1])
                cat_listbox.selection_set(idx-1)
        
        def move_down():
            sel = cat_listbox.curselection()
            if sel and sel[0] < len(self.categories) - 1:
                idx = sel[0]
                # Swap in list
                self.categories[idx], self.categories[idx+1] = self.categories[idx+1], self.categories[idx]
                # Update listbox
                cat_listbox.delete(idx)
                cat_listbox.insert(idx+1, self.categories[idx+1])
                cat_listbox.selection_set(idx+1)
        
        def delete_category():
            sel = cat_listbox.curselection()
            if sel:
                idx = sel[0]
                cat_name = self.categories[idx]
                if messagebox.askyesno("Confirm", f"Delete category '{cat_name}'?", parent=dialog):
                    del self.categories[idx]
                    cat_listbox.delete(idx)
        
        def reset_defaults():
            if messagebox.askyesno("Confirm", "Reset to default categories?", parent=dialog):
                self.categories = self.DEFAULT_CATEGORIES.copy()
                cat_listbox.delete(0, tk.END)
                for cat in self.categories:
                    cat_listbox.insert(tk.END, cat)
        
        ttk.Button(action_frame, text="↑ Move Up", command=move_up).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="↓ Move Down", command=move_down).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="Delete", command=delete_category).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="Reset Defaults", command=reset_defaults).pack(side=tk.RIGHT, padx=2)
        
        # Save/Close buttons
        bottom_frame = ttk.Frame(dialog)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def save_and_close():
            self.save_categories()
            # Update all existing line item dropdowns
            for item in self.line_items:
                current_val = item.category_var.get()
                item.category_combo['values'] = self.categories
                if current_val in self.categories:
                    item.category_var.set(current_val)
            dialog.destroy()
            messagebox.showinfo("Saved", "Categories saved! New line items will use updated categories.")
        
        def cancel():
            # Reload from file to discard changes
            self.categories = self.load_categories()
            dialog.destroy()
        
        ttk.Button(bottom_frame, text="Save & Close", command=save_and_close).pack(side=tk.RIGHT, padx=5)
        ttk.Button(bottom_frame, text="Cancel", command=cancel).pack(side=tk.RIGHT, padx=5)
    
    def get_quote_data(self):
        """Collect all quote data"""
        subtotal = sum(item.get_amount() for item in self.line_items)
        deposit = subtotal * 0.20
        remaining = subtotal - deposit
        
        try:
            weeks = int(self.weeks_var.get() or 1)
        except ValueError:
            weeks = 1
        
        weekly_payment = remaining / weeks if weeks > 0 else remaining
        
        return {
            "quote_number": self.quote_num_var.get(),
            "date": self.date_var.get(),
            "valid_days": self.valid_days_var.get(),
            "weeks": weeks,
            "customer": {
                "name": self.cust_name_var.get(),
                "address": self.address_var.get(),
                "city": self.city_var.get(),
                "state": self.state_var.get(),
                "zip": self.zip_var.get(),
                "phone": self.phone_var.get(),
                "email": self.email_var.get()
            },
            "project_description": self.project_desc.get("1.0", tk.END).strip(),
            "line_items": [item.get_data() for item in self.line_items if item.get_data()["description"]],
            "subtotal": subtotal,
            "deposit": deposit,
            "remaining": remaining,
            "weekly_payment": weekly_payment,
            "notes": self.notes_text.get("1.0", tk.END).strip(),
            "attachments": self.attachments.copy()
        }
    
    def generate_pdf(self):
        """Generate a professional PDF quote"""
        data = self.get_quote_data()
        
        if not data["customer"]["name"]:
            messagebox.showerror("Error", "Please enter customer name")
            return
        
        if not data["line_items"]:
            messagebox.showerror("Error", "Please add at least one line item with a description")
            return
        
        # Ask where to save
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfilename=f"Quote_{data['quote_number']}_{data['customer']['name'].replace(' ', '_')}.pdf"
        )
        
        if not filename:
            return
        
        try:
            create_pdf_quote(data, filename)
            messagebox.showinfo("Success", f"Quote saved to:\n{filename}")
            
            # Open the PDF
            os.system(f'open "{filename}"')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create PDF: {str(e)}")
    
    def export_qbo_csv(self):
        """Export estimate for QuickBooks Online import"""
        data = self.get_quote_data()
        
        if not data["customer"]["name"]:
            messagebox.showerror("Error", "Please enter customer name")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfilename=f"QBO_Estimate_{data['quote_number']}.csv"
        )
        
        if not filename:
            return
        
        try:
            create_qbo_csv(data, filename)
            messagebox.showinfo("Success", 
                f"QuickBooks Online CSV saved to:\n{filename}\n\n"
                "To import:\n"
                "1. Go to QuickBooks Online\n"
                "2. Settings (gear icon) → Import Data\n"
                "3. Select 'Estimates' and upload this file")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create CSV: {str(e)}")
    
    def export_qb_iif(self):
        """Export estimate for QuickBooks Desktop import"""
        data = self.get_quote_data()
        
        if not data["customer"]["name"]:
            messagebox.showerror("Error", "Please enter customer name")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".iif",
            filetypes=[("IIF files", "*.iif")],
            initialfilename=f"QBD_Estimate_{data['quote_number']}.iif"
        )
        
        if not filename:
            return
        
        try:
            create_qb_iif(data, filename)
            messagebox.showinfo("Success", 
                f"QuickBooks Desktop IIF saved to:\n{filename}\n\n"
                "To import:\n"
                "1. Open QuickBooks Desktop\n"
                "2. File → Utilities → Import → IIF Files\n"
                "3. Select this file")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create IIF: {str(e)}")
    
    def clear_all(self):
        """Clear all fields"""
        if messagebox.askyesno("Confirm", "Clear all fields and start a new quote?"):
            self.quote_num_var.set(self.generate_quote_number())
            self.date_var.set(datetime.now().strftime("%m/%d/%Y"))
            self.cust_name_var.set("")
            self.address_var.set("")
            self.city_var.set("")
            self.state_var.set("")
            self.zip_var.set("")
            self.phone_var.set("")
            self.email_var.set("")
            self.project_desc.delete("1.0", tk.END)
            self.weeks_var.set("4")
            
            # Remove all line items except one
            for item in self.line_items[1:]:
                item.destroy()
            self.line_items = self.line_items[:1]
            
            # Clear the remaining item
            self.line_items[0].category_var.set("")
            self.line_items[0].desc_var.set("")
            self.line_items[0].qty_var.set("1")
            self.line_items[0].rate_var.set("0.00")
            
            # Clear attachments
            self.clear_attachments()
            
            self.update_totals()


def create_pdf_quote(data, filename):
    """Create a professional PDF quote with TBG branding"""
    from reportlab.platypus import Flowable
    
    class TBGLogoFlowable(Flowable):
        """TBG Logo as a Flowable"""
        def __init__(self, width=120, height=55):
            Flowable.__init__(self)
            self.width = width
            self.height = height
        
        def draw(self):
            # Red roof/chevron
            roof_width = 56
            roof_height = 14
            roof_x = (self.width - roof_width) / 2
            roof_y = self.height - roof_height - 2
            
            self.canv.setFillColor(TBG_RED)
            self.canv.setStrokeColor(TBG_RED)
            
            path = self.canv.beginPath()
            path.moveTo(roof_x, roof_y)
            path.lineTo(roof_x + roof_width/2, roof_y + roof_height)
            path.lineTo(roof_x + roof_width, roof_y)
            path.lineTo(roof_x + roof_width - 6, roof_y)
            path.lineTo(roof_x + roof_width/2, roof_y + roof_height - 6)
            path.lineTo(roof_x + 6, roof_y)
            path.close()
            self.canv.drawPath(path, fill=1, stroke=0)
            
            self.canv.setFillColor(TBG_BLACK)
            self.canv.setFont("Helvetica-Bold", 24)
            self.canv.drawCentredString(self.width/2, self.height - 38, "TBG")
            
            self.canv.setFillColor(TBG_RED)
            self.canv.setFont("Helvetica", 10)
            self.canv.drawCentredString(self.width/2, self.height - 50, "enterprises")
    
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    styles.add(ParagraphStyle(
        name='CompanyAddress',
        parent=styles['Normal'],
        fontSize=8,
        textColor=TBG_GRAY,
        alignment=TA_LEFT,
        spaceAfter=0
    ))
    
    styles.add(ParagraphStyle(
        name='CompanyName',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=TBG_RED,
        spaceAfter=2,
        alignment=TA_LEFT
    ))
    
    styles.add(ParagraphStyle(
        name='QuoteTitle',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=TBG_BLACK,
        spaceAfter=20,
        alignment=TA_LEFT
    ))
    
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading3'],
        fontSize=11,
        textColor=TBG_RED,
        spaceBefore=15,
        spaceAfter=5,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='TBGBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor=TBG_GRAY,
        spaceAfter=3
    ))
    
    styles.add(ParagraphStyle(
        name='SmallText',
        parent=styles['Normal'],
        fontSize=8,
        textColor=TBG_GRAY
    ))
    
    styles.add(ParagraphStyle(
        name='QuoteNumber',
        parent=styles['Normal'],
        fontSize=16,
        textColor=TBG_BLACK,
        alignment=TA_RIGHT
    ))
    
    story = []
    
    # Header with logo and quote number
    logo = TBGLogoFlowable(width=120, height=55)
    
    header_data = [
        [logo, 
         Paragraph(f"<b>ESTIMATE</b><br/><font size=10>#{data['quote_number']}</font>", 
                   styles['QuoteNumber'])]
    ]
    
    header_table = Table(header_data, colWidths=[4*inch, 3*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    story.append(header_table)
    
    # Company contact info
    story.append(Paragraph(f"{COMPANY_ADDRESS}  |  {COMPANY_PHONE}  |  {COMPANY_EMAIL}", styles['CompanyAddress']))
    
    # Red line separator
    story.append(Spacer(1, 8))
    separator_data = [[""]]
    separator = Table(separator_data, colWidths=[7.5*inch])
    separator.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 3, TBG_RED),
    ]))
    story.append(separator)
    story.append(Spacer(1, 15))
    
    # Quote details and customer info side by side
    quote_details = f"""
    <b>Date:</b> {data['date']}<br/>
    <b>Valid Until:</b> {calculate_valid_date(data['date'], data['valid_days'])}<br/>
    <b>Estimated Duration:</b> {data['weeks']} weeks
    """
    
    customer_info = f"""
    <b>{data['customer']['name']}</b><br/>
    {data['customer']['address']}<br/>
    {data['customer']['city']}, {data['customer']['state']} {data['customer']['zip']}
    """
    if data['customer']['phone']:
        customer_info += f"<br/>{data['customer']['phone']}"
    if data['customer']['email']:
        customer_info += f"<br/>{data['customer']['email']}"
    
    info_data = [
        [Paragraph(quote_details, styles['TBGBody']),
         Paragraph(customer_info, styles['TBGBody'])]
    ]
    
    info_table = Table(info_data, colWidths=[3.5*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 15))
    
    # Project Description
    if data['project_description']:
        story.append(Paragraph("PROJECT DESCRIPTION", styles['SectionHeader']))
        story.append(Paragraph(data['project_description'], styles['TBGBody']))
        story.append(Spacer(1, 10))
    
    # Line Items Table
    story.append(Paragraph("SCOPE OF WORK", styles['SectionHeader']))
    
    # Table header
    table_data = [
        [Paragraph("<b>Category</b>", styles['SmallText']),
         Paragraph("<b>Description</b>", styles['SmallText']),
         Paragraph("<b>Qty</b>", styles['SmallText']),
         Paragraph("<b>Unit</b>", styles['SmallText']),
         Paragraph("<b>Rate</b>", styles['SmallText']),
         Paragraph("<b>Amount</b>", styles['SmallText'])]
    ]
    
    # Line items
    for item in data['line_items']:
        table_data.append([
            Paragraph(item['category'], styles['SmallText']),
            Paragraph(item['description'], styles['SmallText']),
            Paragraph(str(item['quantity']), styles['SmallText']),
            Paragraph(item['unit'], styles['SmallText']),
            Paragraph(f"${float(item['rate'] or 0):,.2f}", styles['SmallText']),
            Paragraph(f"${item['amount']:,.2f}", styles['SmallText'])
        ])
    
    items_table = Table(table_data, colWidths=[1*inch, 2.8*inch, 0.5*inch, 0.5*inch, 0.9*inch, 0.9*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TBG_BLACK),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, TBG_LIGHT_GRAY]),
        ('GRID', (0, 0), (-1, -1), 0.5, TBG_GRAY),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 15))
    
    # Totals
    totals_data = [
        ["", "", "", "", Paragraph("<b>Subtotal:</b>", styles['TBGBody']), 
         Paragraph(f"<b>${data['subtotal']:,.2f}</b>", styles['TBGBody'])],
    ]
    
    totals_table = Table(totals_data, colWidths=[1*inch, 2.8*inch, 0.5*inch, 0.5*inch, 0.9*inch, 0.9*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (4, 0), (-1, -1), 'RIGHT'),
        ('LINEABOVE', (4, 0), (-1, 0), 1, TBG_BLACK),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 20))
    
    # Payment Schedule
    story.append(Paragraph("PAYMENT SCHEDULE", styles['SectionHeader']))
    
    payment_data = [
        [Paragraph("<b>Payment</b>", styles['SmallText']),
         Paragraph("<b>When</b>", styles['SmallText']),
         Paragraph("<b>Amount</b>", styles['SmallText'])],
        [Paragraph("Deposit (20%)", styles['SmallText']),
         Paragraph("Upon acceptance", styles['SmallText']),
         Paragraph(f"${data['deposit']:,.2f}", styles['SmallText'])],
    ]
    
    # Add weekly payments
    for week in range(1, data['weeks'] + 1):
        payment_data.append([
            Paragraph(f"Payment {week}", styles['SmallText']),
            Paragraph(f"Week {week}", styles['SmallText']),
            Paragraph(f"${data['weekly_payment']:,.2f}", styles['SmallText'])
        ])
    
    # Total row
    payment_data.append([
        Paragraph("<b>TOTAL</b>", styles['SmallText']),
        Paragraph("", styles['SmallText']),
        Paragraph(f"<b>${data['subtotal']:,.2f}</b>", styles['SmallText'])
    ])
    
    payment_table = Table(payment_data, colWidths=[2*inch, 2.5*inch, 1.5*inch])
    payment_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TBG_BLACK),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, TBG_GRAY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [white, TBG_LIGHT_GRAY]),
        ('BACKGROUND', (0, -1), (-1, -1), TBG_LIGHT_GRAY),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(payment_table)
    story.append(Spacer(1, 20))
    
    # Notes/Terms
    if data['notes']:
        story.append(Paragraph("TERMS & CONDITIONS", styles['SectionHeader']))
        for line in data['notes'].split('\n'):
            if line.strip():
                story.append(Paragraph(line, styles['SmallText']))
        story.append(Spacer(1, 20))
    
    # Signature section
    story.append(Spacer(1, 30))
    
    sig_data = [
        [Paragraph("ACCEPTED BY:", styles['TBGBody']), "", 
         Paragraph("TBG ENTERPRISES:", styles['TBGBody']), ""],
        ["_" * 35, "", "_" * 35, ""],
        [Paragraph("Customer Signature", styles['SmallText']), 
         Paragraph("Date", styles['SmallText']),
         Paragraph("Authorized Signature", styles['SmallText']),
         Paragraph("Date", styles['SmallText'])],
    ]
    
    sig_table = Table(sig_data, colWidths=[2.5*inch, 1*inch, 2.5*inch, 1*inch])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('TOPPADDING', (0, 1), (-1, 1), 30),
    ]))
    story.append(sig_table)
    
    # Attachments (Plans, Images) - on new pages
    attachments = data.get('attachments', [])
    if attachments:
        from reportlab.platypus import PageBreak
        from PIL import Image as PILImage
        import fitz  # PyMuPDF for PDF handling
        
        story.append(PageBreak())
        story.append(Paragraph("ATTACHED PLANS & DOCUMENTS", styles['SectionHeader']))
        story.append(Spacer(1, 10))
        
        for i, filepath in enumerate(attachments):
            filename = os.path.basename(filepath)
            ext = os.path.splitext(filepath)[1].lower()
            
            story.append(Paragraph(f"<b>Attachment {i+1}:</b> {filename}", styles['SmallText']))
            story.append(Spacer(1, 5))
            
            try:
                if ext in ['.jpg', '.jpeg', '.png']:
                    # Handle images
                    with PILImage.open(filepath) as pil_img:
                        img_width, img_height = pil_img.size
                    
                    # Scale to fit page (max 7" wide, 9" tall)
                    max_width = 7 * inch
                    max_height = 9 * inch
                    
                    scale = min(max_width / img_width, max_height / img_height, 1.0)
                    display_width = img_width * scale
                    display_height = img_height * scale
                    
                    img = Image(filepath, width=display_width, height=display_height)
                    story.append(img)
                    story.append(Spacer(1, 20))
                    
                elif ext == '.pdf':
                    # Handle PDFs - convert pages to images
                    pdf_doc = fitz.open(filepath)
                    for page_num in range(len(pdf_doc)):
                        page = pdf_doc[page_num]
                        # Render at 150 DPI for good quality
                        mat = fitz.Matrix(150/72, 150/72)
                        pix = page.get_pixmap(matrix=mat)
                        
                        # Save to temp file
                        import tempfile
                        temp_img = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                        pix.save(temp_img.name)
                        
                        # Scale to fit page
                        max_width = 7 * inch
                        max_height = 9 * inch
                        
                        scale = min(max_width / pix.width, max_height / pix.height, 1.0)
                        display_width = pix.width * scale
                        display_height = pix.height * scale
                        
                        img = Image(temp_img.name, width=display_width, height=display_height)
                        
                        if page_num > 0:
                            story.append(Paragraph(f"<i>(Page {page_num + 1} of {filename})</i>", styles['SmallText']))
                        
                        story.append(img)
                        story.append(Spacer(1, 10))
                        
                        # Clean up temp file
                        temp_img.close()
                        os.unlink(temp_img.name)
                    
                    pdf_doc.close()
                    story.append(Spacer(1, 20))
                    
            except Exception as e:
                story.append(Paragraph(f"<i>Could not embed attachment: {str(e)}</i>", styles['SmallText']))
                story.append(Spacer(1, 10))
    
    # Build PDF
    doc.build(story)


def calculate_valid_date(date_str, days):
    """Calculate expiration date"""
    try:
        date = datetime.strptime(date_str, "%m/%d/%Y")
        valid_until = date + timedelta(days=int(days))
        return valid_until.strftime("%m/%d/%Y")
    except:
        return "30 days from date"


def create_qbo_csv(data, filename):
    """Create CSV for QuickBooks Online import"""
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header row for QBO estimate import
        writer.writerow([
            'Customer',
            'EstimateNumber',
            'EstimateDate',
            'ExpirationDate',
            'ItemDescription',
            'ItemQuantity',
            'ItemRate',
            'ItemAmount',
            'Memo'
        ])
        
        valid_date = calculate_valid_date(data['date'], data['valid_days'])
        
        # Write each line item as a row
        for i, item in enumerate(data['line_items']):
            writer.writerow([
                data['customer']['name'],
                data['quote_number'],
                data['date'],
                valid_date,
                f"{item['category']}: {item['description']}",
                item['quantity'],
                float(item['rate'] or 0),
                item['amount'],
                data['project_description'] if i == 0 else ""
            ])


def create_qb_iif(data, filename):
    """Create IIF file for QuickBooks Desktop import"""
    with open(filename, 'w', encoding='utf-8') as f:
        # IIF Header for estimates
        f.write("!TRNS\tTRNSTYPE\tDATE\tACCNT\tNAME\tCLASS\tAMOUNT\tDOCNUM\tMEMO\n")
        f.write("!SPL\tTRNSTYPE\tDATE\tACCNT\tNAME\tAMOUNT\tDOCNUM\tMEMO\tQNTY\tPRICE\n")
        f.write("!ENDTRNS\n")
        
        # Format date for IIF (MM/DD/YYYY)
        trns_date = data['date']
        
        # Main transaction line
        f.write(f"TRNS\tESTIMATE\t{trns_date}\tAccounts Receivable\t{data['customer']['name']}\t\t{data['subtotal']:.2f}\t{data['quote_number']}\t{data['project_description'][:50] if data['project_description'] else ''}\n")
        
        # Split lines for each item
        for item in data['line_items']:
            item_desc = f"{item['category']}: {item['description']}"
            f.write(f"SPL\tESTIMATE\t{trns_date}\tServices\t{data['customer']['name']}\t-{item['amount']:.2f}\t{data['quote_number']}\t{item_desc[:50]}\t{item['quantity']}\t{float(item['rate'] or 0):.2f}\n")
        
        f.write("ENDTRNS\n")


if __name__ == "__main__":
    app = TBGQuoteBuilder()
    app.mainloop()
