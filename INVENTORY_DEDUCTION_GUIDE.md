# Inventory Auto-Deduction Guide

## How Inventory Deduction Works

### YES - Inventory IS Auto-Deducted! ✅

Your system has **automatic inventory deduction** built in. Here's exactly how it works:

---

## Trigger Point: Order Status Change

Inventory is automatically deducted when a staff member changes an order's status from **any status** to **"Preparing"**.

### The Workflow:

```
1. Customer places order → Status: "Awaiting Payment"
2. Staff confirms payment → Status: "Paid"
3. Staff starts preparation → Status: "Preparing" ⚡ INVENTORY DEDUCTED HERE
4. Staff dispatches order → Status: "Out for Delivery"
5. Staff confirms delivery → Status: "Delivered"
```

---

## What Happens During Deduction

When a staff member clicks to change status to "Preparing", the system:

### 1. **Calculates Required Ingredients**
   - For each product in the order
   - Looks up the recipe (ProductIngredient entries)
   - Multiplies ingredient quantities by order quantity
   - Example: 
     - Order: 3x Jollof Rice
     - Recipe: Jollof Rice needs 2kg rice + 0.5L oil
     - Required: 6kg rice + 1.5L oil

### 2. **Checks Stock Availability**
   - Verifies sufficient quantity exists in inventory
   - Only checks ingredients from the SAME BRANCH
   - If insufficient stock: **BLOCKS status change** and shows error

### 3. **Deducts from Inventory**
   - Reduces `quantity_available` for each ingredient
   - Updates `updated_at` timestamp
   - Saves changes to database

### 4. **Records Consumption History**
   - Creates an `IngredientConsumption` record for each ingredient
   - Tracks:
     - Which ingredient was used
     - How much was used
     - Which order consumed it
     - Who processed the order
     - When it was consumed
     - Notes (e.g., "Order ORD-2024-001: 3x Jollof Rice")

---

## Example Scenario

### Before Deduction:
```
Ingredient: Rice
Current Stock: 50kg
---
Order #ORD-001: 3x Jollof Rice (needs 6kg)
Status: Paid
```

### Staff Changes Status to "Preparing":
```
System automatically:
1. Checks: 50kg >= 6kg ✓
2. Deducts: 50kg - 6kg = 44kg
3. Updates: Rice stock now shows 44kg
4. Records: Consumption entry created
5. Shows message: "Inventory updated: Deducted: Rice: -6kg"
```

### After Deduction:
```
Ingredient: Rice
Current Stock: 44kg (automatically updated)
---
Consumption History shows:
- Order: ORD-001
- Used: 6kg Rice
- By: manager_user
- Date: 2024-06-20 10:30
- Notes: "Order ORD-001: 3x Jollof Rice"
```

---

## What If Stock Is Insufficient?

### Example:
```
Current Stock: 3kg Rice
Order needs: 6kg Rice
```

When staff tries to change status to "Preparing":
1. ❌ Status change is **BLOCKED**
2. Error message shown: 
   ```
   "Cannot prepare order: Insufficient Rice: need 6kg, have 3kg"
   ```
3. Order remains in "Paid" status
4. No inventory deduction happens
5. Staff must either:
   - Restock the ingredient first
   - Cancel/modify the order

---

## Where to View Deductions

### 1. Inventory List (`/inventory/`)
- Shows current `quantity_available` (automatically updated after deductions)
- Shows `last_restocked` date
- Shows low stock warnings

### 2. Consumption History (`/inventory/consumption/`)
- Complete audit trail of all deductions
- Filterable by:
  - Ingredient
  - Date range
  - Branch
  - Staff member
- Shows which orders consumed which ingredients

### 3. Order Detail Page (`/orders/<id>/`)
- When status changes to "Preparing", shows success message:
  ```
  "Inventory updated: Deducted: Rice: -6kg, Oil: -1.5L"
  ```

---

## Key Points

### ✅ Automatic Features:
- Deduction happens automatically on status change
- No manual calculation needed
- Stock levels update immediately
- Consumption history recorded automatically
- Branch-specific (only deducts from order's branch)

### ⚠️ Manual Steps Required:
- Staff must manually change order status to "Preparing"
- Staff must manually restock ingredients when low
- Products must have recipes defined (ProductIngredient)

### 🔒 Safety Features:
- Cannot prepare orders without sufficient stock
- Only deducts once (checks if already "Preparing")
- Transaction-safe (all-or-nothing deduction)
- Full audit trail maintained

---

## Setting Up for Auto-Deduction

To enable automatic deduction for a product:

1. **Define the Recipe:**
   - Go to product edit page
   - Scroll to "Recipe/Ingredients" section
   - Add ingredients with quantities
   - Example: "Jollof Rice uses 2kg Rice + 0.5L Oil"

2. **Ensure Inventory Exists:**
   - Add ingredients to inventory (`/inventory/add/`)
   - Set correct branch
   - Set initial stock quantity

3. **Process Orders Normally:**
   - Accept order (status: "Paid")
   - Change to "Preparing" → **Deduction happens here**
   - Complete order flow

---

## Management Commands

### Manual Deduction (if needed):
```bash
python manage.py update_inventory_on_order <order_reference>
```

This command can be used to:
- Manually trigger deduction for an order
- Re-process old orders
- Fix inventory if issues occurred

---

## Troubleshooting

### "No ingredients to deduct" message?
- **Cause:** Products in order have no recipes defined
- **Solution:** Add ProductIngredient entries for each product

### Inventory not deducting?
- **Check:** Is order status changing to "Preparing"?
- **Check:** Do products have recipes defined?
- **Check:** Are ingredients in same branch as order?

### Wrong quantities deducted?
- **Check:** ProductIngredient `quantity_required` values
- **Update:** Recipe quantities in product edit page

---

## Summary

**Your inventory system DOES auto-deduct** when staff change order status to "Preparing". The deduction is:
- ✅ Automatic
- ✅ Immediate
- ✅ Validated (blocks if insufficient)
- ✅ Tracked (consumption history)
- ✅ Branch-specific
- ✅ Safe (prevents double-deduction)

Staff only need to follow the normal order workflow, and inventory management happens automatically in the background!
