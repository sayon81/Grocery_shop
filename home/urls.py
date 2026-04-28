from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    # Home and Static Pages
    path('', views.index, name='index'),
    path('categories/', views.categories, name='categories'),
    path('items/', views.items, name='items'),
    path('contact/', views.contact, name='contact'),
    path('search/', views.item_search, name='item_search'),
    
    # Category 
    path('category/<slug:category_slug>/', views.category_items, name='category_items'),
    
    # Product 
    path('product/<slug:product_slug>/', views.product_detail, name='product_detail'),
    path('product/', views.product_detail, name='product_detail_query'),
    
    # Cart
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update-temp/', views.update_temp_cart, name='update_temp_cart'),
    path('cart/remove-temp/', views.remove_temp_item, name='remove_temp_item'),
    path('cart/checkout/', views.checkout_cart, name='checkout_cart'),
    
    
    # Order
    path('order/', views.order, name='order'),
    path('order/<int:item_id>/', views.order_item, name='order_item'),
    path('order/confirmation/<str:order_number>/', views.order_confirmation, name='order_confirmation'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/<str:order_number>/', views.order_detail, name='order_detail'),
    path('orders/<str:order_number>/cancel/', views.cancel_order, name='cancel_order'),
    path('order/success/<str:order_number>/', views.order_success, name='order_success'),
    path('reorder/<str:order_number>/', views.reorder, name='reorder'),
    path('order-status/<str:order_number>/', views.check_order_status, name='check_order_status'),

    # Payment
    path('payment/cart/', views.payment_from_cart, name='payment_from_cart'),
    path('payment/<str:order_number>/', views.process_payment, name='process_payment'),
    path('payment/successful/<str:order_number>/', views.payment_successful, name='payment_successful'),
    path('payment/failed/<str:order_number>/', views.payment_failed, name='payment_failed'),
    path('payment/', views.payment, name='payment'),
    
    # Authentication
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard and Profile
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('address/update/', views.update_address, name='update_address'),
]