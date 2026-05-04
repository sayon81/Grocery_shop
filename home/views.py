from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Product, Category, Order, OrderItem, UserProfile
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail, EmailMessage,EmailMultiAlternatives
from django.conf import settings
from .token import account_activation_token
from .forms import (
    GroceryOrderForm, CheckoutForm, ContactForm, 
    UserProfileForm, AddressForm, LoginForm, SignupForm
)
import json
import uuid
from datetime import datetime


def index(request):
    """Home page view"""
    categories = Category.objects.filter(is_active=True)[:8]
    popular_items = Product.objects.filter(is_available=True, is_popular=True)[:8]
    
    carousel_slides = [
        {
            'image': 'images/slide1.jpg',
            'title': 'Fresh Groceries',
            'subtitle': 'Farm-fresh vegetables and fruits'
        },
        {
            'image': 'images/slide2.jpg',
            'title': 'Organic Products',
            'subtitle': '100% Certified organic'
        },
        {
            'image': 'images/slide3.jpg',
            'title': 'Daily Essentials',
            'subtitle': 'Everything for your kitchen'
        },
    ]
    

    cart = request.session.get('cart', {})
    cart_count = len(cart)
    
    context = {
        'categories': categories,
        'popular_items': popular_items,
        'carousel_slides': carousel_slides, 
        'cart_count': cart_count,
    }
    return render(request, 'index.html', context)


def categories(request):
    """Display all categories"""
    categories = Category.objects.filter(is_active=True)
    
    # Get cart count for navbar
    cart = request.session.get('cart', {})
    cart_count = len(cart)
    
    return render(request, 'categories.html', {
        'categories': categories,
        'cart_count': cart_count
    })

def category_items(request, category_slug):
    """Display items in a specific category"""
    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    items = Product.objects.filter(category=category, is_available=True)
    
    # Get cart count for navbar
    cart = request.session.get('cart', {})
    cart_count = len(cart)
    
    context = {
        'category': category,
        'items': items,
        'cart_count': cart_count,
    }
    return render(request, 'category_items.html', context)


def items(request):
    """Display all items with filtering and pagination"""
    products = Product.objects.filter(is_available=True).select_related('category')
    
    # Filter by category
    category_slug = request.GET.get('category')
    if category_slug and category_slug != 'all':
        products = products.filter(category__slug=category_slug)
    
    # Search
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )
    
    # Sorting
    sort_by = request.GET.get('sort', 'default')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'name_asc':
        products = products.order_by('name')
    elif sort_by == 'name_desc':
        products = products.order_by('-name')
    else:
        products = products.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.filter(is_active=True)
    
    # Get cart count for navbar
    cart = request.session.get('cart', {})
    cart_count = len(cart)
    
    context = {
        'items': page_obj,
        'categories': categories,
        'selected_category': category_slug,
        'sort_by': sort_by,
        'search_query': query,
        'cart_count': cart_count,
    }
    return render(request, 'items.html', context)

def item_search(request):
    """Search items"""
    query = request.GET.get('q', '').strip()
    results = Product.objects.none()
    
    if query:
        results = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        ).filter(is_available=True).distinct()
    
    # Get cart count for navbar
    cart = request.session.get('cart', {})
    cart_count = len(cart)
    
    context = {
        'search_query': query,
        'results': results,
        'results_count': results.count(),
        'cart_count': cart_count,
    }
    return render(request, 'item_search.html', context)


def product_detail(request, product_slug=None):
    """Display product details"""
    cart = request.session.get('cart', {})
    cart_count = len(cart)
    
    if product_slug:
        
        product = get_object_or_404(Product, slug=product_slug, is_available=True)
    else:
        
        class TempProduct:
            def __init__(self, name, category_name, price, description, image):
                self.id = None
                self.name = name
                self.category = type('Category', (), {'name': category_name})()
                self.price = float(price.replace('$', '').replace('₹', '').replace('৳', ''))
                self.description = description
                self.image = image
                self.is_organic = False
                self.is_fresh = True
                self.stock = 20
                self.unit = 'kg'
                
            def get_unit_display(self):
                return self.unit
        
        product = TempProduct(
            name=request.GET.get('name', ''),
            category_name=request.GET.get('category', ''),
            price=request.GET.get('price', '0'),
            description=request.GET.get('description', ''),
            image=request.GET.get('image', '')
        )
    
    context = {
        'product': product,
        'cart_count': cart_count
    }
    return render(request, 'product_detail.html', context)


def view_cart(request):
    """Display cart contents"""
    cart = request.session.get('cart', {})
    cart_items = []
    subtotal = 0
    
    for item_key, item_data in cart.items():
        if item_data.get('is_temp') or not item_key.isdigit():
            price = float(item_data.get('price', 0))
            quantity = item_data.get('quantity', 1)
            item_subtotal = price * quantity

            temp_product = type('Product', (), {
                'id': None,
                'name': item_data.get('name', 'Unknown'),
                'price': price,
                'image_url': item_data.get('image', ''),
                'image': item_data.get('image', ''),
                'category': type('Category', (), {'name': item_data.get('category', 'Unknown')})(),
                'stock': 20,
                'original_price': None,
                'weight': None,
                'weight_unit': None,
                'get_unit_display': lambda: 'pcs',
            })()

            cart_items.append({
                'key': item_key,
                'item': temp_product,
                'quantity': quantity,
                'price': price,
                'subtotal': item_subtotal,
                'is_temp': True,
            })
            subtotal += item_subtotal
        else:
            try:
                product = Product.objects.get(id=int(item_key), is_available=True)
                quantity = item_data.get('quantity', 1)
                price = float(product.price)
                item_subtotal = price * quantity
                
                cart_items.append({
                    'key': item_key,
                    'item': product,
                    'quantity': quantity,
                    'price': price,
                    'subtotal': item_subtotal,
                    'is_temp': False,
                })
                subtotal += item_subtotal
            except Product.DoesNotExist:
                continue
    
    delivery_fee = 0 if subtotal >= 500 else 80.00
    total = subtotal + delivery_fee 
    cart_count = len(cart_items)
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'total': total,
        'cart_count': cart_count,
    }
    return render(request, 'mycart.html', context)

