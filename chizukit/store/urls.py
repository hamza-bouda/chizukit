from django.urls import path ,include
from . import views
from .views import product_detail
from django.contrib.auth import views as auth_views

from django.urls import path
from .views import index, product_detail, all_jerseys, icon_jerseys, new_jerseys, search_jerseys, add_to_cart, cart, process_payment,remove_from_cart, place_order, payment_page, order_success,account,user_logout, add_review, create_payment, execute_payment, payment_cancelled

urlpatterns = [
    path('', index, name='index'),
    path('product/<int:product_id>/', product_detail, name='product_detail'),
    path('all_jerseys/', all_jerseys, name='all_jerseys'),
    path('icon_jerseys/', icon_jerseys, name='icon_jerseys'),
    path('new_jerseys/', new_jerseys, name='new_jerseys'),
    path('search/', search_jerseys, name='search_jerseys'),
    path('add_to_cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/', cart, name='cart'),
    path('remove_from_cart/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
    path('place_order/', place_order, name='place_order'),
    path('payment/<int:order_id>/', payment_page, name='payment_page'),
    path('order_success/', order_success, name='order_success'),
    path('account/', account, name='account'),
    path('logout/', user_logout, name='user_logout'),
    path('product/<int:product_id>/add_review/', add_review, name='add_review'),
    path('create_payment/<int:order_id>/', create_payment, name='create_payment'),
    path('execute_payment/', execute_payment, name='execute_payment'),
    path('payment_cancelled/', payment_cancelled, name='payment_cancelled'),
    path('process_payment/<int:order_id>/',process_payment,name='process_payment'),
]
