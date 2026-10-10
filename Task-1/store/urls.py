from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:pk>/', views.remove_from_cart,
         name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/success/<int:pk>/', views.order_success,
         name='order_success'),
    path('register/', views.register, name='register'),
]