@require_POST
def add_to_cart(request, item_id=None):
    """Add item to cart - handles both ID and query parameters"""
    try:
        product_image = ''
        product_category = ''
        product_name = ''

        if item_id and item_id > 0:
            product = get_object_or_404(Product, id=item_id, is_available=True)
            product_name = product.name
            try:
                product_image = product.image.url if product.image else ''
            except Exception:
                product_image = ''
            product_category = product.category.name if getattr(product, 'category', None) else ''
        else:
            product_name = request.POST.get('product_name') or request.GET.get('name') or ''
            product_price = request.POST.get('product_price') or request.GET.get('price') or '0'
            product_image = request.POST.get('product_image') or request.GET.get('image') or ''
            product_category = request.POST.get('product_category') or request.GET.get('category') or ''

            product = type('Product', (), {
                'id': 0,
                'name': product_name,
                'price': product_price,
                'is_available': True
            })()

        quantity = int(request.POST.get('quantity', 1))

        cart = request.session.get('cart', {})

        if item_id and item_id > 0:
            item_key = str(item_id)
        else:
            item_key = f"temp_{product_name.replace(' ', '_')}"

        if item_key in cart:
            cart[item_key]['quantity'] += quantity
        else:
            cart[item_key] = {
                'quantity': quantity,
                'price': str(product.price),
                'name': product.name,
                'image': product_image,
                'category': product_category,
                'is_temp': item_id is None or item_id == 0
            }
        
        request.session['cart'] = cart
        request.session.modified = True
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'cart_count': len(cart),
                'message': f'{product.name} added to cart'
            })
        
        messages.success(request, f'{product.name} added to cart')
        return redirect('home:view_cart')
        
    except Exception as e:
        print(f"Error adding to cart: {e}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
        messages.error(request, 'Error adding item to cart')
        return redirect('home:items')

@require_POST
def update_cart(request, item_id):
    """Update cart item quantity"""
    try:
        quantity = int(request.POST.get('quantity', 1))
        cart = request.session.get('cart', {})
        item_id_str = str(item_id)
        
        if item_id_str in cart:
            if quantity > 0:
                cart[item_id_str]['quantity'] = quantity
                request.session['cart'] = cart
                request.session.modified = True
                
                # Recalculate all cart totals
                subtotal = 0
                for key, item_data in cart.items():
                    if item_data.get('is_temp'):
                        subtotal += float(item_data['price']) * item_data['quantity']
                    else:
                        try:
                            product = Product.objects.get(id=int(key), is_available=True)
                            subtotal += float(product.price) * item_data['quantity']
                        except Product.DoesNotExist:
                            subtotal += float(item_data['price']) * item_data['quantity']
                
              
                delivery_fee = 0 if subtotal >= 500 else 80.00
                total = subtotal + delivery_fee
                
             
                if cart[item_id_str].get('is_temp'):
                    new_subtotal = float(cart[item_id_str]['price']) * quantity
                else:
                    try:
                        product = Product.objects.get(id=item_id, is_available=True)
                        new_subtotal = float(product.price) * quantity
                    except Product.DoesNotExist:
                        new_subtotal = float(cart[item_id_str]['price']) * quantity
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'new_subtotal': new_subtotal,
                        'new_cart_subtotal': subtotal,
                        'new_delivery_fee': delivery_fee,
                        'new_total': total,
                        'cart_count': sum(item['quantity'] for item in cart.values()),
                        'message': 'Cart updated successfully'
                    })
                
                messages.success(request, 'Cart updated')
            else:
                del cart[item_id_str]
                request.session['cart'] = cart
                request.session.modified = True
                
               
                subtotal = 0
                for key, item_data in cart.items():
                    if item_data.get('is_temp'):
                        subtotal += float(item_data['price']) * item_data['quantity']
                    else:
                        try:
                            product = Product.objects.get(id=int(key), is_available=True)
                            subtotal += float(product.price) * item_data['quantity']
                        except Product.DoesNotExist:
                            subtotal += float(item_data['price']) * item_data['quantity']
                
                delivery_fee = 0 if subtotal >= 500 else 80.00
                total = subtotal + delivery_fee
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'new_cart_subtotal': subtotal,
                        'new_delivery_fee': delivery_fee,

                        'new_total': total,
                        'cart_count': sum(item['quantity'] for item in cart.values()),
                        'message': 'Item removed'
                    })
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Item not found'}, status=404)
            messages.error(request, 'Item not found')
            
    except Exception as e:
        print(f"Error updating cart: {e}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
        messages.error(request, 'Error updating cart')
    
    return redirect('home:view_cart')

@require_POST
def remove_from_cart(request, item_id):
    """Remove item from cart"""
    try:
        cart = request.session.get('cart', {})
        item_id_str = str(item_id)
        
        if item_id_str in cart:
            del cart[item_id_str]
            request.session['cart'] = cart
            request.session.modified = True
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'cart_count': len(cart),
                    'message': 'Item removed from cart'
                })
            
            messages.success(request, 'Item removed from cart')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Item not found'}, status=404)
            messages.error(request, 'Item not found')
            
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
        messages.error(request, 'Error removing item')
    
    return redirect('home:view_cart')

