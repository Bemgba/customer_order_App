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
    rider_view,
    user_view
    )

urlpatterns = [
    #Register
    # path('register/', views.registerPage,name="register"),
    
    #login
    path('login/', auth_view.login_view,name="login"),
    
    #logout
    path ('logout/', auth_view.logout_view, name='logout_view'),

    # path('logout/', views.logoutUser,name="logout"),
    
    #dashboard
    # path('dashboard/', dashborad_view.dashboard_view,name="dashboard"),
    path ('dashboard/', dashborad_view.index_admin, name = 'index_admin'),

    #orders
    path ('Interface/Fetch/order/', order_view.order_list, name = 'order_list' ),
    path ('Interface/Create/single-order/', order_view.create_single_order, name='create_single_order'),
    path ('Interface/Create/bulk-order/', order_view.create_bulk_order, name='create_bulk_order'),

    #Notifications
    path('Interface/Delete/Notification/<int:notification_id>/', notification_view.clear_notification, name='clear_notification'),
    path('Interface/Delete/All-Notifications/', notification_view.clear_all_notifications, name='clear_all_notifications'),
    
    #User Profile
    path ('Interface/Fetch/profile-settings/', profile_view.profileSet_view, name = 'profileSet_view'),

    #Customer
    path ('Interface/Create/new-customer/', customer_view.customer_create, name = 'new_customer' ),
    path ('Interface/Fetch/customer/', customer_view.customer_view, name='customer_view'),

    #Payment 
    path ('Interface/Create/new-payment/', payment_view.new_payment, name = 'new_payment' ),
    path ('Interface/Fetch/payment-history/', payment_view.payment_history, name = 'payment_history' ),

    #Rider View
    path ('Interface/Fetch/Rider/', rider_view.rider_view, name = 'rider_view'),
    
    #User management
    path ('Interface/Fetch/user/', user_view.user_list, name = 'user_list'),
    path ('Interface/Create/user/', user_view.user_create, name = 'user_create'),
    
    
#     path('user/', views.userPage,name="user-page"),
    
#     path('', views.home ,name="home"),
#     path('products', views.products,name="products"),
#     path('customer/<str:pk_test>', views.customer,name="customer"),
#     path('profile', views.profile,name="profile"),
#     path('create_order/<str:pk>', views.createOrder ,name="create_order"),
#     #path('create_order', views.createOrder ,name="create_order1"),
#     path('update_order/<str:pk>', views.updateOrder ,name="update_order"),
#     path('delete_order/<str:pk>', views.deleteOrder ,name="delete_order"),
#     path('account/', views.accountSettings, name="account"),
# #     path('account/<str:pk_test>/', views.accountSettings, name='account2'),
#     path('view_all_orders/', views.view_all_orders, name="view_all_orders"),
    
    
#     #PASSWORD RESET
#     path('reset_password/',auth_views.PasswordResetView.as_view(template_name="accounts/password_reset.html"),name="reset_password"),
#     path('reset_done/', auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
#     path('reset_confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
#     # path('reset_complette/', auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complette"),
#     path('reset_complete/', auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),

#     #pdf generate
#     path('delivered_orders_pdf/', views.delivered_orders_pdf, name='delivered_orders_pdf'),
#     path('customer/<str:pk_test>/delivered_orders_pdf/', views.customer_delivered_orders_pdf, name='customer_delivered_orders_pdf'),
#     # most-ordered-products
#     path('most-ordered-products/', views.most_ordered_products, name='most_ordered_products'),
      ]
 