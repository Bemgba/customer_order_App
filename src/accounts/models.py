from os import name
from django.db import models
from django.contrib.auth.models import User
import random
from django.utils.translation import gettext_lazy as _
import secrets
import datetime

# Create your models here.

class UserInfoExtend(models.Model):
    user= models.OneToOneField(User,blank=True,null=True,on_delete=models.CASCADE)
    phone = models.BigIntegerField( null=True, blank=True)
    whatsappNumber = models.BigIntegerField( null=True, blank=True)
    user_type = models.CharField(max_length=20,default="sub_admin") #sub_admin,  
    username = models.CharField(_('Username'), max_length=100, default='', unique=True)
    photo = models.ImageField(upload_to='users', default="/static/images/profile1.png", null=True, blank=True)
    country = models.CharField(max_length=200, null=True, default='Nigeria')
    verification_status = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    @property
    def user_into(self):
        data = {
            "first_name" : self.user.first_name,
            "last_name" : self.user.last_name,
            "date_joined": self.user.date_joined
        }
        return data

    @property
    def user_email(self):
        data = {
            "email" : self.user.email,
        }
        return data

    def save(self,*args,**kwargs):
        self.otp =  random.randint(100000,999999)
        super().save(*args,**kwargs)

    def __str__(self):
        return f"info for: {self.user.date_joined} {self.user.first_name} {self.user.last_name} || email : {self.user.email} || user_type: {self.user_type}"


class Rider(models.Model):
    name= models.CharField(max_length=200, null= True, blank = True)
    phone = models.CharField(max_length=200)
    # email = models.EmailField()
    # verification_status = models.BooleanField(default=False)
    address = models.CharField(null=True, blank=True, max_length=50)
    apart = models.CharField(_("Apartment"), max_length=128, null= True, blank = True)
    city = models.CharField(_("City"), max_length=128, null= True, blank = True)
    town = models.CharField(_("Town"), max_length=128) 
    state = models.CharField(_("State"), max_length=64, default="Lagos")
    country = models.CharField(_("Country"), max_length=64, default="Nigeria")
    bike_number = models.CharField(max_length=10, null=True, blank=True) #bike plate number
    bike_insurance =  models.CharField(max_length=100, null=True, blank=True)
    bike_traking = models.CharField(max_length=30, null=True, blank=True)
    user_type = models.CharField(max_length=20, default="rider")
    Guarantor_name = models.CharField(null=True, blank=True, max_length=30)
    Guarantor_mobile_number =models.CharField(null=True, blank=True, max_length=30)
    Guarantor_address = models.CharField(max_length=50)
    Guarantor_apart = models.CharField(_("Apartment"), max_length=128, null= True, blank = True)
    Guarantor_city = models.CharField(_("City"), max_length=128, null= True, blank = True)
    Guarantor_town = models.CharField(_("Town"), max_length=128, null= True, blank = True) 
    Guarantor_state = models.CharField(_("State"), max_length=64, default="Lagos")
    valid_id = models.BinaryField(null=True, blank=True, max_length=20)
    user_image = models.ImageField(default = 'default.jpg', null = False, blank = False)#models.BinaryField(null=True, blank=True)
    # dob = models.DateField(null=True, blank=True)
    highest_level_of_education = models.CharField(null=True, blank=True, max_length=20)
    marital_status = models.CharField(null=True, blank=True, max_length=20)
    registration_date= models.DateField(auto_now=True, null=False)
    assignedTasks = models.IntegerField(default=0)
    completedTasks = models.IntegerField(default=0)

    def __str__(self):
        return f"info for: {self.name}  || user_type: {self.user_type}"

class Location(models.Model):
    
    # location_apart = models.CharField(_("Apartment"), max_length=128, null= True, blank = True)
    location_zone = models.CharField(_("Zone"), max_length=128, null= True, blank = True)
    location_city = models.CharField(_("City"), max_length=128, null= True, blank = True)
    location_town = models.CharField(_("Town"), max_length=128) 
    location_state = models.CharField(_("State"), max_length=64, default="Lagos")
    location_country = models.CharField(_("Country"), max_length=64, default="Nigeria")
    def __str__(self):
        return self.location_city


