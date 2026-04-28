"""Seed the database with realistic grocery categories and products.

Downloads real product images from Unsplash into the media folder and
creates matching Category and Product records.

Usage:
    python manage.py seed_data           # adds data, skips items that already exist
    python manage.py seed_data --fresh   # wipes existing categories/products first
"""
from __future__ import annotations

import io
import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from home.models import Category, Product


# Category hero images (unsplash direct image URLs).
CATEGORIES = [
    {
        "name": "Fresh Fruits",
        "description": "Hand-picked seasonal fruits delivered fresh from the farm.",
        "image": "https://images.unsplash.com/photo-1610832958506-aa56368176cf?w=1000&q=80",
    },
    {
        "name": "Fresh Vegetables",
        "description": "Crisp, locally-sourced vegetables full of nutrients.",
        "image": "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=1000&q=80",
    },
    {
        "name": "Dairy & Eggs",
        "description": "Farm-fresh milk, cheese, yogurt and cage-free eggs.",
        "image": "https://images.unsplash.com/photo-1628088062854-d1870b4553da?w=1000&q=80",
    },
    {
        "name": "Bakery",
        "description": "Freshly baked bread, pastries and artisan treats.",
        "image": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=1000&q=80",
    },
    {
        "name": "Meat & Seafood",
        "description": "Premium cuts and fresh catches, responsibly sourced.",
        "image": "https://images.unsplash.com/photo-1607623814075-e51df1bdc82f?w=1000&q=80",
    },
    {
        "name": "Beverages",
        "description": "Juices, teas, coffee and refreshing drinks.",
        "image": "https://images.unsplash.com/photo-1625772299848-391b6a87d7b3?w=1000&q=80",
    },
    {
        "name": "Snacks",
        "description": "Crunchy, sweet and savoury snacks for every craving.",
        "image": "https://images.unsplash.com/photo-1621939514649-280e2ee25f60?w=1000&q=80",
    },
    {
        "name": "Pantry Staples",
        "description": "Rice, oils, pasta, spices and everyday essentials.",
        "image": "https://images.unsplash.com/photo-1607301405390-d831c242f59b?w=1000&q=80",
    },
]


