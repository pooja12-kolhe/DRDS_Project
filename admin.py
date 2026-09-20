from django.contrib import admin
from .models import User, Stock, Distribution
from .models import OTP

admin.site.register(User)
admin.site.register(Stock)
admin.site.register(Distribution)
admin.site.register(OTP)