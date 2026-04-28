from django.contrib import admin
from .models import Category, Product, Order, OrderItem, UserProfile

# Category Admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    list_editable = ['is_active']
    list_per_page = 20
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Media', {
            'fields': ('image',),
            'classes': ('wide',)
        }),
        ('Status', {
            'fields': ('is_active',),
            'classes': ('wide',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at']

# Product Admin
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'original_price', 'stock', 'unit', 'is_available', 'is_popular']
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['category', 'is_available', 'is_popular', 'is_organic', 'is_fresh', 'unit']
    search_fields = ['name', 'description']
    list_editable = ['price', 'stock', 'is_available', 'is_popular']
    ordering = ['-created_at']
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'original_price'),
            'classes': ('wide',)
        }),
        ('Inventory', {
            'fields': ('stock', 'unit', 'weight', 'weight_unit'),
            'classes': ('wide',)
        }),
        ('Product Attributes', {
            'fields': ('is_organic', 'is_fresh', 'is_popular', 'is_available'),
            'classes': ('wide',)
        }),
        ('Media', {
            'fields': ('image',),
            'classes': ('wide',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    
    # Add custom actions
    actions = ['make_available', 'make_unavailable', 'make_popular']
    
    def make_available(self, request, queryset):
        queryset.update(is_available=True)
    make_available.short_description = "Mark selected products as available"
    
    def make_unavailable(self, request, queryset):
        queryset.update(is_available=False)
    make_unavailable.short_description = "Mark selected products as unavailable"
    
    def make_popular(self, request, queryset):
        queryset.update(is_popular=True)
    make_popular.short_description = "Mark selected products as popular"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ['get_item_name', 'quantity', 'price', 'subtotal']
    readonly_fields = ['get_item_name']  
    
    def get_item_name(self, obj):
        return obj.get_name()
    get_item_name.short_description = 'Item Name'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer_name', 'get_items_count', 'total_amount', 'status', 'payment_status', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['order_number', 'customer_name', 'email']
    inlines = [OrderItemInline]
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    
    def get_items_count(self, obj):
        count = obj.items.count()
        if count == 1:
            item = obj.items.first()
            return f"{item.get_name()} x {item.quantity}"
        return f"{count} items"
    get_items_count.short_description = 'Items'
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'payment_status', 'payment_method')
        }),
        ('Customer Details', {
            'fields': ('customer_name', 'email', 'phone_number', 'address', 'special_instructions')
        }),
        ('Payment Details', {
            'fields': ('subtotal', 'delivery_fee', 'tax', 'discount', 'total_amount')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order_link', 'customer_name', 'item_name', 'quantity', 'display_price', 'display_subtotal']
    list_filter = ['order__status', 'order__payment_status']  # Fixed: use order__status, not food__category
    search_fields = ['order__order_number', 'order__customer_name', 'product_name', 'food__name']
    readonly_fields = ['item_name', 'display_price', 'display_subtotal']  # Use methods, not 'food'
    
    def order_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        url = reverse('admin:home_order_change', args=[obj.order.id])
        return format_html('<a href="{}">{}</a>', url, obj.order.order_number)
    order_link.short_description = 'Order'
    order_link.admin_order_field = 'order__order_number'
    
    def customer_name(self, obj):
        return obj.order.customer_name or '-'
    customer_name.short_description = 'Customer'
    customer_name.admin_order_field = 'order__customer_name'
    
    def item_name(self, obj):
        return obj.get_name() or 'Unknown Item'
    item_name.short_description = 'Item'
    item_name.admin_order_field = 'food__name'
    
    def display_price(self, obj):
        return f"৳{obj.price}"
    display_price.short_description = 'Price'
    
    def display_subtotal(self, obj):
        return f"৳{obj.subtotal}"
    display_subtotal.short_description = 'Subtotal'
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order', 'item_name', 'quantity', 'display_price', 'display_subtotal')
        }),
        ('Product Details', {
            'fields': ('food', 'product_name', 'product_category'),
            'classes': ('collapse',)
        }),
    )

# UserProfile Admin
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'contact_number', 'email_verified', 'created_at']
    list_filter = ['email_verified', 'created_at']
    search_fields = ['user__username', 'user__email', 'contact_number', 'default_address']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Contact Information', {
            'fields': ('contact_number', 'default_address'),
            'classes': ('wide',)
        }),
        ('Profile Details', {
            'fields': ('profile_pic', 'email_verified'),
            'classes': ('wide',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )