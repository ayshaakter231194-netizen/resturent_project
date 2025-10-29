from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import JsonResponse
from .models import Category, FoodItem, Customer, Order, OrderItem
from .forms import CheckoutForm
from decimal import Decimal

DELIVERY_FEE_INSIDE = Decimal('60.00')
DELIVERY_FEE_OUTSIDE = Decimal('120.00')

def menu_view(request):
    categories = Category.objects.all()
    category_slug = request.GET.get('category')
    foods = FoodItem.objects.filter(is_available=True).select_related('category')
    
    # Get 3-5 featured foods for the slideshow (you can customize this logic)
    featured_foods = FoodItem.objects.filter(is_available=True, image__isnull=False).order_by('?')[:5]
    
    if category_slug:
        foods = foods.filter(category__slug=category_slug)
        # Try to get the active category for display
        active_category = categories.filter(slug=category_slug).first()
    else:
        active_category = None
        
    return render(request, 'menu/menu.html', {
        'categories': categories, 
        'foods': foods, 
        'active_slug': category_slug,
        'active_category': active_category,
        'featured_foods': featured_foods
    })

# Cart is stored in session: {'cart': {food_id: {'name':..., 'price': 'x.xx', 'qty': n}}}
def add_to_cart(request, food_id):
    food = get_object_or_404(FoodItem, id=food_id, is_available=True)
    cart = request.session.get('cart', {})
    item = cart.get(str(food_id), {'name': food.name, 'price': str(food.price), 'qty': 0})
    item['qty'] = item.get('qty', 0) + 1
    cart[str(food_id)] = item
    request.session['cart'] = cart
    return redirect('menu:cart')

def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    subtotal = Decimal('0.00')
    for fid, data in cart.items():
        qty = int(data['qty'])
        price = Decimal(data['price'])
        total = price * qty
        subtotal += total
        cart_items.append({'food_id': fid, 'name': data['name'], 'price': price, 'qty': qty, 'total': total})
    return render(request, 'menu/cart.html', {'cart_items': cart_items, 'subtotal': subtotal})

def update_cart(request):
    # expects POST with food_id and qty
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        for key, val in request.POST.items():
            if key.startswith('qty_'):
                fid = key.split('_',1)[1]
                try:
                    qty = int(val)
                    if qty <= 0:
                        cart.pop(fid, None)
                    else:
                        if fid in cart:
                            cart[fid]['qty'] = qty
                except:
                    pass
        request.session['cart'] = cart
    return redirect('menu:cart')

def checkout_view(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('menu:menu')
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        inside_choice = request.POST.get('inside_dhaka') == 'yes'
        if form.is_valid():
            customer = form.save()
            subtotal = Decimal('0.00')
            for fid, data in cart.items():
                subtotal += Decimal(data['price']) * int(data['qty'])
            delivery_fee = DELIVERY_FEE_INSIDE if inside_choice else DELIVERY_FEE_OUTSIDE
            total = subtotal + delivery_fee
            order = Order.objects.create(
                customer=customer,
                total=total,
                delivery_fee=delivery_fee,
                inside_dhaka=inside_choice,
                payment_method='COD',
            )
            for fid, data in cart.items():
                food = FoodItem.objects.get(id=fid)
                OrderItem.objects.create(
                    order=order,
                    food=food,
                    quantity=int(data['qty']),
                    price_at_order=Decimal(data['price'])
                )
            # clear cart
            request.session['cart'] = {}
            return render(request, 'menu/order_success.html', {'order': order})
    else:
        form = CheckoutForm()
    # calculate subtotal for display
    subtotal = Decimal('0.00')
    cart_items = []
    for fid, data in cart.items():
        qty = int(data['qty'])
        price = Decimal(data['price'])
        total = price * qty
        subtotal += total
        cart_items.append({'name': data['name'], 'price': price, 'qty': qty, 'total': total})
    return render(request, 'menu/checkout.html', {'form': form, 'cart_items': cart_items, 'subtotal': subtotal})

def remove_from_cart(request, food_id):
    cart = request.session.get('cart', {})
    cart.pop(str(food_id), None)
    request.session['cart'] = cart
    return redirect('menu:cart')