class Customer(models.Model):
    dt_reg = models.DateTimeField(_(""), auto_now=True)
    company_name = models.CharField(max_length=200, null=True, blank=True)
    customer_address = models.CharField(_("Address"), max_length=420, default="none")
    customer_apart = models.CharField(_("Apartment"), max_length=128, null=True, blank=True)
    customer_city = models.CharField(_("City"), max_length=128, default="none")  # Lagos Mainland, Lagos Island
    customer_town = models.CharField(_("Town"), max_length=128, default="none")
    customer_state = models.CharField(_("State"), max_length=64, default="Lagos")
    customer_country = models.CharField(_("Country"), max_length=64, default="Nigeria")
    customer_no = models.CharField(max_length=200, db_index=True, default='none')  #TODO: Add db_index=True for indexing
    customer_name = models.CharField(max_length=200, default='none')
    customer_email = models.CharField(max_length=100, default='none')

    def __str__(self):
        return f"name: {self.customer_name} email: {self.customer_email} no: {self.customer_no}"

class Counter(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    orderC= models.IntegerField(default=0)
    def __str__(self):
        return self.customer.customer_name  

class Receipient(models.Model):

    receiver_name = models.CharField(max_length=100, null = False, blank = False)
    receiver_email = models.EmailField(max_length=100, null = False, blank = False)
    receiver_phone = models.BigIntegerField(null = False, blank = False)
    receiver_address = models.CharField(max_length=100, null = False, blank = False)
    receiver_apart = models.CharField(_("Apartment"), max_length=128, null= True, blank = True)
    receiver_city = models.CharField(_("City"), max_length=128, null= True, blank = True)
    receiver_town = models.CharField(_("Town"), max_length=128) 
    receiver_state = models.CharField(_("State"), max_length=64, default="Lagos")
    receiver_country = models.CharField(_("Country"), max_length=64, default="Nigeria")
    # receiver_location= models.ForeignKey(location, on_delete=models.CASCADE)

    sender = models.ForeignKey(Customer, on_delete=models.CASCADE, null = True)

    dt_reg = models.DateTimeField(_(""), auto_now=True)
    
    #def save(self, *args,**kwargs):
    #    if user_info_extend(user = self.sender.user).user_type == "customer":
    #         super().save(*args,**kwargs)
    #    else:
    #        return"erororprororo"
    def __str__(self):
        return self.receiver_name

class Order(models.Model):
    delivery_type = models.CharField(max_length =30, default = 'Same-Day Delivery', null = True, blank = True ) #Same-Day Delivery
    customer =  models.ForeignKey(Customer, on_delete=models.CASCADE)
    receipient = models.ForeignKey(Receipient, on_delete=models.CASCADE, null= True)
    branch =  models.CharField(max_length = 200, default='Mafoluku')
    status = models.CharField(max_length = 200, default='Pending') #Pending, Fulfilled(Delivery Fulfilled), Cancelled(Order Cancelled), Assigned(Pick-up Assigned, Delivery Assigned), Processing(Order Processing) 
    reference_number = models.CharField(max_length=255, unique=True, default='none')
    pricing = models.DecimalField(max_digits=10, decimal_places=2, null = True, blank = True )
    pck_description = models.CharField(max_length=255, null = True, blank = True )
    pck_weight = models.IntegerField(null = True, blank = True)
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now=True)
    deliver_time = models.DateTimeField(auto_now=True)
    rider = models.ForeignKey(Rider, on_delete=models.CASCADE, null= True, blank=True)
    # why_delete = models.TextField(max_length=255, default="customer asked to cancel")
    reason = models.TextField(null= True, blank=True)
    # def save(self, *args, **kwargs):
    #     if self.pickup is None:
    #         self.pickup = self.customer.customer_address + self.customer.city + self.cust.state
    #     super(order, self).save(*args, **kwargs)
    def __str__(self):
        return self.reference_number

