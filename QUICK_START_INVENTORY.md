# Quick Start: Using Inventory Management

## For CEO Users

### Accessing Inventory
1. Login to CRM with your CEO account
2. Look at left sidebar under "MANAGEMENT"
3. Click **"INVENTORY"** menu (archive icon 📦)
4. You'll see the ingredient list

### Adding an Ingredient
1. Click **"Add Ingredient"** button (top right)
2. Fill in the form:
   - **Branch**: Select which branch this ingredient belongs to
   - **Name**: E.g., "Flour", "Chicken Breast", "Cooking Oil"
   - **Unit**: E.g., "kg", "litres", "pieces", "bags"
   - **Quantity Available**: Current stock amount (e.g., 100)
   - **Reorder Level**: Alert threshold (e.g., 20)
3. Click **"Create Ingredient"**
4. Done! You'll see it in the list

### Understanding Stock Status

| Status | Badge Color | Meaning |
|--------|-------------|---------|
| **In Stock** | 🟢 Green | Quantity > Reorder Level |
| **Low Stock** | 🟡 Yellow | Quantity ≤ Reorder Level |
| **Out of Stock** | 🔴 Red | Quantity = 0 |

### Editing Stock Levels
1. Find the ingredient in the list
2. Click **"Edit"** button
3. Update **"Quantity Available"** field
4. Click **"Save Changes"**

### Example: Restocking Flour
```
Current: 15 kg (Low Stock - yellow warning)
After restock: 100 kg (In Stock - green)

Action:
1. Click Edit on "Flour"
2. Change "Quantity Available" from 15 to 100
3. Save
4. Status changes to green automatically
```

## For Managers (with permission)

### Prerequisites
Your CEO must:
1. Create/edit a Role
2. Check ✅ "can_manage_inventory" permission
3. Assign you that role
4. Assign you to a specific branch

### What You Can Do
- ✅ View ingredients for YOUR branch only
- ✅ Add ingredients to YOUR branch
- ✅ Edit ingredients in YOUR branch
- ✅ Delete ingredients from YOUR branch

### What You CANNOT Do
- ❌ View other branches' ingredients
- ❌ Edit other branches' ingredients
- ❌ Change which branch an ingredient belongs to

### Your Workflow
1. Login with your manager account
2. Navigate to INVENTORY menu
3. See only YOUR branch's ingredients
4. Manage stock as needed
5. Branch field is locked when adding/editing

## Common Tasks

### Task 1: Initial Inventory Setup
```
For a new branch "Downtown Kitchen":

Ingredients to add:
- Flour           (kg)      → Qty: 50,  Reorder: 10
- Sugar           (kg)      → Qty: 30,  Reorder: 5
- Cooking Oil     (litres)  → Qty: 20,  Reorder: 5
- Chicken Breast  (kg)      → Qty: 40,  Reorder: 15
- Onions          (kg)      → Qty: 25,  Reorder: 10
- Tomatoes        (kg)      → Qty: 20,  Reorder: 8
```

### Task 2: Daily Stock Check
1. Go to Inventory list
2. Look for yellow-highlighted rows (low stock)
3. Check warning badge at top: "3 low stock"
4. Review each low-stock item
5. Plan restocking or update quantities

### Task 3: After Receiving Delivery
1. Click Edit on the ingredient
2. Add received quantity to current amount
3. Example: Had 15 kg flour, received 50 kg
   - New amount: 15 + 50 = 65 kg
4. Save changes
5. Status updates automatically

### Task 4: Setting Up Alerts
```
To get warnings before running out:

Example: Flour
- Daily usage: ~5 kg
- Delivery time: 3 days
- Safety buffer: 2 days

Reorder Level = (5 kg × 5 days) = 25 kg

When stock hits 25 kg, you get 5 days to restock
before running out.
```

## Visual Guide

### Ingredient List View
```
┌─────────────────────────────────────────────────────────┐
│ 📦 Inventory Management     [3 ingredients] [⚠️ 1 low]  │
│                                    [+ Add Ingredient]    │
├─────────────────────────────────────────────────────────┤
│ ⚠️ Low Stock Alert: 1 ingredient(s) below reorder level│
├───┬────────┬────┬──────────┬────────┬────────┬─────────┤
│ # │ Name   │Unit│Available │ Reorder│ Status │ Actions │
├───┼────────┼────┼──────────┼────────┼────────┼─────────┤
│ 1 │ Flour  │ kg │   🔴 0   │   20   │🔴 Out  │ Edit Del│
│ 2 │ Sugar  │ kg │  🟡 15   │   20   │🟡 Low  │ Edit Del│
│ 3 │ Oil    │ltr │ 🟢 100   │   10   │🟢 In   │ Edit Del│
└───┴────────┴────┴──────────┴────────┴────────┴─────────┘

Yellow row = Low stock (quantity ≤ reorder level)
```

