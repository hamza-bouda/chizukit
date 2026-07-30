from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    main_image = models.ImageField(upload_to='products/')
    category = models.CharField(max_length=100)
    brand = models.CharField(max_length=100)
    sponsor = models.CharField(max_length=100, null=True, blank=True)
    size = models.CharField(max_length=10)
    customization = models.CharField(max_length=100, null=True, blank=True)
    sleeve_type = models.CharField(max_length=100)
    seasons = models.CharField(max_length=100)
    quality_rating = models.CharField(max_length=10)
    is_new = models.BooleanField(default=False)
    is_iconic = models.BooleanField(default=False)
    is_sold = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')

from django.contrib.sessions.models import Session

class Cart(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f'Cart for {self.user.username}'
        return f'Cart for session {self.session_key}'

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

class Order(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100,default='')
    last_name = models.CharField(max_length=100,default='')
    email = models.EmailField(default='default@example.com')  # Ajouter le champ email
    telephone = models.CharField(max_length=15, default='0000000000')  # Ajouter le champ telephone
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    bank_transfer_image = models.ImageField(upload_to='bank_transfers/', null=True, blank=True)


    def __str__(self):
        return f'Order {self.id}'

    def get_total(self):
        return sum(item.price for item in self.items.all())
    
    def get_shipping_cost(self):
        return Decimal('45.00') # Exemple de coût fixe de livraison
    
    def get_tax(self):
        return Decimal('0.95')  # Exemple de taux de taxe fixe
    
    def get_grand_total(self):
        return self.get_total() + self.get_shipping_cost() + self.get_tax()

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return str(self.id)

class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Review by {self.user.username} for {self.product.name}'