class Waybill(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    receipient = models.ForeignKey(Receipient, on_delete=models.CASCADE)
    status = models.BooleanField(max_length=200, default= False)#still-buying = false, completed = true
    def __str__(self):
            return str(self.receipient)

class Payment(models.Model):
    id = models.CharField(max_length=200, primary_key=True, editable=False)#This will be used as the reference
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    # itemInfo = models.TextField(null = True, blank = True)
    bank = models.CharField(default=None, max_length=20)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.BooleanField(default=False)#if false payment hasnt been approved or completed by api
    order_date = models.DateTimeField(auto_now_add=True)
    # delivery_status = models.TextField(default='Pending')
    # order = models.ForeignKey(order, on_delete=models.CASCADE)
    class Meta():
        ordering = ('-order_date',)
    
    def __str__(self)-> str: #adding a unique constraint
        return f"user: {self.customer} price: {self.payment_amount} "
    
    def save(self, *args, **kwargs) -> None: #when creating reference, ensure that the refernce is unique
        while not self.id: #if the current object does not have a refernce, we create a reference
            ref = secrets.token_urlsafe(50)
            object_with_similar_ref = Payment.objects.filter(id=ref)
            if not object_with_similar_ref == ref:
                self.id = ref
        waybillitem = Waybill.objects.filter(customer = self.customer)
        self.items = str(waybillitem)
        vals = []
        # for price in waybillitem:
        #     vals.append(int(price.product.price))
        # self.payment_amount = sum(vals)* 100
        # waybillitem.delete()

        super().save(*args, **kwargs)

class Notification(models.Model):
    # sender = models.ForeignKey(customer, on_delete=models.CASCADE, related_name='sender')
    # recipient = models.ForeignKey(receipient, on_delete=models.CASCADE, related_name='recipient')
    # order= models.ForeignKey(order, on_delete=models.CASCADE, related_name='order')
    # payment=models.ForeignKey(payment, on_delete=models.CASCADE, related_name = 'payment')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now=True)
    is_read = models.BooleanField(default=False)
    def __str__(self):
        return self.message















# class Customer(models.Model):
#     # user= models.OneToOneField(User,blank=True,null=True,on_delete=models.CASCADE)
#     name=models.CharField(max_length=200,null=True)
#     phone=models.CharField(max_length=200,null=True)
#     email=models.CharField(max_length=200,null=True)
#     profile_pic=models.ImageField(default="user_avatar.png",null=True,blank=True)
#     date_create=models.DateTimeField(auto_now_add=True,null=True)
#     def __str__(self):
#         return self.name 
    
class Tag(models.Model):
    name=models.CharField(max_length=200,null=True)
    def __str__(self):
        return self.name 
    
#   #product  
# class Product(models.Model):
#     CATEGORY=(
#         ('Indoor','Indoor'),
#         ('Out Door','Out Door'),
#         ('chops','chops'),
#         ('Food','Food'),
#         ('Snacks','Snacks'),
#         ('appetizer','appetizer'),
        
#     )
#     name=models.CharField(max_length=200,null=True)
#     price=models.CharField(max_length=200,null=True)
#     category=models.CharField(max_length=200,null=True,choices=CATEGORY)
#     description=models.CharField(max_length=200,null=True,blank=True)
#     tags=models.ManyToManyField(Tag)
#     date_create=models.DateTimeField(auto_now_add=True,null=True)
#     def __str__(self):
#         return self.name 
# #order
# class Order(models.Model):
#     STATUS=(
#         ('Pending','Pending'),
#         ('Out of Delivery','Out of Delivery'),
#         ('Delivered','Delivered'),
#             )
#     customer=models.ForeignKey(Customer,null=True,on_delete=models.SET_NULL)#if customer is deleted, her order remain in the order table with null value for customer
#     product=models.ForeignKey(Product,null=True,on_delete=models.SET_NULL)
#     date_create=models.DateTimeField(auto_now_add=True,null=True)
#     status=models.CharField(max_length=200,null=True,choices=STATUS)
#     nates=models.CharField(max_length=1000,null=True)
    
#     def __str__(self):
#         return self.product.name
    
    
# # class Profile(models.Model):
# #         user= models.OneToOneField(User,blank=True,null=True,on_delete=models.CASCADE)
# #         first_name=models.CharField(max_length=200,blank=True,null=True)
# #         last_name=models.CharField(max_length=200,blank=True,null=True)
# #         phone=models.CharField(max_length=200,null=True,blank=True)
# # def __str__(self):
# #         return str(self.user)
    
    

#     #post_save.connect(update_profile, sender=User)
    
    
    
    
#     #Return the total count for number of time a "Meat Pie" was ordered
#     #MeatPieOrders=firstCustomer.order_set.filter(product__name"Meat pie").count()
#     #Return total count for each product ordered
#     #allOrders={}
#     '''
#     for orders in firstCustomer.order_set.all():
#     if order.product.name in allOrders:
#     allOrders[order.product.name] +=1
#     else:
#     allOrders[order.product.name]=1
#     #RETURN : ALLoRDERS{'bALL':2,'BBq grill':1}
#     '''
    
    
    