### Add/Edit Form
```
┌─────────────────────────────────────┐
│ 📦 Add Ingredient        [← Back]   │
├─────────────────────────────────────┤
│                                     │
│ Branch: [Downtown Kitchen ▼]       │
│                                     │
│ Ingredient Name:                    │
│ [Flour                      ]       │
│                                     │
│ Unit of Measurement:                │
│ [kg                         ]       │
│ e.g. kg, litres, pieces             │
│                                     │
│ Quantity Available:                 │
│ [100                        ]       │
│                                     │
│ Reorder Level:                      │
│ [20                         ]       │
│ Alert when stock falls below        │
│                                     │
│ [Cancel]  [✓ Create Ingredient]    │
└─────────────────────────────────────┘
```

## Troubleshooting

### "I don't see the INVENTORY menu"
**Solution:**
- **CEO**: Verify your `is_ceo` flag is True
- **Manager**: Ask CEO to grant you "can_manage_inventory" permission
- Clear browser cache and refresh

### "403 Forbidden" when accessing inventory
**Solution:**
- Contact CEO to grant you inventory permission
- CEO needs to add you to a role with `can_manage_inventory` checked

### "I can't select a different branch"
**Solution:**
- **This is normal for managers!** You're restricted to your assigned branch
- Only CEO can select any branch

### "Ingredient isn't showing as low stock"
**Check:**
- Is `quantity_available` ≤ `reorder_level`?
- Example: If quantity=25 and reorder=20, it's NOT low (25 > 20)
- Example: If quantity=15 and reorder=20, it IS low (15 ≤ 20)

### "Can't delete an ingredient"
**Reason:**
- You might not have permission (manager trying to delete from another branch)
- Ingredient might be linked to products (recipe)
- Check with CEO if this is the case

## Best Practices

### ✅ DO:
- Set realistic reorder levels based on:
  - Daily usage rate
  - Supplier delivery time
  - Safety buffer
- Update quantities immediately after:
  - Receiving deliveries
  - Taking stock inventory
  - Waste/spoilage
- Check inventory daily for low stock warnings
- Keep ingredient names consistent (e.g., always "Flour" not sometimes "flour" or "FLOUR")

### ❌ DON'T:
- Set reorder level to 0 (you'll never get warnings)
- Let stock reach 0 without reordering
- Use different units for the same ingredient across branches
- Delete ingredients that are used in product recipes
- Ignore yellow warnings

## Stock Management Tips

### Tip 1: Calculate Reorder Level
```
Formula: Reorder Level = (Daily Usage × Lead Time) + Safety Stock

Example:
- Daily flour usage: 10 kg
- Supplier delivers in: 2 days
- Safety buffer: 5 days
- Reorder = (10 × 2) + (10 × 5) = 70 kg

Order when you hit 70 kg, receive in 2 days when you're at 50 kg.
```

### Tip 2: Track Usage Patterns
```
Monitor over time:
- Which ingredients run low most often?
- What's your actual daily usage?
- Are reorder levels too high/low?

Adjust reorder levels seasonally if needed.
```

### Tip 3: Batch Updates
```
After weekly inventory count:
1. Print ingredient list
2. Count physical stock
3. Update all quantities at once
4. Review discrepancies
```

### Tip 4: Color-Coded System
```
Your visual guide at a glance:
- 🟢 Green badge = Relax, good stock
- 🟡 Yellow badge = Plan to reorder soon
- 🔴 Red badge = URGENT: Order now!
```

## Quick Reference

| Action | CEO Access | Manager Access |
|--------|-----------|----------------|
| View all branches' inventory | ✅ Yes | ❌ No (own branch only) |
| Add ingredient to any branch | ✅ Yes | ❌ No (own branch only) |
| Edit any ingredient | ✅ Yes | ❌ No (own branch only) |
| Delete any ingredient | ✅ Yes | ❌ No (own branch only) |
| Change ingredient's branch | ✅ Yes | ❌ No (locked field) |
| Grant inventory permission | ✅ Yes | ❌ No |

## Need Help?

1. Check documentation:
   - `INVENTORY_FEATURE_SUMMARY.md` - Full feature details
   - `SETUP_INVENTORY_FOR_CEO.md` - Permission setup
   - `INVENTORY_ARCHITECTURE.md` - Technical details

2. Contact your CEO to:
   - Grant you inventory access
   - Adjust your permissions
   - Assign you to a branch

3. Check Django admin:
   - Verify your UserProfile settings
   - Check your assigned roles
   - View permission flags

## Summary

**Getting Started in 3 Steps:**
1. Login as CEO (or get permission from CEO)
2. Click INVENTORY in sidebar
3. Start adding ingredients with quantities and reorder levels

**Managing Stock in 3 Steps:**
1. Check list for yellow warnings
2. Click Edit on low-stock items
3. Update quantity after restocking

That's it! The system automatically handles the rest (status badges, alerts, highlights).
