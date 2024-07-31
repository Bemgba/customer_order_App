from django.urls import path
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
 