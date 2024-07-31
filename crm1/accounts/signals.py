from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Customer
from django.contrib.auth.models import Group


#@receiver(post_save, sender=User)
def customer_profile(sender, instance, created, **kwargs):
    if created:
        group=Group.objects.get(name='customers')
        instance.groups.add(group)
        
        Customer.objects.create(
        user=instance,
        name=instance.username,
        ) 
        print('Profile created')
post_save.connect(customer_profile,sender=User)
    
    
# @receiver(post_save, sender=User)
# def update_profile(sender, instance, created, **kwargs):
#     if not created:
#         instance.profile.save()
#         print('Profile updated')