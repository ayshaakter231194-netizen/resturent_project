from django.urls import path
from . import views

app_name = 'menu'
urlpatterns = [
    path('', views.menu_view, name='menu'),
    path('add/<int:food_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/update/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:food_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout_view, name='checkout'),
]
