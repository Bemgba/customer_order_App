<<<<<<< HEAD
import logging

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger('accounts')


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Auto-create a UserProfile whenever a new User is saved.

    - Users created by the CEO via the app's 'Create Staff' form will have
      their roles and branch assigned explicitly in the view — the signal
      just ensures the profile row always exists.
    - Users who self-register via the public /register/ page get a bare
      profile (no roles, no branch, is_ceo=False), which routes them to
      the customer portal via the admin_only decorator.
    - The Customer record for self-registered users is created in the view
      after the signal runs.
    """
    if created:
        # Import here to avoid circular import at module level
        from .models import UserProfile
        UserProfile.objects.get_or_create(user=instance)
        logger.info('UserProfile created for %s', instance.username)
=======
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
>>>>>>> bda2651b2d659a1fa8eddca086b4a11b677495ca
