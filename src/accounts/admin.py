from django.contrib import admin
from .models import Customer, Tag, Order, UserInfoExtend, Notification, Customer, Payment, Receipient, Rider, Counter

# Register your models here.
admin.site.register(Customer)
admin.site.register(Notification)
admin.site.register(Tag)
admin.site.register(Order)
admin.site.register(UserInfoExtend)
admin.site.register(Payment)
admin.site.register(Receipient)
admin.site.register(Rider)
admin.site.register(Counter)

class UserInfoExtendAdmin(admin.ModelAdmin):
    list_display = ('user', 'username', 'phone', 'country', 'verification_status')
    search_fields = ('user__username', 'username')