@require_POST
def update_temp_cart(request):
    """Update quantity of temporary cart items"""
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            item_key = data.get('item_key')
            quantity = int(data.get('quantity'))
        else:
            item_key = request.POST.get('item_key')
            quantity = int(request.POST.get('quantity', 1))
        
        cart = request.session.get('cart', {})
        
        if item_key in cart:
            cart[item_key]['quantity'] = quantity
            request.session['cart'] = cart
            request.session.modified = True
            
            # Calculate new subtotal for this item
            price = float(cart[item_key]['price'])
            new_subtotal = price * quantity
            
            # RECALCULATE ALL CART TOTALS
            subtotal = 0
            for key, item_data in cart.items():
                if item_data.get('is_temp'):
                    subtotal += float(item_data['price']) * item_data['quantity']
                else:
                    try:
                        product = Product.objects.get(id=int(key), is_available=True)
                        subtotal += float(product.price) * item_data['quantity']
                    except (Product.DoesNotExist, ValueError):
                        subtotal += float(item_data['price']) * item_data['quantity']
            
            # Calculate delivery fee (FREE for orders >= 500)
            delivery_fee = 0 if subtotal >= 500 else 80.00
            total = subtotal + delivery_fee
            
            return JsonResponse({
                'success': True,
                'new_subtotal': new_subtotal,
                'new_cart_subtotal': subtotal,
                'new_delivery_fee': delivery_fee,
                'new_total': total
            })
        
        return JsonResponse({'success': False, 'error': 'Item not found'}, status=404)
    except Exception as e:
        print(f"Error updating temp cart: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_POST
def remove_temp_item(request):
    """Remove temporary item from cart"""
    try:
        data = json.loads(request.body)
        item_key = data.get('item_key')
        
        cart = request.session.get('cart', {})
        
        if item_key in cart:
            del cart[item_key]
            request.session['cart'] = cart
            request.session.modified = True
            
            return JsonResponse({'success': True})
        
        return JsonResponse({'success': False, 'error': 'Item not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def checkout_cart(request):
    """Process checkout from cart"""
    if request.method == 'POST':
        # Get form data
        customer_name = request.POST.get('customer_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone_number')
        address = request.POST.get('address')
        
        cart = request.session.get('cart', {})
        
        if not cart:
            messages.error(request, 'Your cart is empty')
            return redirect('home:view_cart')
        
        # Create order
        order = Order.objects.create(
            order_number='ORD-' + str(uuid.uuid4().hex[:8].upper()),
            user=request.user if request.user.is_authenticated else None,
            customer_name=customer_name,
            email=email,
            phone_number=phone,
            address=address,
            status='pending',
            payment_status='pending'
        )
        
        subtotal = 0
        order_items_list = []  # Store items for email
        
        for item_key, item_data in cart.items():
            # Check if this is a temporary item (key is not a number)
            if item_data.get('is_temp') or not item_key.isdigit():
                # This is a temporary item
                product_name = item_data.get('name', 'Unknown Product')
                price = float(item_data.get('price', 0))
                quantity = item_data.get('quantity', 1)
                item_subtotal = price * quantity
                
                order_item = OrderItem.objects.create(
                    order=order,
                    food=None,  # No database product
                    product_name=product_name,
                    product_image=item_data.get('image', ''),
                    product_category=item_data.get('category', ''),
                    quantity=quantity,
                    price=price,
                    subtotal=item_subtotal
                )
                subtotal += item_subtotal
                
                # Add to email list
                order_items_list.append({
                    'name': product_name,
                    'quantity': quantity,
                    'price': price,
                    'subtotal': item_subtotal
                })
            else:
                try:
                    product = Product.objects.get(id=int(item_key), is_available=True)
                    quantity = item_data.get('quantity', 1)
                    item_subtotal = float(product.price) * quantity
                    
                    order_item = OrderItem.objects.create(
                        order=order,
                        food=product,
                        product_name=product.name,
                        quantity=quantity,
                        price=float(product.price),
                        subtotal=item_subtotal
                    )
                    subtotal += item_subtotal
                    
                    # Add to email list
                    order_items_list.append({
                        'name': product.name,
                        'quantity': quantity,
                        'price': float(product.price),
                        'subtotal': item_subtotal
                    })
                except Product.DoesNotExist:
                    continue
        
        # Update order totals
        delivery_fee = 80.00
        order.subtotal = subtotal
        order.delivery_fee = delivery_fee
        order.total_amount = subtotal + delivery_fee
        order.save()
        print("CHECKOUT FUNCTION CALLED")
        print(f"Order saved: {order.order_number}")
        print(f"Customer email: {email}")
        print(f"Items in order: {len(order_items_list)}")
        # ========== SEND ORDER CONFIRMATION EMAIL ==========
        try:
            email_sent = send_order_confirmation_email(order, order_items_list, delivery_fee)
            print(f"Email sent result: {email_sent}")
        except Exception as e:
            print(f"Email function crashed: {e}")
            email_sent = False
        
        # Clear cart
        del request.session['cart']
        request.session.modified = True
        
        # Success message with email status
        if email_sent:
            messages.success(request, f'Order placed successfully! A confirmation email has been sent to {email}')
        else:
            messages.success(request, f'Order placed successfully! (Email delivery failed, but your order is confirmed)')
        
        return redirect('home:order_confirmation', order_number=order.order_number)
    
    return redirect('home:view_cart')


def order(request):
    """Display order page for a single item"""
    product_name = request.GET.get('name', '')
    product_image = request.GET.get('image', '')
    product_price = request.GET.get('price', '0').replace('$', '').replace('£', '').replace('₮', '').replace('₹', '').replace('৳', '')
    product_category = request.GET.get('category', '')
    
    try:
        price = float(product_price)
    except ValueError:
        price = 0.0

    try:
        initial_quantity = int(request.GET.get('quantity', 1))
    except (TypeError, ValueError):
        initial_quantity = 1
    initial_quantity = max(1, min(initial_quantity, 20))
    
    cart = request.session.get('cart', {})
    cart_count = len(cart)
    
    # Create a temporary product object for the template
    class TempProduct:
        def __init__(self, name, image, price, category_name):
            self.id = None
            self.name = name
            self.image = image if image else None
            self.price = price
            self.stock = 20
            self.description = f"Fresh {name}"
            self.is_organic = False
            self.is_fresh = True
            self.unit = 'kg'
            
            # Create a category object
            class Category:
                def __init__(self, name):
                    self.name = name
            self.category = Category(category_name)
            
        def get_unit_display(self):
            return self.unit
    
    product = TempProduct(product_name, product_image, price, product_category)
    
    if request.method == 'POST':
        form = GroceryOrderForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            
            post_product_name = request.POST.get('product_name', product_name)
            post_product_price = (
                request.POST.get('product_price', str(price))
                .replace('$', '')
                .replace('£', '')
                .replace('₮', '')
                .replace('₹', '')
                .replace('৳', '')
            )
            post_product_category = request.POST.get('product_category', product_category)
            post_product_image = request.POST.get('product_image', product_image)
            
            try:
                post_price = float(post_product_price)
            except ValueError:
                post_price = price
            
            subtotal = post_price * quantity
            delivery_fee = 0 if subtotal >= 500 else 80
            total = subtotal + delivery_fee
            
            customer_name = form.cleaned_data.get('customer_name', '')
            email = form.cleaned_data.get('email', '')
            phone_number = form.cleaned_data.get('phone_number', '')
            address = form.cleaned_data.get('address', '')
            
            pending_order_number = 'TEMP-' + str(uuid.uuid4().hex[:8].upper())
            request.session['pending_order'] = {
                'product_name': post_product_name,
                'product_image': post_product_image,
                'product_category': post_product_category,
                'quantity': quantity,
                'price': post_price,
                'subtotal': subtotal,
                'delivery_fee': delivery_fee,
                'total': total,
                'customer_name': customer_name,
                'email': email,
                'phone_number': phone_number,
                'address': address,
                'order_number': pending_order_number,
            }
            request.session.modified = True
            
            from urllib.parse import urlencode
            query_params = urlencode({
                'name': post_product_name,
                'price': post_price,
                'quantity': quantity,
                'unit': 'kg',
                'order_id': pending_order_number,
            })
            return redirect(f"{reverse('home:payment')}?{query_params}")
    else:
        initial = {'quantity': initial_quantity}
        # Pre-fill for logged in users
        if request.user.is_authenticated:
            try:
                profile = request.user.profile
                initial.update({
                    'customer_name': request.user.get_full_name() or request.user.username,
                    'email': request.user.email,
                    'phone_number': profile.contact_number,
                    'address': profile.default_address,
                })
            except:
                initial.update({
                    'customer_name': request.user.get_full_name() or request.user.username,
                    'email': request.user.email,
                })
        form = GroceryOrderForm(initial=initial)
    
    context = {
        'product': product,
        'form': form,
        'cart_count': cart_count,
    }
    return render(request, 'order_items.html', context)


def send_order_confirmation_email(order, order_items_list, delivery_fee):
    """Send order confirmation email for cart checkout"""
    print("EMAIL FUNCTION STARTED")
    print(f"To: {order.email}")
    print(f"Items: {len(order_items_list)}")
    if not order.email:
         print("No email found!")
         return False
    
    try:
        subject = f'Order Confirmation - {order.order_number}'
        
        # Build the email content manually (no HTML template needed)
        items_text = ""
        for item in order_items_list:
            items_text += f"\n• {item['name']} x {item['quantity']} = ৳{item['subtotal']}"
        
        message = f"""
Dear {order.customer_name},

Thank you for your order at SwiftMart!

Order Details:
---------------
Order Number: {order.order_number}
Order Date: {order.created_at.strftime('%B %d, %Y at %I:%M %p')}

Items Ordered:{items_text}

Payment Summary:
----------------
Subtotal: ৳{order.subtotal}
Delivery Fee: ৳{delivery_fee}
Total Amount: ৳{order.total_amount}

Delivery Information:
---------------------
Address: {order.address}
Phone: {order.phone_number}

Your order will be delivered within 30-45 minutes.

Thank you for shopping with SwiftMart!

Best regards,
SwiftMart Team
"""
        
        # Send email using send_mail (which we know works)
        result = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.email],
            fail_silently=False,
        )
        
        print(f"Email sent successfully! Result: {result}")
        return True
        
    except Exception as e:
        print(f"Email error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def send_admin_order_notification(order):
    """Send order notification to admin"""
    try:
        subject = f'🚨 New Order - {order.order_number}'
        
        message = f"""
New Order Received!

Order: {order.order_number}
Customer: {order.customer_name}
Email: {order.email}
Phone: {order.phone_number}
Total: ৳{order.total_amount}

View this order in the admin panel.
"""
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['swiftmartswiftmart@gmail.com'],
            fail_silently=True,
        )
        print("Admin notification sent")
        
    except Exception as e:
        print(f"Admin notification error: {str(e)}")


def send_single_order_confirmation_email(order, product_name, quantity, price, subtotal, delivery_fee, total):
    """Send email for single item order"""
    try:
        subject = f'Order Confirmation - {order.order_number}'
        message = f"""
Dear {order.customer_name},

Thank you for your order at SwiftMart!

Order Number: {order.order_number}
Items: {product_name} x{quantity} = ৳{subtotal}
Total: ৳{total}

Delivery Address: {order.address}

Thank you for shopping with SwiftMart!
"""
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [order.email])
        print(f"Single order email sent to {order.email}")
        return True
    except Exception as e:
        print(f"Single order email error: {str(e)}")
        return False


