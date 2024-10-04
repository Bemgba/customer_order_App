from os import name
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Customer(models.Model):
    user= models.OneToOneField(User,blank=True,null=True,on_delete=models.CASCADE)
    name=models.CharField(max_length=200,null=True)
    phone=models.CharField(max_length=200,null=True)
    email=models.CharField(max_length=200,null=True)
    profile_pic=models.ImageField(default="user_avatar.png",null=True,blank=True)
    date_create=models.DateTimeField(auto_now_add=True,null=True)
    def __str__(self):
        return self.name 
    
class Tag(models.Model):
    name=models.CharField(max_length=200,null=True)
    def __str__(self):
        return self.name 
    
  #product  
class Product(models.Model):
    CATEGORY=(
        ('Indoor','Indoor'),
        ('Out Door','Out Door'),
        ('chops','chops'),
        ('Food','Food'),
        ('Snacks','Snacks'),
        ('appetizer','appetizer'),
        
    )
    name=models.CharField(max_length=200,null=True)
    price=models.CharField(max_length=200,null=True)
    category=models.CharField(max_length=200,null=True,choices=CATEGORY)
    description=models.CharField(max_length=200,null=True,blank=True)
    tags=models.ManyToManyField(Tag)
    date_create=models.DateTimeField(auto_now_add=True,null=True)
    def __str__(self):
        return self.name 
#order
class Order(models.Model):
    STATUS=(
        ('Pending','Pending'),
        ('Out of Delivery','Out of Delivery'),
        ('Delivered','Delivered'),
            )
    customer=models.ForeignKey(Customer,null=True,on_delete=models.SET_NULL)#if customer is deleted, her order remain in the order table with null value for customer
    product=models.ForeignKey(Product,null=True,on_delete=models.SET_NULL)
    date_create=models.DateTimeField(auto_now_add=True,null=True)
    status=models.CharField(max_length=200,null=True,choices=STATUS)
    nates=models.CharField(max_length=1000,null=True)
    
    def __str__(self):
        return self.product.name
    
    
# class Profile(models.Model):
#         user= models.OneToOneField(User,blank=True,null=True,on_delete=models.CASCADE)
#         first_name=models.CharField(max_length=200,blank=True,null=True)
#         last_name=models.CharField(max_length=200,blank=True,null=True)
#         phone=models.CharField(max_length=200,null=True,blank=True)
# def __str__(self):
#         return str(self.user)
    
    

    #post_save.connect(update_profile, sender=User)
    
    
    
    
    #Return the total count for number of time a "Meat Pie" was ordered
    #MeatPieOrders=firstCustomer.order_set.filter(product__name"Meat pie").count()
    #Return total count for each product ordered
    #allOrders={}
    '''
    for orders in firstCustomer.order_set.all():
    if order.product.name in allOrders:
    allOrders[order.product.name] +=1
    else:
    allOrders[order.product.name]=1
    #RETURN : ALLoRDERS{'bALL':2,'BBq grill':1}
    '''
    
    
    