PRODUCTS = {
    "Fresh Fruits": [
        {"name": "Red Apples", "price": 180, "original_price": 220, "unit": "kg",
         "description": "Crunchy and sweet red apples, perfect for snacking or baking.",
         "is_popular": True, "is_fresh": True,
         "image": "https://images.unsplash.com/photo-1568702846914-96b305d2aaeb?w=800&q=80"},
        {"name": "Bananas", "price": 60, "original_price": 75, "unit": "dozen",
         "description": "Ripe, naturally sweet bananas rich in potassium.",
         "is_popular": True, "is_fresh": True,
         "image": "https://images.unsplash.com/photo-1603833665858-e61d17a86224?w=800&q=80"},
        {"name": "Navel Oranges", "price": 140, "unit": "kg",
         "description": "Juicy, seedless navel oranges bursting with vitamin C.",
         "is_fresh": True,
         "image": "https://images.unsplash.com/photo-1547514701-42782101795e?w=800&q=80"},
        {"name": "Strawberries", "price": 220, "original_price": 260, "unit": "g", "weight": 250, "weight_unit": "g",
         "description": "Plump, fragrant strawberries — great on yogurt or on their own.",
         "is_popular": True, "is_organic": True, "is_fresh": True,
         "image": "https://images.unsplash.com/photo-1464965911861-746a04b4bca6?w=800&q=80"},
        {"name": "Alphonso Mango", "price": 320, "unit": "kg",
         "description": "The king of mangoes — rich, buttery and aromatic.",
         "is_popular": True, "is_fresh": True,
         "image": "https://images.unsplash.com/photo-1553279768-865429fa0078?w=800&q=80"},
        {"name": "Seedless Watermelon", "price": 90, "unit": "pcs",
         "description": "Cool, crisp and refreshing — perfect for hot days.",
         "is_fresh": True,
         "image": "https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=800&q=80"},
        {"name": "Green Grapes", "price": 160, "unit": "kg",
         "description": "Sweet, juicy seedless green grapes.",
         "is_fresh": True,
         "image": "https://images.unsplash.com/photo-1537640538966-79f369143f8f?w=800&q=80"},
        {"name": "Pineapple", "price": 110, "unit": "pcs",
         "description": "Tropical pineapple with a perfect sweet-tangy balance.",
         "is_fresh": True,
         "image": "https://images.unsplash.com/photo-1550258987-190a2d41a8ba?w=800&q=80"},
    ],
    "Fresh Vegetables": [
        {"name": "Ripe Tomatoes", "price": 55, "unit": "kg",
         "description": "Vine-ripened tomatoes, rich in flavour and lycopene.",
         "is_popular": True, "is_fresh": True,
         "image": "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=800&q=80"},
        {"name": "Potatoes", "price": 40, "unit": "kg",
         "description": "Versatile everyday potatoes — boil, fry or roast.",
         "is_popular": True, "is_fresh": True,
         "image": "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=800&q=80"},
        {"name": "Red Onions", "price": 60, "unit": "kg",
         "description": "Sharp, flavourful red onions — a kitchen staple.",
         "is_fresh": True,
         "image": "https://images.unsplash.com/photo-1580201092675-a0a6a6cafbb1?w=800&q=80"},
        {"name": "Carrots", "price": 70, "unit": "kg",
         "description": "Sweet, crunchy carrots loaded with beta-carotene.",
         "is_fresh": True, "is_organic": True,
         "image": "https://images.unsplash.com/photo-1445282768818-728615cc910a?w=800&q=80"},
        {"name": "Broccoli", "price": 120, "unit": "kg",
         "description": "Fresh green broccoli florets, rich in fibre.",
         "is_fresh": True, "is_organic": True,
         "image": "https://images.unsplash.com/photo-1459411621453-7b03977f4bfc?w=800&q=80"},
        {"name": "Baby Spinach", "price": 80, "unit": "g", "weight": 200, "weight_unit": "g",
         "description": "Tender baby spinach leaves — perfect for salads and smoothies.",
         "is_fresh": True, "is_organic": True,
         "image": "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=800&q=80"},
        {"name": "Cucumber", "price": 50, "unit": "kg",
         "description": "Cool, crisp cucumbers — great for salads or pickling.",
         "is_fresh": True,
         "image": "https://images.unsplash.com/photo-1449300079323-02e209d9d3a6?w=800&q=80"},
        {"name": "Bell Peppers Mix", "price": 160, "unit": "kg",
         "description": "Colourful red, yellow and green peppers — crunchy and sweet.",
         "is_popular": True, "is_fresh": True,
         "image": "https://images.unsplash.com/photo-1563565375-f3fdfdbefa83?w=800&q=80"},
    ],
    "Dairy & Eggs": [
        {"name": "Full Cream Milk", "price": 95, "unit": "l", "weight": 1, "weight_unit": "l",
         "description": "Farm-fresh full cream milk, pasteurised and homogenised.",
         "is_popular": True,
         "image": "https://images.unsplash.com/photo-1563636619-e9143da7973b?w=800&q=80"},
        {"name": "Cheddar Cheese Block", "price": 380, "unit": "g", "weight": 200, "weight_unit": "g",
         "description": "Aged cheddar cheese with a sharp, rich flavour.",
         "image": "https://images.unsplash.com/photo-1486297678162-eb2a19b0a32d?w=800&q=80"},
        {"name": "Greek Yogurt", "price": 140, "unit": "g", "weight": 400, "weight_unit": "g",
         "description": "Thick and creamy Greek yogurt, high in protein.",
         "is_popular": True,
         "image": "https://images.unsplash.com/photo-1488477181946-6428a0291777?w=800&q=80"},
        {"name": "Unsalted Butter", "price": 210, "unit": "g", "weight": 200, "weight_unit": "g",
         "description": "Creamy unsalted butter, perfect for cooking and baking.",
         "image": "https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?w=800&q=80"},
        {"name": "Free Range Eggs", "price": 160, "unit": "dozen",
         "description": "Cage-free brown eggs from pasture-raised hens.",
         "is_popular": True, "is_organic": True,
         "image": "https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=800&q=80"},
        {"name": "Paneer", "price": 180, "unit": "g", "weight": 250, "weight_unit": "g",
         "description": "Soft, fresh paneer made from whole milk.",
         "image": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=800&q=80"},
    ],
    "Bakery": [
        {"name": "Sourdough Loaf", "price": 180, "unit": "pcs",
         "description": "Artisan sourdough with a crisp crust and tangy crumb.",
         "is_popular": True,
         "image": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=800&q=80"},
        {"name": "Butter Croissants", "price": 60, "unit": "pcs",
         "description": "Flaky, buttery croissants baked fresh every morning.",
         "is_popular": True,
         "image": "https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=800&q=80"},
        {"name": "Everything Bagels", "price": 45, "unit": "pcs",
         "description": "Chewy bagels topped with sesame, poppy seeds and garlic.",
         "image": "https://images.unsplash.com/photo-1612203985729-70726954388c?w=800&q=80"},
        {"name": "Blueberry Muffins", "price": 55, "unit": "pcs",
         "description": "Soft muffins packed with juicy blueberries.",
         "image": "https://images.unsplash.com/photo-1607958996333-41aef7caefaa?w=800&q=80"},
        {"name": "Glazed Donuts", "price": 40, "unit": "pcs",
         "description": "Light, fluffy donuts with a classic sweet glaze.",
         "image": "https://images.unsplash.com/photo-1551024601-bec78aea704b?w=800&q=80"},
        {"name": "Whole Wheat Bread", "price": 90, "unit": "pcs",
         "description": "Hearty whole wheat sandwich loaf, sliced.",
         "is_organic": True,
         "image": "https://images.unsplash.com/photo-1549931319-a545dcf3bc73?w=800&q=80"},
    ],
    "Meat & Seafood": [
        {"name": "Chicken Breast", "price": 320, "unit": "kg",
         "description": "Boneless, skinless chicken breast — lean and tender.",
         "is_popular": True, "is_fresh": True,
         "image": "https://images.unsplash.com/photo-1587593810167-a84920ea0781?w=800&q=80"},
        {"name": "Ground Beef", "price": 520, "unit": "kg",
         "description": "Freshly ground lean beef, 85% lean / 15% fat.",
         "is_fresh": True,
         "image": "https://images.unsplash.com/photo-1588168333986-5078d3ae3976?w=800&q=80"},
        {"name": "Atlantic Salmon Fillet", "price": 780, "unit": "kg",
         "description": "Fresh salmon fillet, rich in omega-3 fatty acids.",
         "is_popular": True, "is_fresh": True,
         "image": "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=800&q=80"},
        {"name": "Jumbo Shrimp", "price": 650, "unit": "kg",
         "description": "Succulent jumbo shrimp, peeled and deveined.",
         "is_fresh": True,
         "image": "https://images.unsplash.com/photo-1565680018434-b513d5e5fd47?w=800&q=80"},
        {"name": "Chicken Wings", "price": 280, "unit": "kg",
         "description": "Party-ready chicken wings — perfect for grilling or frying.",
         "is_fresh": True,
         "image": "https://images.unsplash.com/photo-1527477396000-e27163b481c2?w=800&q=80"},
    ],
    "Beverages": [
        {"name": "Fresh Orange Juice", "price": 180, "unit": "l", "weight": 1, "weight_unit": "l",
         "description": "100% pure orange juice, no added sugar.",
         "is_popular": True,
         "image": "https://images.unsplash.com/photo-1600271886742-f049cd451bba?w=800&q=80"},
        {"name": "Ground Coffee", "price": 450, "unit": "g", "weight": 250, "weight_unit": "g",
         "description": "Medium roast arabica coffee with chocolate and caramel notes.",
         "is_popular": True,
         "image": "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=800&q=80"},
        {"name": "Green Tea Bags", "price": 260, "unit": "pcs",
         "description": "Premium green tea — 50 bags of refreshing goodness.",
         "is_organic": True,
         "image": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=800&q=80"},
        {"name": "Coconut Water", "price": 90, "unit": "l", "weight": 500, "weight_unit": "ml",
         "description": "Naturally hydrating tender coconut water.",
         "image": "https://images.unsplash.com/photo-1580910051074-3eb694886505?w=800&q=80"},
        {"name": "Mineral Water", "price": 40, "unit": "l", "weight": 1, "weight_unit": "l",
         "description": "Pure natural mineral water, sourced from the Himalayas.",
         "image": "https://images.unsplash.com/photo-1543007630-9710e4a00a20?w=800&q=80"},
    ],
    "Snacks": [
        {"name": "Salted Potato Chips", "price": 80, "unit": "g", "weight": 150, "weight_unit": "g",
         "description": "Thin, crispy potato chips with just the right amount of salt.",
         "is_popular": True,
         "image": "https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=800&q=80"},
        {"name": "Dark Chocolate Bar", "price": 150, "unit": "g", "weight": 100, "weight_unit": "g",
         "description": "Rich 70% cocoa dark chocolate — smooth and intense.",
         "is_popular": True,
         "image": "https://images.unsplash.com/photo-1511381939415-e44015466834?w=800&q=80"},
        {"name": "Chocolate Chip Cookies", "price": 180, "unit": "g", "weight": 300, "weight_unit": "g",
         "description": "Classic chewy cookies loaded with chocolate chips.",
         "image": "https://images.unsplash.com/photo-1558961363-fa8fdf82db35?w=800&q=80"},
        {"name": "Mixed Nuts", "price": 380, "unit": "g", "weight": 250, "weight_unit": "g",
         "description": "Roasted mix of almonds, cashews, walnuts and pistachios.",
         "is_organic": True,
         "image": "https://images.unsplash.com/photo-1599599810769-bcde5a160d32?w=800&q=80"},
        {"name": "Butter Popcorn", "price": 70, "unit": "g", "weight": 100, "weight_unit": "g",
         "description": "Light, crunchy movie-style butter popcorn.",
         "image": "https://images.unsplash.com/photo-1578849278619-e73505e9610f?w=800&q=80"},
    ],
    "Pantry Staples": [
        {"name": "Basmati Rice", "price": 220, "unit": "kg", "weight": 5, "weight_unit": "kg",
         "description": "Long grain aromatic basmati rice — perfect for biryanis.",
         "is_popular": True,
         "image": "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=800&q=80"},
        {"name": "Extra Virgin Olive Oil", "price": 620, "unit": "l", "weight": 500, "weight_unit": "ml",
         "description": "Cold-pressed extra virgin olive oil — fruity and peppery.",
         "is_popular": True, "is_organic": True,
         "image": "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=800&q=80"},
        {"name": "Durum Wheat Pasta", "price": 140, "unit": "g", "weight": 500, "weight_unit": "g",
         "description": "Authentic Italian pasta made from 100% durum wheat.",
         "image": "https://images.unsplash.com/photo-1551462147-ff29053bfc14?w=800&q=80"},
        {"name": "Raw Forest Honey", "price": 320, "unit": "g", "weight": 500, "weight_unit": "g",
         "description": "Pure, unprocessed forest honey from wild beekeepers.",
         "is_organic": True,
         "image": "https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=800&q=80"},
        {"name": "White Sugar", "price": 65, "unit": "kg",
         "description": "Refined white sugar — a baking and beverage essential.",
         "image": "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=800&q=80"},
        {"name": "Sea Salt", "price": 55, "unit": "g", "weight": 500, "weight_unit": "g",
         "description": "Natural coarse sea salt — enhances every dish.",
         "image": "https://images.unsplash.com/photo-1472476443507-c7a5948772fc?w=800&q=80"},
    ],
}


def download_image(url: str, timeout: int = 15) -> bytes | None:
    """Download image bytes from a URL. Returns None on failure."""
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (grocery-seed-script)"})
        with urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except (HTTPError, URLError, TimeoutError, Exception):
        return None


def unique_slug(model, base: str) -> str:
    """Generate a slug unique within the given model."""
    slug = slugify(base) or "item"
    candidate = slug
    i = 2
    while model.objects.filter(slug=candidate).exists():
        candidate = f"{slug}-{i}"
        i += 1
    return candidate


class Command(BaseCommand):
    help = "Seed the database with realistic grocery categories and products (with real images)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fresh",
            action="store_true",
            help="Delete all existing categories and products before seeding.",
        )
        parser.add_argument(
            "--skip-images",
            action="store_true",
            help="Create records without downloading images (useful when offline).",
        )

    def handle(self, *args, **options):
        fresh = options["fresh"]
        skip_images = options["skip_images"]

        if fresh:
            self.stdout.write(self.style.WARNING("Deleting existing products and categories..."))
            Product.objects.all().delete()
            Category.objects.all().delete()

        cat_objs = {}
        for cat_data in CATEGORIES:
            cat_objs[cat_data["name"]] = self._create_category(cat_data, skip_images)

        total_products = 0
        for cat_name, items in PRODUCTS.items():
            category = cat_objs.get(cat_name)
            if not category:
                continue
            for item in items:
                if self._create_product(category, item, skip_images):
                    total_products += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Categories: {len(cat_objs)}, products processed: {total_products}."
            )
        )

    def _create_category(self, data: dict, skip_images: bool) -> Category:
        name = data["name"]
        slug = slugify(name)
        category, created = Category.objects.get_or_create(
            slug=slug,
            defaults={
                "name": name,
                "description": data.get("description", ""),
                "is_active": True,
            },
        )

        if not created:
            category.name = name
            category.description = data.get("description", "")
            category.is_active = True

        needs_image = not category.image or not self._image_exists(category.image)
        if needs_image and not skip_images:
            img_bytes = download_image(data["image"])
            if img_bytes:
                filename = f"{slug}.jpg"
                category.image.save(filename, ContentFile(img_bytes), save=False)
                self.stdout.write(f"  [category] {name} — image saved ({len(img_bytes)} bytes)")
            else:
                self.stdout.write(self.style.WARNING(f"  [category] {name} — image download failed"))

        category.save()
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created category: {name}"))
        else:
            self.stdout.write(f"Updated category: {name}")
        return category

    def _create_product(self, category: Category, data: dict, skip_images: bool) -> bool:
        name = data["name"]
        base_slug = slugify(f"{name}-{category.slug}")
        existing = Product.objects.filter(name=name, category=category).first()

        if existing:
            product = existing
            created = False
        else:
            product = Product(
                name=name,
                slug=unique_slug(Product, base_slug),
                category=category,
            )
            created = True

        product.description = data.get("description", "")
        product.price = data["price"]
        if data.get("original_price"):
            product.original_price = data["original_price"]
        product.unit = data.get("unit", "kg")
        if data.get("weight"):
            product.weight = data["weight"]
        if data.get("weight_unit"):
            product.weight_unit = data["weight_unit"]
        product.stock = data.get("stock", 50)
        product.is_available = True
        product.is_popular = data.get("is_popular", False)
        product.is_organic = data.get("is_organic", False)
        product.is_fresh = data.get("is_fresh", False)

        needs_image = not product.image or not self._image_exists(product.image)
        if needs_image and not skip_images and data.get("image"):
            img_bytes = download_image(data["image"])
            if img_bytes:
                filename = f"{slugify(name)}.jpg"
                product.image.save(filename, ContentFile(img_bytes), save=False)
                self.stdout.write(f"  [product] {name} — image saved ({len(img_bytes)} bytes)")
            else:
                self.stdout.write(self.style.WARNING(f"  [product] {name} — image download failed"))
            time.sleep(0.15)

        product.save()
        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"  {action} product: {name} (₹{product.price}/{product.unit})"))
        return True

    @staticmethod
    def _image_exists(image_field) -> bool:
        try:
            path = image_field.path
        except Exception:
            return False
        return os.path.isfile(path)