def get_customer_defaults(request):
    """Return logged-in customer details for payment forms."""
    defaults = {
        'customer_name': '',
        'email': '',
        'phone_number': '',
        'address': '',
    }

    if request.user.is_authenticated:
        defaults['customer_name'] = request.user.get_full_name() or request.user.username
        defaults['email'] = request.user.email

        try:
            profile = request.user.profile
            defaults['phone_number'] = profile.contact_number
            defaults['address'] = profile.default_address
        except UserProfile.DoesNotExist:
            pass

    return defaults


def order_item(request, item_id):
    """Order a specific item"""
    product = get_object_or_404(Product, id=item_id, is_available=True)
    
    # Get cart count for navbar
    cart = request.session.get('cart', {})
    cart_count = len(cart)
    
    if request.method == 'POST':
        form = GroceryOrderForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            
            order = form.save(commit=False)
            order.status = 'pending'
            order.payment_status = 'pending'
            
            if request.user.is_authenticated:
                order.user = request.user
            
            order.save()
            
            # Create order item
            OrderItem.objects.create(
                order=order,
                food=product,
                quantity=quantity,
                price=product.price,
                subtotal=float(product.price) * quantity
            )
            
            # Update order totals
            order.subtotal = float(product.price) * quantity
            order.delivery_fee = 2.00
            order.tax = order.subtotal * 0.05
            order.total_amount = order.subtotal + order.delivery_fee + order.tax
            order.save()
            
            messages.success(request, 'Order placed successfully')
            return redirect('home:order_confirmation', order_number=order.order_number)
    else:
        form = GroceryOrderForm(initial={'quantity': 1})
        if request.user.is_authenticated:
            try:
                profile = request.user.profile
                form.initial.update({
                    'customer_name': request.user.get_full_name() or request.user.username,
                    'email': request.user.email,
                    'phone_number': profile.contact_number,
                })
            except:
                pass
    
    context = {
        'product': product,
        'form': form,
        'cart_count': cart_count,
    }
    return render(request, 'order.html', context)

