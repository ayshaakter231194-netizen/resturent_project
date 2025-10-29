from django.db import models
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class FoodItem(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='foods')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='foods/', blank=True, null=True)
    is_available = models.BooleanField(default=True)  # availability
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.category.name})"

class Customer(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, default='Dhaka')  # keep simple

    def __str__(self):
        return f"{self.name} - {self.phone}"

class Order(models.Model):
    PAYMENT_METHODS = (
        ('COD', 'Cash on Delivery'),
    )
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(default=timezone.now)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    inside_dhaka = models.BooleanField(default=True)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, default='COD')
    note = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Order #{self.id} - {self.customer.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    food = models.ForeignKey(FoodItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price_at_order = models.DecimalField(max_digits=8, decimal_places=2)  # snapshot

    def __str__(self):
        return f"{self.quantity} x {self.food.name}"
