from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


# ===============================
# Branch Model
# ===============================
class Branch(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# ===============================
# Custom User Model
# ===============================
class User_profile(AbstractUser):
    branches = models.ManyToManyField(Branch)
    is_salesagent = models.BooleanField(default=False)
    is_manager = models.BooleanField(default=False)
    is_owner = models.BooleanField(default=False)

    username = models.CharField(
        _("username"),
        max_length=100,
        unique=True,
        null=True,
        blank=True,
    )

    email = models.EmailField(_("email address"), unique=True)
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.username if self.username else self.email


# ===============================
# Category Model
# ===============================
class Category(models.Model):
    category_name = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.category_name if self.category_name else "Unnamed Category"


# ===============================
# Stock Model (with image field)
# ===============================
class Stock(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    category_name = models.ForeignKey(
        Category, on_delete=models.SET_NULL, blank=True, null=True
    )
    item_name = models.CharField(max_length=100, blank=True, null=True)
    sku = models.CharField(max_length=50, unique=True, blank=True, null=True)  # Added SKU field
    product_quantity = models.IntegerField(default=0, blank=True, null=True)
    cost = models.IntegerField(default=0, blank=True, null=True)
    issued_quantity = models.CharField(max_length=100, null=True, blank=True)
    total_quantity = models.CharField(max_length=100, null=True, blank=True)
    type_of_stock = models.CharField(max_length=100, blank=True, null=True)
    supplier_name = models.CharField(max_length=15, blank=True, null=True)
    unit_of_measure = models.CharField(max_length=20, default="kg", blank=True, null=True)  # KG, units, liters, etc.
    low_stock_threshold = models.IntegerField(default=10, blank=True, null=True)  # Custom threshold per item
    date_added = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(default=timezone.now)

    # 📸 Image for cereals or products
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)

    def __str__(self):
        return self.item_name if self.item_name else "Unnamed Stock"
    
    def get_stock_status(self):
        """Return stock status based on quantity and custom threshold"""
        threshold = self.low_stock_threshold or 10  # Default to 10 if not set
        if self.product_quantity == 0:
            return "Out of Stock"
        elif self.product_quantity < threshold:
            return "Low Stock"
        else:
            return "In Stock"
    
    def get_status_color(self):
        """Return Bootstrap color class based on stock status"""
        status = self.get_stock_status()
        if status == "Out of Stock":
            return "danger"
        elif status == "Low Stock":
            return "warning"
        else:
            return "success"
    
    def get_quantity_with_unit(self):
        """Return quantity with unit of measure (e.g., '50 kg', '10 units')"""
        unit = self.unit_of_measure or "units"
        return f"{self.product_quantity} {unit}" if self.product_quantity else f"0 {unit}"
    
    def get_low_stock_warning(self):
        """Return low stock warning message with threshold"""
        threshold = self.low_stock_threshold or 10
        unit = self.unit_of_measure or "units"
        if self.product_quantity < threshold and self.product_quantity > 0:
            return f"Low stock: Only {self.product_quantity} {unit} left (threshold: {threshold} {unit})"
        return ""


# ===============================
# Sale Model
# ===============================
class Sale(models.Model):
    PAYMENT_CHOICES = [
        ("Cash", "Cash"),
        ("Credit", "Credit"),
        ("mobile money", "mobile money"),
    ]

    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.ForeignKey(Stock, on_delete=models.SET_NULL, null=True)
    product_quantity = models.IntegerField(default=0, blank=True, null=True)
    unit_price = models.IntegerField(default=0, blank=True, null=True)
    amount_recieved = models.IntegerField(default=0, blank=True, null=True)
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_CHOICES, blank=True, null=True
    )
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    sales_date = models.DateTimeField(null=False, default=timezone.now)
    sales_agent = models.ForeignKey(User_profile, on_delete=models.SET_NULL, null=True)
    confirm_quantity = models.CharField(max_length=100, null=True, blank=True)

    def get_sales(self):
        if self.product_quantity and self.unit_price:
            return self.product_quantity * self.unit_price
        return 0

    def change_sales(self):
        if self.amount_recieved and self.unit_price:
            return abs(self.amount_recieved - self.get_sales())
        return 0

    def get_available_quantity(self):
        if not hasattr(self, "issued_quantity"):
            return self.product_quantity

        try:
            issued = int(self.issued_quantity or 0)
            return self.product_quantity - issued
        except ValueError:
            return self.product_quantity

    def __str__(self):
        return f"Sale to {self.customer_name}" if self.customer_name else "Unnamed Sale"

def save(self, *args, **kwargs):
    if self.product_name and self.product_quantity:
        stock_item = self.product_name

        # Check if enough stock exists
        if stock_item.product_quantity >= self.product_quantity:
            # Deduct the sold quantity from stock
            stock_item.product_quantity -= self.product_quantity
            stock_item.save()
        else:
            raise ValueError(f"Not enough stock for {stock_item.item_name}")

    super().save(*args, **kwargs)

# ===============================
# Credit Model
# ===============================
class Credit(models.Model):
    STATUS_CHOICES = [("Pending", "Pending"), ("Paid", "Paid")]

    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=10, blank=True, null=True)
    product_quantity = models.IntegerField(default=5, blank=True, null=True)
    product_type = models.CharField(max_length=50, blank=True, null=True)
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    national_id = models.CharField(max_length=25, blank=True, null=True)
    contact = models.CharField(max_length=15, blank=True, null=True)
    due_amount = models.IntegerField(default=0, blank=True, null=True)
    due_date = models.DateField(auto_now_add=True, blank=True, null=True)
    dispatch_date = models.DateField(auto_now_add=True, blank=True, null=True)
    approved_by = models.ForeignKey(User_profile, on_delete=models.SET_NULL, null=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="Pending", blank=True, null=True
    )

    def __str__(self):
        return f"Credit for {self.customer_name}" if self.customer_name else "Unnamed Credit"


# ===============================
# Receipt Model
# ===============================
class Receipt(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateField(auto_now_add=True, blank=True, null=True)
    total_amount = models.IntegerField(default=0, blank=True, null=True)

    def __str__(self):
        return (
            f"Receipt for {self.customer_name} on {self.date}"
            if self.customer_name and self.date
            else "Unnamed Receipt"
        )


# ===============================
# Buying Model
# ===============================
class Buying(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=100, blank=True, null=True)
    type_of_product = models.CharField(max_length=50, blank=True, null=True)
    date = models.DateField(auto_now_add=True)
    product_quantity = models.IntegerField(default=0, blank=True, null=True)
    cost = models.IntegerField(default=0, blank=True, null=True)
    dealers_name = models.CharField(max_length=100, blank=True, null=True)
    contact = models.CharField(max_length=15, blank=True, null=True)
    sell_price = models.IntegerField(default=0, blank=True, null=True)

    def __str__(self):
        return (
            f"Purchase of {self.product_name}"
            if self.product_name
            else "Unnamed Purchase"
        )