def order_confirmation(request, order_number):
    """Display order confirmation"""
    order = get_object_or_404(Order, order_number=order_number)
    
    # Get cart count for navbar
    cart = request.session.get('cart', {})
    cart_count = len(cart)
    
    context = {
        'order': order,
        'order_items': order.items.all(),
        'cart_count': cart_count,
    }
    return render(request, 'order_confirmation.html', context)

def order_success(request, order_number):
    """Display order success page"""
    order = get_object_or_404(Order, order_number=order_number)
    
    # Get cart count for navbar
    cart = request.session.get('cart', {})
    cart_count = len(cart)
    
    context = {
        'order': order,
        'order_items': order.items.all(),
        'cart_count': cart_count,
    }
    return render(request, 'order_success.html', context)

@login_required
def order_list(request):
    """Display user's orders"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get cart count for navbar
    cart = request.session.get('cart', {})
    cart_count = len(cart)
    
    context = {
        'orders': page_obj,
        'cart_count': cart_count
    }
    return render(request, 'order_list.html', context)

def order_detail(request, order_number):
    """Display order details"""
    order = get_object_or_404(Order, order_number=order_number)
    
    # Check permission
    if order.user and order.user != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to view this order')
        return redirect('home:index')
    
    # Get cart count for navbar
    cart = request.session.get('cart', {})
    cart_count = len(cart)
    
    context = {
        'order': order,
        'order_items': order.items.all(),
        'cart_count': cart_count,
    }
    return render(request, 'order_detail.html', context)

@login_required
def cancel_order(request, order_number):
    """Cancel an order"""
    order = get_object_or_404(Order, order_number=order_number)
    
    if order.user != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to cancel this order')
        return redirect('home:index')
    
    if order.status in ['pending','processing']:
        order.status = 'cancelled'
        order.save()
        messages.success(request, 'Order cancelled successfully')
    else:
        messages.error(request, f'Order cannot be cancelled as it is {order.status}')
    
    return redirect('home:order_detail', order_number=order.order_number)


def payment_from_cart(request):
    """Create payment page from cart contents"""
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, 'Your cart is empty')
        return redirect('home:view_cart')

    subtotal = 0
    total_quantity = 0
    item_names = []

    for key, item_data in cart.items():
        qty = item_data.get('quantity', 1)
        total_quantity += qty
        if item_data.get('is_temp') or not key.isdigit():
            price = float(item_data.get('price', 0))
            item_names.append(item_data.get('name', 'Unknown'))
        else:
            try:
                product = Product.objects.get(id=int(key), is_available=True)
                price = float(product.price)
                item_names.append(product.name)
            except Product.DoesNotExist:
                continue
        subtotal += price * qty

    delivery_fee = 0 if subtotal >= 500 else 80.00
    total = subtotal + delivery_fee

    if len(item_names) == 1:
        product_name = item_names[0]
    elif len(item_names) == 2:
        product_name = f'{item_names[0]} & {item_names[1]}'
    else:
        product_name = f'{item_names[0]} & {len(item_names) - 1} more items'

    order_number = 'CART-' + str(uuid.uuid4().hex[:8].upper())

    order = {
        'order_number': order_number,
        'product_name': product_name,
        'price': round(subtotal / total_quantity, 2) if total_quantity > 0 else 0,
        'quantity': total_quantity,
        'unit': 'items',
        'subtotal': subtotal,
        'delivery_charge': delivery_fee,
        'total': total,
        'is_cart': True,
    }

    cart_count = len(cart)
    context = {
        'order': order,
        'cart_count': cart_count,
        'is_cart_payment': True,
    }
    return render(request, 'payment.html', context)


def payment(request):
    """Display payment page"""
    order_number = request.GET.get('order_number')
    order = None
    is_temp_order = False
    
    
    cart = request.session.get('cart', {})
    cart_count = len(cart)
    
    
    print("="*50)
    print("PAYMENT VIEW - GET parameters:")
    for key, value in request.GET.items():
        print(f"  {key}: '{value}'")
    print("="*50)
    
    if order_number and not order_number.startswith('TEMP-'):
        try:
            order = Order.objects.get(order_number=order_number)
        except Order.DoesNotExist:
            order = None
    
    if not order:
        
        is_temp_order = True
        product_name = request.GET.get('name', '')
        product_price = request.GET.get('price', '0').replace('$', '').replace('₹', '').replace('৳', '')
        quantity = int(request.GET.get('quantity', 1))
        
        # Get unit from query parameters
        unit = request.GET.get('unit', 'kg')
        
        # Debug print
        print(f"Payment page - Product: {product_name}")
        print(f"Payment page - Price from URL: '{request.GET.get('price')}'")
        print(f"Payment page - Cleaned price: '{product_price}'")
        print(f"Payment page - Quantity from URL: '{request.GET.get('quantity')}'")
        print(f"Payment page - Quantity (int): {quantity}")
        print(f"Payment page - Unit from URL: '{request.GET.get('unit')}'")
        print(f"Payment page - Unit (using): '{unit}'")
        
        try:
            price = float(product_price)
        except ValueError:
            price = 0.0
            
        subtotal = price * quantity
        delivery_charge = 80.00  # Make sure this matches your template
        total = subtotal + delivery_charge
        
        print(f"Payment page - Calculated subtotal: {subtotal}")
        print(f"Payment page - Calculated total: {total}")
        
        order = {
            'order_number': 'TEMP-' + str(uuid.uuid4().hex[:8].upper()),
            'product_name': product_name,
            'price': price,
            'quantity': quantity,
            'unit': unit,
            'subtotal': subtotal,
            'delivery_charge': delivery_charge,
            'total': total,
            'is_temp': True
        }
    
    customer_defaults = get_customer_defaults(request)
    pending_order = request.session.get('pending_order', {}) or {}
    if request.GET.get('order_id') != pending_order.get('order_number'):
        pending_order = {}

    context = {
        'order': order,
        'cart_count': cart_count,
        'is_temp_order': is_temp_order,
        'pending_customer_name': pending_order.get('customer_name') or customer_defaults['customer_name'],
        'pending_email': pending_order.get('email') or customer_defaults['email'],
        'pending_phone': pending_order.get('phone_number') or customer_defaults['phone_number'],
        'pending_address': pending_order.get('address') or customer_defaults['address'],
        'pending_image': pending_order.get('product_image', ''),
    }
    return render(request, 'payment.html', context)

@require_POST
def process_payment(request, order_number):
    """Process payment for an order"""
    
    payment_method = request.POST.get('payment_method')
    
    if not payment_method:
        return JsonResponse({
            'success': False,
            'message': 'Please select a payment method'
        }, status=400)
    
    # Get customer details from POST, then fall back to the logged-in profile.
    customer_defaults = get_customer_defaults(request)
    customer_name = request.POST.get('customer_name') or customer_defaults['customer_name']
    email = request.POST.get('email') or customer_defaults['email']
    phone = request.POST.get('phone_number') or customer_defaults['phone_number']
    address = request.POST.get('address') or customer_defaults['address']
    
    # Get order details from POST
    product_name = request.POST.get('product_name', '')
    quantity = int(request.POST.get('quantity', 1))
    total_amount = float(request.POST.get('total_amount', 0))
    
    # Calculate delivery fee and subtotal
    posted_delivery_fee = request.POST.get('delivery_fee')
    posted_subtotal = request.POST.get('subtotal')
    delivery_fee = float(posted_delivery_fee) if posted_delivery_fee not in (None, '') else 80.00
    subtotal = float(posted_subtotal) if posted_subtotal not in (None, '') else total_amount - delivery_fee
    price_per_unit = subtotal / quantity if quantity > 0 else 0
    
    
    if order_number.startswith('CART-'):
        cart = request.session.get('cart', {})
        if not cart:
            return JsonResponse({
                'success': False,
                'message': 'Cart data not found'
            }, status=400)

        new_order_number = 'ORD-' + str(uuid.uuid4().hex[:8].upper())

        cart_subtotal = 0
        cart_items_data = []
        for key, item_data in cart.items():
            qty = item_data.get('quantity', 1)
            price = float(item_data.get('price', 0))
            product_obj = None
            p_name = item_data.get('name', 'Unknown')
            p_image = item_data.get('image', '')
            p_category = item_data.get('category', '')

            if not item_data.get('is_temp') and key.isdigit():
                try:
                    product_obj = Product.objects.get(id=int(key), is_available=True)
                    price = float(product_obj.price)
                    p_name = product_obj.name
                except Product.DoesNotExist:
                    pass

            item_total = price * qty
            cart_subtotal += item_total
            cart_items_data.append({
                'product': product_obj,
                'name': p_name,
                'image': p_image,
                'category': p_category,
                'quantity': qty,
                'price': price,
                'subtotal': item_total,
            })

        cart_delivery = 0 if cart_subtotal >= 500 else 80.00
        cart_total = cart_subtotal + cart_delivery

        order = Order.objects.create(
            order_number=new_order_number,
            user=request.user if request.user.is_authenticated else None,
            customer_name=customer_name or (request.user.get_full_name() if request.user.is_authenticated else ''),
            email=email or (request.user.email if request.user.is_authenticated else ''),
            phone_number=phone,
            address=address,
            subtotal=cart_subtotal,
            delivery_fee=cart_delivery,
            tax=0,
            total_amount=cart_total,
            payment_method=payment_method,
            status='processing',
            payment_status='paid',
        )

        for ci in cart_items_data:
            OrderItem.objects.create(
                order=order,
                item=ci['product'],
                product_name=ci['name'],
                product_image=ci['image'],
                product_category=ci['category'],
                quantity=ci['quantity'],
                price=ci['price'],
                subtotal=ci['subtotal'],
            )
        email_sent = False
        try:
            email_sent = send_order_confirmation_email(order, cart_items_data, cart_delivery)
            print("Email sent after CART order")
        except Exception as e:
            print("Email error:", str(e))

        if 'cart' in request.session:
            del request.session['cart']
        request.session.modified = True

        return JsonResponse({
            'success': True,
            'order_id': order.order_number,
            'message': 'Payment processed successfully',
            'email_sent': email_sent,
        })

    elif order_number.startswith('TEMP-'):
        new_order_number = 'ORD-' + str(uuid.uuid4().hex[:8].upper())
        
        order = Order.objects.create(
            order_number=new_order_number,
            user=request.user if request.user.is_authenticated else None,
            customer_name=customer_name,
            email=email,
            phone_number=phone,
            address=address,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            tax=0,
            total_amount=total_amount,
            payment_method=payment_method,
            status='processing',
            payment_status='paid'
        )
        
        OrderItem.objects.create(
            order=order,
            item=None,  
            product_name=product_name,
            quantity=quantity,
            price=price_per_unit,
            subtotal=subtotal
        )
        email_sent = False
        try:
            order_items_list = [{
                'name': product_name,
                'quantity': quantity,
                'price': price_per_unit,
                'subtotal': subtotal
            }]
            email_sent = send_order_confirmation_email(order, order_items_list, delivery_fee)
            print("Email sent after TEMP order")
        except Exception as e:
            print("Email error:", str(e))
        
        return JsonResponse({
            'success': True,
            'order_id': order.order_number,
            'message': 'Payment processed successfully',
            'email_sent': email_sent,
        })
    
    else:
        # If order doesn't exist, CREATE it
        order, created = Order.objects.get_or_create(
            order_number=order_number,
            defaults={
                'user': request.user if request.user.is_authenticated else None,
                'customer_name': customer_name,
                'email': email,
                'phone_number': phone,
                'address': address,
                'subtotal': subtotal,
                'delivery_fee': delivery_fee,
                'tax': 0,
                'total_amount': total_amount,
                'payment_method': payment_method,
                'status': 'processing',
                'payment_status': 'paid'
            }
        )

        if created and product_name:
            OrderItem.objects.create(
                order=order,
                item=None,
                product_name=product_name,
                quantity=quantity,
                price=price_per_unit,
                subtotal=subtotal
            )
        else:
            order.payment_method = payment_method
            order.payment_status = 'paid'
            order.status = 'processing'
            order.customer_name = customer_name or order.customer_name
            order.email = email or order.email
            order.phone_number = phone or order.phone_number
            order.address = address or order.address
            order.save()

        order_items_list = [{
            'name': item.get_name(),
            'quantity': item.quantity,
            'price': item.price,
            'subtotal': item.subtotal,
        } for item in order.items.all()]
        if not order_items_list and product_name:
            order_items_list = [{
                'name': product_name,
                'quantity': quantity,
                'price': price_per_unit,
                'subtotal': subtotal,
            }]

        email_sent = False
        try:
            email_sent = send_order_confirmation_email(order, order_items_list, order.delivery_fee)
        except Exception as e:
            print("Email error:", str(e))

        return JsonResponse({
            'success': True,
            'order_id': order.order_number,
            'message': 'Payment successful!',
            'email_sent': email_sent,
        })


def payment_successful(request, order_number):
    """Display payment successful page"""
    try:
        order = Order.objects.get(order_number=order_number)
        context = {'order': order}
    except Order.DoesNotExist:
        context = {'order_number': order_number}
    
    # Get cart count for navbar
    cart = request.session.get('cart', {})
    cart_count = len(cart)
    context['cart_count'] = cart_count
    
    return render(request, 'payment_successfull.html', context)

def payment_failed(request, order_number):
    """Display payment failed page"""
    
    cart = request.session.get('cart', {})
    cart_count = len(cart)
    
    context = {
        'order_number': order_number,
        'error_code': 'PAYMENT_FAILED_' + str(uuid.uuid4().hex[:4].upper()),
        'current_time': datetime.now(),
        'cart_count': cart_count,
    }
    return render(request, 'payment_failed.html', context)


def contact(request):
    """Display contact page"""
   
    cart = request.session.get('cart', {})
    cart_count = len(cart)
    
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
           
            messages.success(request, 'Thank you for contacting us! We will get back to you soon.')
            return redirect('contact')
    else:
        form = ContactForm()
    
    context = {
        'form': form,
        'cart_count': cart_count
    }
    return render(request, 'contact.html', context)


def login_view(request):
    """Handle user login"""
    cart = request.session.get('cart', {})
    cart_count = len(cart)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name}!')
                return redirect('home:index')
            else:
                messages.error(request, 'Please verify your email address before logging in. Check your inbox for the activation link.')
                return render(request, 'login.html', {'cart_count': cart_count})
        else:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'login.html', {'cart_count': cart_count})

def signup(request):
    """Handle user registration with email verification"""
    # Get cart count for navbar
    cart = request.session.get('cart', {})
    cart_count = len(cart)
    
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            # Check if email already exists
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already registered! Please login or use a different email.')
                return render(request, 'signup.html', {'form': form, 'cart_count': cart_count})
            
            # Create user with is_active=False
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=name,
                is_active=False
            )
            
            # Create profile
            UserProfile.objects.create(user=user)
            
            # Send verification email
            try:
                current_site = get_current_site(request)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = account_activation_token.make_token(user)
                
                # Build activation link
                activation_link = f"http://{current_site.domain}/activate/{uid}/{token}/"
                
                # Simple text email (avoid template errors)
                mail_subject = 'Activate Your SwiftMart Account'
                mail_message = f"""
