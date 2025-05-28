from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('address-book/', views.address_book, name='address_book'),
    path('address-book/add/', views.add_address, name='add_address'),
    path('address-book/edit/<int:address_id>/', views.edit_address, name='edit_address'),
    path('address-book/delete/<int:address_id>/', views.delete_address, name='delete_address'),
]
