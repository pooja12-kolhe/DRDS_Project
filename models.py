from django.db import models
from django.utils.timezone import now
from datetime import datetime

class User(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('shopkeeper', 'Shopkeeper'),
        ('user', 'User'),
    )

    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15)
    email = models.EmailField(null=True, blank=True)
    password = models.CharField(max_length=100)
    ration_card_no = models.CharField(max_length=50)
    address = models.TextField()
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return self.name


class Stock(models.Model):
    item_name = models.CharField(max_length=50)
    quantity = models.IntegerField()
    available_from = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        return self.item_name


class Distribution(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=50)
    quantity = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.item_name


class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.otp

class FamilyMember(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    age = models.IntegerField()

    def __str__(self):
        return self.name
    
class Notification(models.Model):
    message = models.TextField()
    created_at = models.DateTimeField(default=now)
    show_from = models.DateTimeField(default=now)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return self.message   
    
  