Hello {name},

Thank you for registering at SwiftMart!

Please click the link below to activate your account:
{activation_link}

This link will expire in 24 hours.

If you didn't create an account with SwiftMart, please ignore this email.

Best regards,
SwiftMart Team
"""
                
                # Send email
                email_message = EmailMessage(
                    subject=mail_subject,
                    body=mail_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[email],
                )
                email_message.send(fail_silently=False)
                
                messages.success(request, f'Welcome {name}! Please check your email ({email}) to activate your account.')
                return redirect('login')
                
            except Exception as e:
                # If email fails, delete the user
                user.delete()
                messages.error(request, f'Unable to send verification email. Please try again later. Error: {str(e)}')
                return render(request, 'signup.html', {'form': form, 'cart_count': cart_count})
                
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = SignupForm()
    
    context = {
        'form': form,
        'cart_count': cart_count
    }
    return render(request, 'signup.html', context)


def activate(request, uidb64, token):
    """Activate user account via email link"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and account_activation_token.check_token(user, token):
        # Activate the user
        user.is_active = True
        user.save()
        
        # Now login the user (no need to set backend after removing allauth)
        login(request, user)
        
        messages.success(request, f'Congratulations {user.first_name}! Your account has been activated. You are now logged in.')
        return redirect('home:index')
    else:
        messages.error(request, 'Activation link is invalid or has expired! Please register again.')
        return redirect('signup')

