from django.urls import path
from . import views

urlpatterns = [
    path('', views.store, name='store'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),
    path('product/<slug:slug>/', views.product_detail_by_slug, name='product_detail_by_slug'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/data/', views.cart_data, name='cart_data'),
]