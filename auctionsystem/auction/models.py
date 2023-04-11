import email
from django.db import models
from django.contrib import auth
from django.utils import timezone
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator

class Item(models.Model):
    static_id = models.UUIDField(max_length=48, unique=True, default=uuid.uuid4, editable=False, primary_key=True)
    name = models.CharField(max_length=100, null = False)
    description = models.TextField(default = None)
    minimum_bid = models.IntegerField(null = False)
    reserve_price = models.IntegerField(null = False)
    end_time = models.DateTimeField(null = False)
    is_sold = models.BooleanField(default=False, null = False)
    is_live = models.BooleanField(default = True, null = False)
    start_time = models.DateTimeField(auto_now_add=True)
    bid_increment = models.IntegerField(null = False)
    category = models.ForeignKey("Category", on_delete = models.CASCADE, related_name="category_items")
    current_bid = models.IntegerField()
    added_by = models.ForeignKey("Admin", on_delete = models.CASCADE, related_name="admin_items")

    class Meta:
        db_table = "item"
    
    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=30)
    static_id = models.UUIDField( max_length=48, unique=True, default=uuid.uuid4, editable=False, primary_key=True)

    class Meta:
        db_table = "category"

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    static_id = models.UUIDField( max_length=48, unique=True, default=uuid.uuid4, editable=False, primary_key=True)
    email =  models.CharField(max_length=100)
    password = models.CharField(max_length=50, null = False)
    registration_date = models.DateField(auto_now_add = True)
    age = models.IntegerField(null = False)

    class Meta:
        db_table = "UserProfile"
    
    def __str__(self):
        return self.email

class Admin(models.Model):
    static_id = models.UUIDField( max_length=48, unique=True, default=uuid.uuid4, editable=False, primary_key=True)
    email =  models.CharField(max_length=100)
    password = models.CharField(max_length=50, null = False)
    age = models.IntegerField(null = False)

    class Meta:
        db_table = "Admin"

    def __str__(self):
        return self.email
    
class Bid(models.Model):
    static_id = models.UUIDField( max_length=48, unique=True, default=uuid.uuid4, editable=False,  primary_key=True)
    amount = models.IntegerField()
    placed_at = models.DateTimeField(auto_now_add=True)
    item = models.ForeignKey("Item", on_delete=models.CASCADE, related_name="item_bids")
    placed_by = models.ForeignKey("UserProfile", on_delete=models.CASCADE, related_name="user_bids")

    class Meta:
        db_table = "Bid"
    
    def __str__(self):
        return self.item.name + "-" + self.placed_by.email

class ItemImage(models.Model):
    item = models.ForeignKey("Item", on_delete=models.CASCADE, related_name="item_images")
    image = models.ImageField(upload_to = "images/all/")

    class Meta :
        db_table = "itemimages"
    
    def __str__(self):
        return self.item.name
