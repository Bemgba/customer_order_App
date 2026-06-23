from django.urls import path
<<<<<<< HEAD
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # -----------------------------------------------------------------------
    # Public — no login required
    # -----------------------------------------------------------------------
    path('',          views.menu,  name='menu'),          # public menu / home
    path('cart/',     views.cart_view, name='cart_view'),
    path('cart/add/<int:product_id>/',    views.cart_add,    name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('checkout/',     views.checkout,          name='checkout'),
    path('order/confirm/<str:reference>/',
         views.order_confirmation, name='order_confirmation'),

    # AJAX — load LGAs for a given state
    path('ajax/load-lgas/', views.load_lgas, name='load_lgas'),

    # -----------------------------------------------------------------------
    # Public order tracking (no login required)
    path('track/', views.order_track, name='order_track'),

    # Customer portal (login required)
    path('my-orders/',                         views.my_orders,       name='my_orders'),
    path('my-orders/cancel/<str:reference>/',  views.cancel_order,    name='cancel_order'),
    path('account-settings/',                  views.account_settings, name='account_settings'),

    # Auth
    # -----------------------------------------------------------------------
    path('register/', views.registerPage, name='register'),
    path('login/',    views.loginPage,    name='login'),
    path('logout/',   views.logoutUser,   name='logout'),
    path('profile/',  views.profile,      name='profile'),

    # -----------------------------------------------------------------------
    # Staff dashboard (login required)
    # -----------------------------------------------------------------------
    path('dashboard/',  views.home,            name='home'),
    path('products/',                  views.products,       name='products'),
    path('products/add/',              views.createProduct,  name='create_product'),
    path('products/<int:pk>/edit/',    views.updateProduct,  name='update_product'),
    path('products/<int:pk>/delete/',  views.deleteProduct,  name='delete_product'),

    # Product categories
    path('categories/',                    views.category_list,    name='category_list'),
    path('categories/add/',                views.createCategory,   name='create_category'),
    path('categories/<int:pk>/edit/',      views.updateCategory,   name='update_category'),
    path('categories/<int:pk>/delete/',    views.deleteCategory,   name='delete_category'),
    path('customer/<str:pk_test>/', views.customer, name='customer'),

    # Orders
    path('orders/',                  views.view_all_orders, name='view_all_orders'),
    path('orders/<int:pk>/',         views.order_detail,    name='order_detail'),
    path('orders/<int:pk>/delete/',  views.deleteOrder,     name='delete_order'),
    
    # NEW: Separate payment and delivery management
    path('orders/<int:order_id>/payment/update/', 
         views.update_payment_status, name='update_payment_status'),
    path('orders/<int:order_id>/delivery/confirm-dispatcher/', 
         views.confirm_delivery_dispatcher, name='confirm_delivery_dispatcher'),
    path('orders/<int:order_id>/delivery/confirm-customer/', 
         views.confirm_delivery_customer, name='confirm_delivery_customer'),
    
    # Dispatcher assignment
    path('orders/<int:order_id>/assign-dispatcher/',
         views.assign_dispatcher, name='assign_dispatcher'),
    # Dispatcher dashboard
    path('dispatcher/', views.dispatcher_dashboard, name='dispatcher_dashboard'),

    # Branch management (CEO only)
    path('branches/',                     views.branch_list,   name='branch_list'),
    path('branches/create/',              views.createBranch,  name='create_branch'),
    path('branches/<str:pk>/update/',     views.updateBranch,  name='update_branch'),
    path('branches/<str:pk>/delete/',     views.deleteBranch,  name='delete_branch'),

    # Role management (CEO only)
    path('roles/',                    views.role_list,   name='role_list'),
    path('roles/create/',             views.createRole,  name='create_role'),
    path('roles/<str:pk>/update/',    views.updateRole,  name='update_role'),
    path('roles/<str:pk>/delete/',    views.deleteRole,  name='delete_role'),

    # User management (CEO only)
    path('users/',                    views.user_list,        name='user_list'),
    path('users/create/',             views.createStaffUser,  name='create_staff_user'),
    path('users/<str:pk>/edit/',      views.editUserRoles,    name='edit_user_roles'),
    path('users/<str:pk>/delete/',    views.deleteUser,       name='delete_user'),

    # Reports
    path('reports/top-products/',  views.most_ordered_products, name='most_ordered_products'),
    path('reports/delivered-pdf/', views.delivered_orders_pdf,  name='delivered_orders_pdf'),
    path('reports/payments/',      views.payment_reports,       name='payment_reports'),

    # Inventory (CEO and managers with permission)
    path('inventory/',                     views.ingredient_list,      name='ingredient_list'),
    path('inventory/add/',                 views.createIngredient,     name='create_ingredient'),
    path('inventory/<int:pk>/edit/',       views.updateIngredient,     name='update_ingredient'),
    path('inventory/<int:pk>/delete/',     views.deleteIngredient,     name='delete_ingredient'),
    path('inventory/consumption/',         views.ingredient_consumption_history, name='consumption_history'),

    # Notifications
    path('notifications/', views.notifications_view, name='notifications'),

    # Password reset
    path('reset_password/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html'), name='reset_password'),
    path('reset_done/',     auth_views.PasswordResetDoneView.as_view(),
         name='password_reset_done'),
    path('reset_confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset_complete/', auth_views.PasswordResetCompleteView.as_view(),
         name='password_reset_complete'),
]
=======
from.import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    #Register
    path('register/', views.registerPage,name="register"),
    #login
    path('login/', views.loginPage,name="login"),
   #logout
    path('logout/', views.logoutUser,name="logout"),
    #User Profile
    path('user/', views.userPage,name="user-page"),
    
    path('', views.home ,name="home"),
    path('products', views.products,name="products"),
    path('customer/<str:pk_test>', views.customer,name="customer"),
    path('profile', views.profile,name="profile"),
    path('create_order/<str:pk>', views.createOrder ,name="create_order"),
    #path('create_order', views.createOrder ,name="create_order1"),
    path('update_order/<str:pk>', views.updateOrder ,name="update_order"),
    path('delete_order/<str:pk>', views.deleteOrder ,name="delete_order"),
    path('account/', views.accountSettings, name="account"),
    
    #PASSWORD RESET
    path('reset_password/', 
         auth_views.PasswordResetView.as_view(template_name="accounts/password_reset.html"), 
         name="reset_password"),
    path('reset_done/', auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path('reset_confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path('reset_complette/', auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complette"),
    
    

   ]
 
>>>>>>> bda2651b2d659a1fa8eddca086b4a11b677495ca
