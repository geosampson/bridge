"""
New Product Creation Dialog

Allows creating new WooCommerce products from Capital data with manual image upload.
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image
import os


class NewProductDialog(ctk.CTkToplevel):
    """Dialog for creating new WooCommerce products from Capital data"""
    
    def __init__(self, parent, capital_product, woo_client, db):
        super().__init__(parent)
        
        self.parent = parent
        self.capital_product = capital_product
        self.woo_client = woo_client
        self.db = db
        self.uploaded_images = []
        
        self.title(f"Create New Product - {capital_product.get('CODE', '')}")
        self.geometry("900x700")
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui()
        self.populate_from_capital()
        
    def setup_ui(self):
        """Setup the dialog UI"""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Main frame with scrollbar
        main_frame = ctk.CTkScrollableFrame(self, label_text="New Product Information")
        main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        main_frame.grid_columnconfigure(1, weight=1)
        
        row = 0
        
        # Capital Information (Read-only)
        ctk.CTkLabel(main_frame, text="Capital ERP Data", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=row, column=0, columnspan=2, pady=(0, 10), sticky="w"
        )
        row += 1
        
        ctk.CTkLabel(main_frame, text="SKU/CODE:").grid(row=row, column=0, sticky="w", pady=5)
        self.capital_code_label = ctk.CTkLabel(main_frame, text="", font=ctk.CTkFont(weight="bold"))
        self.capital_code_label.grid(row=row, column=1, sticky="w", pady=5)
        row += 1
        
        ctk.CTkLabel(main_frame, text="Description:").grid(row=row, column=0, sticky="w", pady=5)
        self.capital_descr_label = ctk.CTkLabel(main_frame, text="", wraplength=500)
        self.capital_descr_label.grid(row=row, column=1, sticky="w", pady=5)
        row += 1
        
        ctk.CTkLabel(main_frame, text="Retail Price:").grid(row=row, column=0, sticky="w", pady=5)
        self.capital_price_label = ctk.CTkLabel(main_frame, text="", font=ctk.CTkFont(weight="bold"))
        self.capital_price_label.grid(row=row, column=1, sticky="w", pady=5)
        row += 1
        
        ctk.CTkLabel(main_frame, text="Stock:").grid(row=row, column=0, sticky="w", pady=5)
        self.capital_stock_label = ctk.CTkLabel(main_frame, text="")
        self.capital_stock_label.grid(row=row, column=1, sticky="w", pady=5)
        row += 1
        
        # Separator
        ctk.CTkLabel(main_frame, text="").grid(row=row, column=0, columnspan=2, pady=10)
        row += 1
        
        # WooCommerce Product Data (Editable)
        ctk.CTkLabel(main_frame, text="WooCommerce Product", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=row, column=0, columnspan=2, pady=(0, 10), sticky="w"
        )
        row += 1
        
        ctk.CTkLabel(main_frame, text="Product Name:*").grid(row=row, column=0, sticky="w", pady=5)
        self.name_entry = ctk.CTkEntry(main_frame, width=400)
        self.name_entry.grid(row=row, column=1, sticky="ew", pady=5)
        row += 1
        
        ctk.CTkLabel(main_frame, text="SKU:*").grid(row=row, column=0, sticky="w", pady=5)
        self.sku_entry = ctk.CTkEntry(main_frame, width=400)
        self.sku_entry.grid(row=row, column=1, sticky="ew", pady=5)
        row += 1
        
        ctk.CTkLabel(main_frame, text="Regular Price (€):*").grid(row=row, column=0, sticky="w", pady=5)
        self.price_entry = ctk.CTkEntry(main_frame, width=150)
        self.price_entry.grid(row=row, column=1, sticky="w", pady=5)
        row += 1
        
        ctk.CTkLabel(main_frame, text="Sale Price (€):").grid(row=row, column=0, sticky="w", pady=5)
        self.sale_price_entry = ctk.CTkEntry(main_frame, width=150, placeholder_text="Optional")
        self.sale_price_entry.grid(row=row, column=1, sticky="w", pady=5)
        row += 1
        
        ctk.CTkLabel(main_frame, text="Stock Quantity:").grid(row=row, column=0, sticky="w", pady=5)
        self.stock_entry = ctk.CTkEntry(main_frame, width=150)
        self.stock_entry.grid(row=row, column=1, sticky="w", pady=5)
        row += 1
        
        ctk.CTkLabel(main_frame, text="Short Description:").grid(row=row, column=0, sticky="nw", pady=5)
        self.short_desc_text = ctk.CTkTextbox(main_frame, width=400, height=80)
        self.short_desc_text.grid(row=row, column=1, sticky="ew", pady=5)
        row += 1
        
        ctk.CTkLabel(main_frame, text="Description:").grid(row=row, column=0, sticky="nw", pady=5)
        self.desc_text = ctk.CTkTextbox(main_frame, width=400, height=150)
        self.desc_text.grid(row=row, column=1, sticky="ew", pady=5)
        row += 1
        
        # Product Images
        ctk.CTkLabel(main_frame, text="Product Images:").grid(row=row, column=0, sticky="nw", pady=5)
        images_frame = ctk.CTkFrame(main_frame)
        images_frame.grid(row=row, column=1, sticky="ew", pady=5)
        
        ctk.CTkButton(
            images_frame,
            text="📷 Upload Images",
            command=self.upload_images,
            width=150
        ).pack(side="left", padx=5)
        
        self.images_label = ctk.CTkLabel(images_frame, text="No images uploaded")
        self.images_label.pack(side="left", padx=10)
        row += 1
        
        # Product Status
        ctk.CTkLabel(main_frame, text="Status:").grid(row=row, column=0, sticky="w", pady=5)
        self.status_var = ctk.StringVar(value="publish")
        status_frame = ctk.CTkFrame(main_frame)
        status_frame.grid(row=row, column=1, sticky="w", pady=5)
        
        ctk.CTkRadioButton(status_frame, text="Publish", variable=self.status_var, value="publish").pack(side="left", padx=5)
        ctk.CTkRadioButton(status_frame, text="Draft", variable=self.status_var, value="draft").pack(side="left", padx=5)
        row += 1
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        ctk.CTkButton(
            button_frame,
            text="✓ Create Product",
            command=self.create_product,
            fg_color="green",
            hover_color="darkgreen",
            width=150
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="✕ Cancel",
            command=self.destroy,
            fg_color="gray",
            hover_color="darkgray",
            width=150
        ).pack(side="left", padx=5)
        
    def populate_from_capital(self):
        """Populate fields with Capital data"""
        # Capital info (read-only labels)
        self.capital_code_label.configure(text=self.capital_product.get('CODE', ''))
        self.capital_descr_label.configure(text=self.capital_product.get('DESCR', ''))
        self.capital_price_label.configure(text=f"€{float(self.capital_product.get('RTLPRICE', 0)):.2f}")
        self.capital_stock_label.configure(text=str(int(float(self.capital_product.get('BALANCEQTY', 0)))))
        
        # Pre-fill WooCommerce fields
        self.name_entry.insert(0, self.capital_product.get('DESCR', ''))
        self.sku_entry.insert(0, self.capital_product.get('CODE', ''))
        self.price_entry.insert(0, str(float(self.capital_product.get('RTLPRICE', 0))))
        self.stock_entry.insert(0, str(int(float(self.capital_product.get('BALANCEQTY', 0)))))
        self.short_desc_text.insert("1.0", self.capital_product.get('DESCR', ''))
        
    def upload_images(self):
        """Upload product images"""
        files = filedialog.askopenfilenames(
            title="Select Product Images",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.gif *.webp"),
                ("All files", "*.*")
            ]
        )
        
        if files:
            self.uploaded_images = list(files)
            self.images_label.configure(text=f"{len(files)} image(s) selected")
            
    def create_product(self):
        """Create the product in WooCommerce"""
        # Validate required fields
        name = self.name_entry.get().strip()
        sku = self.sku_entry.get().strip()
        price = self.price_entry.get().strip()
        
        if not name:
            messagebox.showerror("Error", "Product name is required")
            return
        
        if not sku:
            messagebox.showerror("Error", "SKU is required")
            return
        
        if not price:
            messagebox.showerror("Error", "Regular price is required")
            return
        
        try:
            regular_price = float(price)
            if regular_price < 0:
                raise ValueError("Price cannot be negative")
        except ValueError:
            messagebox.showerror("Error", "Invalid regular price")
            return
        
        # Get optional fields
        sale_price_str = self.sale_price_entry.get().strip()
        sale_price = None
        if sale_price_str:
            try:
                sale_price = float(sale_price_str)
            except ValueError:
                messagebox.showerror("Error", "Invalid sale price")
                return
        
        stock_str = self.stock_entry.get().strip()
        stock_quantity = None
        if stock_str:
            try:
                stock_quantity = int(float(stock_str))
            except ValueError:
                messagebox.showerror("Error", "Invalid stock quantity")
                return
        
        short_description = self.short_desc_text.get("1.0", "end-1c").strip()
        description = self.desc_text.get("1.0", "end-1c").strip()
        status = self.status_var.get()
        
        # Confirm creation
        if not messagebox.askyesno(
            "Confirm Creation",
            f"Create new product in WooCommerce?\n\n"
            f"Name: {name}\n"
            f"SKU: {sku}\n"
            f"Price: €{regular_price:.2f}\n"
            f"Images: {len(self.uploaded_images)}\n"
            f"Status: {status}"
        ):
            return
        
        try:
            # Prepare product data
            product_data = {
                'name': name,
                'sku': sku,
                'regular_price': str(regular_price),
                'status': status,
                # Hide stock from customers but track internally
                'manage_stock': False,  # Don't show stock to customers
                'stock_status': 'instock',  # Always show as in stock
            }
            
            if sale_price is not None:
                product_data['sale_price'] = str(sale_price)
            
            if stock_quantity is not None:
                product_data['stock_quantity'] = stock_quantity
            
            if short_description:
                product_data['short_description'] = short_description
            
            if description:
                product_data['description'] = description
            
            # Upload images first if any
            if self.uploaded_images:
                images = []
                for img_path in self.uploaded_images:
                    # TODO: Upload image to WooCommerce media library
                    # For now, just add as external URL if possible
                    images.append({'src': img_path})
                
                product_data['images'] = images
            
            # Create product in WooCommerce
            response = self.woo_client.create_product(product_data)
            
            if response:
                # Save match to database
                self.db.save_product_match(
                    capital_sku=self.capital_product.get('CODE', ''),
                    woo_id=response['id'],
                    woo_sku=sku,
                    match_type='created',
                    confidence=100.0,
                    matched_by='user'
                )
                
                messagebox.showinfo(
                    "Success",
                    f"Product created successfully!\n\n"
                    f"WooCommerce ID: {response['id']}\n"
                    f"SKU: {sku}\n\n"
                    f"The product is now available in your store."
                )
                
                self.destroy()
            else:
                messagebox.showerror("Error", "Failed to create product")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create product:\n{str(e)}")