def resend_activation(request):
    """Resend activation email to user"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email, is_active=False)
            
            # Resend activation email
            current_site = get_current_site(request)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = account_activation_token.make_token(user)
            
            plain_message = f"""
Hello {user.first_name},

Please click the link below to activate your SwiftMart account:
http://{current_site.domain}/activate/{uid}/{token}/

This link will expire in 24 hours.

Best regards,
SwiftMart Team
"""
            
            send_mail(
                'Activate Your SwiftMart Account - Resend',
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            messages.success(request, f'Activation email has been resent to {email}. Please check your inbox.')
        except User.DoesNotExist:
            messages.error(request, 'No inactive account found with this email address.')
    
    return render(request, 'resend_activation.html')


def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home:index')  

@login_required
def dashboard(request):
    """Display user dashboard"""
    user = request.user
    orders = Order.objects.filter(user=user).order_by('-created_at')[:5]
    
   
    cart = request.session.get('cart', {})
    cart_count = len(cart)
    
    # Try to get or create profile
    try:
        profile = user.profile
    except:
        # Create profile if it doesn't exist
        profile = UserProfile.objects.create(user=user)
    
    # Handle profile update
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'profile':
            profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
            if profile_form.is_valid():
                profile_form.save()
                
                # Update user fields
                user.first_name = request.POST.get('first_name', user.first_name)
                user.last_name = request.POST.get('last_name', user.last_name)
                user.email = request.POST.get('email', user.email)
                user.save()
                
                messages.success(request, 'Profile updated successfully!')
            else:
                for field, errors in profile_form.errors.items():
                    for error in errors:
                        messages.error(request, error)
        
        elif form_type == 'address':
            address_form = AddressForm(request.POST)
            if address_form.is_valid():
                profile.default_address = address_form.cleaned_data['address']
                profile.save()
                messages.success(request, 'Address updated successfully!')
            else:
                for field, errors in address_form.errors.items():
                    for error in errors:
                        messages.error(request, error)
        
        return redirect('home:dashboard')
    
    else:
        profile_form = UserProfileForm(instance=profile)
        address_form = AddressForm(initial={'address': profile.default_address})
    
    context = {
        'user': user,
        'orders': orders,
        'profile_form': profile_form,
        'address_form': address_form,
        'cart_count': cart_count,
    }
    return render(request, 'dashboard.html', context)

@login_required
def update_profile(request):
    """View to update user profile"""
    if request.method == 'POST':
        user = request.user
        profile = user.profile
        
        # Update user fields
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        
        
        profile.contact_number = request.POST.get('contact_number', '')
        
        
        if 'profile_pic' in request.FILES:
            profile.profile_pic = request.FILES['profile_pic']
        
        profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('home:dashboard')
    
    return redirect('home:dashboard')

@login_required
def update_address(request):
    """View to update user address"""
    if request.method == 'POST':
        address = request.POST.get('address', '')
        
        if address:
            profile = request.user.profile
            profile.default_address = address
            profile.save()
            messages.success(request, 'Address updated successfully!')
        else:
            messages.error(request, 'Address cannot be empty.')
        
        return redirect('home:dashboard')
    
    return redirect('home:dashboard')

@login_required
def reorder(request, order_id):
    """Reorder items from a previous order"""
    try:
        # Try to find the order
        original_order = Order.objects.get(order_number=order_id, user=request.user)
        
        # Get current cart
        cart = request.session.get('cart', {})
        
        items_added = 0
        
        # Process each item in the order
        for order_item in original_order.items.all():
            # Check if the product still exists and is available
            if order_item.item and order_item.item.is_available and order_item.item.stock > 0:
                product = order_item.item
                product_id = str(product.id)
                
                if product_id in cart:
                    # Update quantity if already in cart
                    cart[product_id]['quantity'] += order_item.quantity
                else:
                    # Add new item to cart
                    cart[product_id] = {
                        'quantity': order_item.quantity,
                        'name': product.name,
                        'price': str(product.price),
                        'image': product.image.url if product.image else '',
                        'category': product.category.name if product.category else '',
                    }
                items_added += 1
            elif order_item.item and not order_item.item.is_available:
                # Product exists but not available
                messages.warning(request, f'{order_item.get_name()} is no longer available')
            elif not order_item.item and order_item.product_name:
                # Product was deleted but we have saved name
                cart[f"temp_{order_item.id}"] = {
                    'quantity': order_item.quantity,
                    'name': order_item.product_name,
                    'price': str(order_item.price),
                    'image': order_item.product_image,
                    'category': order_item.product_category,
                    'is_temp': True,
                }
                items_added += 1
        
        if items_added > 0:
            # Save cart to session
            request.session['cart'] = cart
            request.session.modified = True
            messages.success(request, f'{items_added} item(s) added to your cart!')
        else:
            messages.warning(request, 'No items could be added to cart (items may be unavailable)')
        
        return redirect('home:view_cart')
        
    except Order.DoesNotExist:
        messages.error(request, 'Order not found')
        return redirect('home:order_list')
    except Exception as e:
        messages.error(request, f'Error adding items to cart: {str(e)}')
        return redirect('home:order_list')
    
def check_order_status(request, order_number):
    """AJAX endpoint to check order status"""
    try:
        order = Order.objects.get(order_number=order_number)
        return JsonResponse({
            'success': True,
            'status': order.status,
            'status_display': order.get_status_display(),
        })
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order not found'}, status=404)
