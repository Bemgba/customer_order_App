from django.urls import path
from .import views
from django.contrib.auth import views as auth_views
from .view_port import (
    auth_view, 
    dashborad_view, 
    order_view, 
    notification_view, 
    profile_view, 
    customer_view, 
    payment_view,
    invoice_view,
    rider_view,
    user_view
    )

urlpatterns = [
    #Register
    # path('register/', views.registerPage,name="register"),
    # path ('sign-up/', auth_view.SignUpView.as_view(), name='sign-up'),

    #login
    # path('login/', auth_view.login_view,name="login"),
    path('login/', auth_view.LoginView.as_view(), name="login"),
    
    #logout
    path ('logout/', auth_view.LogoutView.as_view(), name='logout'),
    
    #dashboard
    # path('dashboard/', dashborad_view.dashboard_view,name="dashboard"),
    path ('dashboard/', dashborad_view.DashboardAPIView.as_view(), name = 'index_admin'),

    #orders
    path ('Interface/Fetch/Order/', order_view.order_list, name = 'order_list' ),
    path ('Interface/Create/Single-Order/', order_view.create_single_order, name='create_single_order'),
    path ('Interface/Create/Bulk-Order/', order_view.create_bulk_order, name='create_bulk_order'),

    #Notifications
    path('Interface/Delete/Notification/<int:notification_id>/', notification_view.clear_notification, name='clear_notification'),
    path('Interface/Delete/All-Notifications/', notification_view.clear_all_notifications, name='clear_all_notifications'),
    
    #User Profile
    path ('Interface/Fetch/Profile-Settings/', profile_view.profileSet_view, name = 'profileSet_view'),

    #Customer
    path ('Interface/Create/New-Customer/', customer_view.customer_create, name = 'new_customer' ),
    path ('Interface/Action/Customer/', customer_view.customer_view, name='customer_view'),
    path ('Interface/Fetch/Customer/', customer_view.viewCustomer_page, name='viewCustomer_page'),

    #Payment 
    path ('Interface/Create/New-Payment/', payment_view.new_payment, name = 'new_payment' ),
    path ('Interface/Fetch/Payment-History/', payment_view.payment_history, name = 'payment_history' ),

    #Invoice 
    path ('Interface/Create/Invoice/<int:order_id>', invoice_view.invoice_generate, name='invoice_generate'),
    path ('Interface/Fetch/Invoice/Download/<int:order_id>', invoice_view.render_template_as_jpeg, name='download'),

    #Rider View
    path ('Interface/Fetch/Rider/', rider_view.rider_view, name = 'rider_view'),
    
    #User management
    path ('Interface/Fetch/User/', user_view.user_list, name = 'user_list'),
    path ('Interface/Create/User/', user_view.user_create, name = 'user_create'),
    
    ]
 