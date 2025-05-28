from django.urls import path
from . import views

urlpatterns = [
    path('', views.store, name='store'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),
    path('category/<int:id>/', views.category, name='category'),
    path('search/', views.search, name='search'),
    path('filter/', views.filter_products, name='filter_products'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
]