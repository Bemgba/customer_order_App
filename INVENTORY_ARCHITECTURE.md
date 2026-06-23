# Inventory Management - Architecture Overview

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER ROLES                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐              ┌─────────────────┐             │
│  │     CEO      │              │    MANAGER      │             │
│  │ (is_ceo=True)│              │  (has role with │             │
│  │              │              │  can_manage_    │             │
│  │ • ALL access │              │  inventory)     │             │
│  │ • ALL branches│             │                 │             │
│  └──────┬───────┘              │ • Branch-scoped │             │
│         │                       │   access        │             │
│         │                       └────────┬────────┘             │
│         │                                │                      │
│         └────────────┬───────────────────┘                      │
│                      │                                          │
│                      ▼                                          │
│         ┌────────────────────────┐                             │
│         │  Permission Check      │                             │
│         │  @requires_permission  │                             │
│         │  ('can_manage_         │                             │
│         │   inventory')          │                             │
│         └────────────┬───────────┘                             │
│                      │                                          │
└──────────────────────┼──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                      URL ROUTING                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  /inventory/                  → ingredient_list                 │
│  /inventory/add/              → createIngredient                │
│  /inventory/<id>/edit/        → updateIngredient                │
│  /inventory/<id>/delete/      → deleteIngredient                │
│                                                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                         VIEWS                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────┐       │
│  │  ingredient_list()                                   │       │
│  │  ─────────────────                                   │       │
│  │  • Query: Ingredient.objects                         │       │
│  │  • CEO: All branches                                 │       │
│  │  • Manager: Their branch only                        │       │
│  │  • Calculate low stock count                         │       │
│  │  • Render: ingredient_list.html                      │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                  │
│  ┌─────────────────────────────────────────────────────┐       │
│  │  createIngredient()                                  │       │
│  │  ──────────────────                                  │       │
│  │  • Form: IngredientForm                              │       │
│  │  • CEO: Can select any branch                        │       │
│  │  • Manager: Branch locked to theirs                  │       │
│  │  • Save → Redirect to list                           │       │
│  │  • Render: ingredient_form.html                      │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                  │
│  ┌─────────────────────────────────────────────────────┐       │
│  │  updateIngredient(pk)                                │       │
│  │  ────────────────────                                │       │
│  │  • Get: Ingredient by ID                             │       │
│  │  • Permission: Branch check for managers             │       │
│  │  • Form: IngredientForm (instance)                   │       │
│  │  • Save → Redirect to list                           │       │
│  │  • Render: ingredient_form.html                      │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                  │
│  ┌─────────────────────────────────────────────────────┐       │
│  │  deleteIngredient(pk)                                │       │
│  │  ────────────────────                                │       │
│  │  • Get: Ingredient by ID                             │       │
│  │  • Permission: Branch check for managers             │       │
│  │  • Confirm → Delete → Redirect                       │       │
│  │  • Render: delete.html                               │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                        FORMS                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  IngredientForm                                                  │
│  ──────────────                                                  │
│  Fields:                                                         │
│    • branch            [ForeignKey → Branch]                    │
│    • name              [CharField]                              │
│    • unit              [CharField]                              │
│    • quantity_available [DecimalField]                          │
│    • reorder_level     [DecimalField]                           │
│                                                                  │
│  Validation:                                                     │
│    • All fields required                                        │
│    • Quantities must be ≥ 0                                     │
│                                                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATABASE MODELS                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────┐            │
│  │  Ingredient                                     │            │
│  │  ──────────                                     │            │
│  │  • id (PK)                                      │            │
│  │  • branch (FK → Branch)                         │            │
│  │  • name                                         │            │
│  │  • unit                                         │            │
│  │  • quantity_available                           │            │
│  │  • reorder_level                                │            │
│  │  • updated_at (auto)                            │            │
│  │                                                 │            │
│  │  @property is_low:                              │            │
│  │    return quantity_available <= reorder_level   │            │
│  └────────────────────────────────────────────────┘            │
│                                                                  │
│  ┌────────────────────────────────────────────────┐            │
│  │  ProductIngredient (Recipe)                     │            │
│  │  ──────────────────────────                     │            │
│  │  • product (FK → Product)                       │            │
│  │  • ingredient (FK → Ingredient)                 │            │
│  │  • quantity_required                            │            │
│  │                                                 │            │
│  │  [Links products to ingredients they need]      │            │
│  └────────────────────────────────────────────────┘            │
│                                                                  │
│  ┌────────────────────────────────────────────────┐            │
│  │  Role                                           │            │
│  │  ────                                           │            │
│  │  • can_manage_inventory (BooleanField)          │            │
│  │    [Permission flag for inventory access]       │            │
│  └────────────────────────────────────────────────┘            │
│                                                                  │
│  ┌────────────────────────────────────────────────┐            │
│  │  UserProfile                                    │            │
│  │  ───────────                                    │            │
│  │  • is_ceo (BooleanField)                        │            │
│  │  • branch (FK → Branch)                         │            │
│  │  • roles (M2M → Role)                           │            │
│  │                                                 │            │
│  │  def has_permission(perm):                      │            │
│  │    if is_ceo: return True  ← CEO bypass         │            │
│  │    return check roles...                        │            │
│  └────────────────────────────────────────────────┘            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Template Structure

```
dashboard1_base.html
│
├── dashboard1_header.html
│
├── dashboard1_sidebar.html
│   │
│   └── INVENTORY menu added here
│       ├── All Ingredients → ingredient_list
│       └── Add Ingredient → createIngredient
│
└── Content Block
    │
    ├── ingredient_list.html
    │   │
    │   ├── Table Header
    │   │   ├── # (counter)
    │   │   ├── Branch (CEO only)
    │   │   ├── Name
    │   │   ├── Unit
    │   │   ├── Available
    │   │   ├── Reorder Level
    │   │   ├── Status (badge)
    │   │   ├── Last Updated
    │   │   └── Actions
    │   │
    │   ├── For each ingredient:
    │   │   ├── Display row
    │   │   ├── Highlight if is_low (yellow)
    │   │   ├── Status badge (green/yellow/red)
    │   │   └── Edit/Delete buttons
    │   │
    │   └── Low stock alert (if any)
    │
    └── ingredient_form.html
        │
        ├── Form fields:
        │   ├── Branch (dropdown, locked for managers)
        │   ├── Name (text input)
        │   ├── Unit (text input with placeholder)
        │   ├── Quantity Available (number input)
        │   └── Reorder Level (number input)
        │
        ├── Validation errors
        ├── Cancel button
        └── Submit button
```

## Permission Flow

```
User Login
    │
    ▼
┌─────────────────┐
│ Check Profile   │
└────────┬────────┘
         │
         ▼
    ┌────────┐
    │ is_ceo?│───Yes───► FULL ACCESS to Inventory
    └───┬────┘           (all branches)
        │
        No
        │
        ▼
    ┌──────────────────┐
    │ Has role with    │
    │ can_manage_      │───Yes───► SCOPED ACCESS
    │ inventory?       │           (own branch only)
    └───┬──────────────┘
        │
        No
        │
        ▼
    ┌──────────────────┐
    │ 403 FORBIDDEN    │
    │ No inventory     │
    │ access           │
    └──────────────────┘
```

## Data Flow Example: Adding an Ingredient

```
1. CEO clicks "Add Ingredient"
   │
   ▼
2. URL: /inventory/add/
   │
   ▼
3. View: createIngredient()
   │
   ├─→ Check permission (@requires_permission)
   │   └─→ CEO: Pass automatically
   │
   ├─→ Initialize form
   │   ├─→ CEO: All branches available
   │   └─→ Manager: Branch pre-filled and locked
   │
   └─→ Render: ingredient_form.html
       │
       ▼
4. User fills form:
   - Branch: "Main Kitchen"
   - Name: "Flour"
   - Unit: "kg"
   - Quantity: 100
   - Reorder: 20
   │
   ▼
5. Submit (POST)
   │
   ▼
6. View validates & saves:
   - form.is_valid()
   - ingredient = form.save()
   - messages.success()
   │
   ▼
7. Redirect to: /inventory/
   │
   ▼
8. ingredient_list displays new ingredient
   - Status: "In Stock" (100 > 20)
   - Badge: Green
```

## Stock Status Logic

```python
# In Ingredient model:

@property
def is_low(self):
    return self.quantity_available <= self.reorder_level

# Examples:
# quantity=100, reorder=20  → is_low=False → Green badge "In Stock"
# quantity=15,  reorder=20  → is_low=True  → Yellow badge "Low Stock"  
# quantity=0,   reorder=20  → is_low=True  → Red badge "Out of Stock"
```

## UI Components

### Badges
- 🟢 **Green** (`badge-success`): In Stock (quantity > reorder_level)
- 🟡 **Yellow** (`badge-warning`): Low Stock (quantity ≤ reorder_level, > 0)
- 🔴 **Red** (`badge-danger`): Out of Stock (quantity = 0)

### Icons
- 📦 `icon-archive`: Inventory menu
- ➕ `icon-plus-circle`: Add ingredient
- ✏️ `fa-edit`: Edit ingredient
- 🗑️ `fa-trash`: Delete ingredient
- ⚠️ `icon-warning`: Low stock alert

### Visual Indicators
- **Yellow row highlight**: Low stock item
- **Warning badge count**: Number of low stock items
- **Alert banner**: Shown when any items are low

## Security Features

1. **Permission Decorator**: All views protected with `@requires_permission`
2. **CEO Bypass**: Automatic full access for CEO users
3. **Branch Scoping**: Managers restricted to their branch
4. **Field Locking**: Branch field disabled for non-CEO users
5. **Permission Verification**: Edit/delete operations check branch ownership
6. **403 Responses**: Unauthorized access blocked with proper error

## Integration Points

### Existing Features
- ✅ Uses same permission system as products/orders
- ✅ Uses same form/template patterns as categories
- ✅ Uses same decorators (`@requires_permission`)
- ✅ Uses same helper functions (`_get_profile`, `_get_branch`)
- ✅ Integrates with existing sidebar navigation
- ✅ Uses existing delete.html template

### Future Integration
- 🔮 ProductIngredient: Recipe management UI
- 🔮 Order fulfillment: Auto-deduct stock
- 🔮 Notifications: Email on low stock
- 🔮 Reports: Usage trends, waste tracking
- 🔮 Stock transfers: Between branches
- 🔮 Audit log: Track stock changes

## File Structure

```
crm1/
├── accounts/
│   ├── models.py                    [Ingredient, ProductIngredient models]
│   ├── views.py                     [4 new inventory views]
│   ├── forms.py                     [IngredientForm, updated RoleForm]
│   ├── urls.py                      [4 new inventory routes]
│   └── templates/
│       └── accounts/
│           ├── dashboard1_sidebar.html    [Updated with INVENTORY menu]
│           ├── ingredient_list.html       [New: list view]
│           └── ingredient_form.html       [New: create/edit form]
│
└── Documentation (in project root):
    ├── INVENTORY_FEATURE_SUMMARY.md       [Complete feature overview]
    ├── SETUP_INVENTORY_FOR_CEO.md         [CEO setup guide]
    └── INVENTORY_ARCHITECTURE.md          [This file]
```

## Summary

The inventory management feature is built using the same architectural patterns as the rest of the CRM:
- Permission-based access control
- CEO automatic bypass
- Branch-scoped data
- Consistent UI/UX
- Django best practices
- Clean separation of concerns

It seamlessly integrates with existing code and provides a solid foundation for future enhancements.
