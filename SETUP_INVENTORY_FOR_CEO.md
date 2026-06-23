# How to Enable Inventory Access for CEO

## CEO Access is AUTOMATIC! ✅

**Good news:** If a user has `is_ceo=True` in their UserProfile, they automatically have access to ALL features including inventory management. No additional setup needed!

## How CEO Permission Works

The system checks permissions in this order:

1. **Is the user a superuser?** → YES = Full access to everything
2. **Is the user marked as CEO (`is_ceo=True`)?** → YES = Full access to everything
3. **Does the user have a role with the specific permission?** → Check role permissions

See the code in `crm1/accounts/models.py` - `UserProfile.has_permission()`:

```python
def has_permission(self, perm):
    if self.is_ceo or self.user.is_superuser:
        return True  # ← CEO bypasses all permission checks!
    # ... then check roles ...
```

## Verify CEO Has Access

### Method 1: Check in Django Admin
1. Go to Django admin panel
2. Navigate to User Profiles
3. Find the CEO user
4. Verify `is_ceo` checkbox is **checked** ✅

### Method 2: Check in Database (if you have direct access)
```sql
SELECT 
    u.username, 
    up.is_ceo, 
    b.name as branch
FROM 
    accounts_userprofile up
    JOIN auth_user u ON up.user_id = u.id
    LEFT JOIN accounts_branch b ON up.branch_id = b.id
WHERE 
    up.is_ceo = 1;
```

### Method 3: Django Shell
```bash
python manage.py shell
```

Then run:
```python
from django.contrib.auth.models import User
from accounts.models import UserProfile

# Check all CEOs
ceos = UserProfile.objects.filter(is_ceo=True)
for profile in ceos:
    print(f"CEO: {profile.user.username}")
    print(f"  Has inventory permission: {profile.has_permission('can_manage_inventory')}")
```

## Create a CEO User (If Needed)

If you need to create a new CEO user:

### Option 1: Django Admin
1. Go to Admin → Users → Add User
2. Create username and password
3. Go to User Profiles → Add User Profile
4. Select the user you just created
5. **Check the "is_ceo" checkbox** ✅
6. Optionally select a branch (CEOs can see all branches anyway)
7. Save

### Option 2: Django Shell
```python
from django.contrib.auth.models import User
from accounts.models import UserProfile

# Create user
ceo_user = User.objects.create_user(
    username='ceo_username',
    email='ceo@company.com',
    password='secure_password',
    first_name='John',
    last_name='Doe'
)

# Create profile with CEO flag
profile = UserProfile.objects.create(
    user=ceo_user,
    is_ceo=True  # ← This is the magic flag!
)

print(f"CEO user created: {ceo_user.username}")
print(f"Has inventory access: {profile.has_permission('can_manage_inventory')}")
```

### Option 3: Management Command (if exists in your project)
```bash
python manage.py create_staff_user --username ceo1 --is-ceo
```

## Grant Inventory Permission to Regular Managers

If you want a **non-CEO manager** to have inventory access:

1. Go to Django Admin → Roles → Add/Edit Role
2. Find or create a role (e.g., "Inventory Manager" or "Branch Manager")
3. **Check "can_manage_inventory"** ✅
4. Save the role
5. Go to User Profiles
6. Find the manager's profile
7. Add the role you just created to their "Roles" field
8. Assign them to a specific branch
9. Save

Now that manager will see and manage inventory for their assigned branch only.

## Current Status

✅ **Inventory feature is fully implemented**
✅ **CEO automatically has access** (via `is_ceo=True`)
✅ **Permission system in place** (`can_manage_inventory`)
✅ **UI added to dashboard** (Inventory menu in sidebar)
✅ **Role form includes inventory permission checkbox**

## Quick Test

1. Login as CEO user
2. Look at the left sidebar under "MANAGEMENT" section
3. You should see "INVENTORY" menu with archive icon 📦
4. Click it to see ingredient list
5. Click "Add Ingredient" to create one

If you don't see the INVENTORY menu:
- Verify you're logged in as a user with `is_ceo=True`
- Check browser console for JavaScript errors
- Clear cache and refresh page
- Verify the sidebar template was properly updated

## Troubleshooting

### "I don't see the INVENTORY menu"
**Check:**
- Is the user's `is_ceo` flag set to `True`?
- Is the user logged in?
- Did you restart the Django server after making code changes?
- Clear browser cache

### "403 Forbidden when accessing inventory"
**Check:**
- Verify `is_ceo=True` in UserProfile
- Check that views have `@requires_permission('can_manage_inventory')`
- Verify CEO bypass logic in `has_permission()` method

### "Branch field is disabled/locked"
**This is correct behavior for non-CEO users!**
- CEO: Can select any branch
- Managers: Locked to their assigned branch

### "Low stock warnings not showing"
**Check:**
- `quantity_available` < `reorder_level` for the ingredient
- Refresh the page after updating quantities

## Summary

**For CEO users: Nothing extra needed!** The `is_ceo=True` flag grants automatic access to inventory management (and all other features). Just ensure the flag is set correctly in the UserProfile, and the CEO will see the INVENTORY menu in the dashboard immediately after login.
