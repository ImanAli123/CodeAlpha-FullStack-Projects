from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .models import Product, Order, OrderItem


def home(request):
    products = Product.objects.all().order_by('-created_at')
    return render(request, 'store/home.html', {'products': products})


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'store/product_detail.html', {
        'product': product
    })


def get_cart(request):
    return request.session.get('cart', {})


@require_POST
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    cart = get_cart(request)
    key = str(product.pk)
    quantity = int(cart.get(key, 0))

    if product.stock < 1:
        messages.error(request, 'This product is out of stock.')
    elif quantity >= product.stock:
        messages.error(request, 'Available stock limit reached.')
    else:
        cart[key] = quantity + 1
        request.session['cart'] = cart
        messages.success(request, 'Product added to cart.')

    return redirect('cart')


def cart_view(request):
    cart = get_cart(request)
    items = []
    total = Decimal('0.00')

    for product_id, quantity in cart.items():
        product = Product.objects.filter(pk=product_id).first()
        if product and quantity > 0:
            subtotal = product.price * quantity
            items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal,
            })
            total += subtotal

    return render(request, 'store/cart.html', {
        'items': items,
        'total': total,
    })


@require_POST
def remove_from_cart(request, pk):
    cart = get_cart(request)
    cart.pop(str(pk), None)
    request.session['cart'] = cart
    return redirect('cart')


@login_required
def checkout(request):
    cart = get_cart(request)
    items = []
    total = Decimal('0.00')

    for product_id, quantity in cart.items():
        product = Product.objects.filter(pk=product_id).first()
        if product and quantity > 0:
            items.append((product, quantity))
            total += product.price * quantity

    if not items:
        messages.error(request, 'Your cart is empty.')
        return redirect('home')

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()

        if not full_name or not address or not phone:
            messages.error(request, 'Please complete all checkout fields.')
            return redirect('checkout')

        with transaction.atomic():
            # Lock product rows and recheck stock at checkout.
            product_ids = [p.pk for p, _ in items]
            locked = {
                p.pk: p for p in Product.objects.select_for_update()
                .filter(pk__in=product_ids).order_by('pk')
            }

            for product, quantity in items:
                current = locked.get(product.pk)
                if current is None or current.stock < quantity:
                    messages.error(
                        request,
                        f'Insufficient stock for {product.name}.'
                    )
                    return redirect('cart')

            order = Order.objects.create(
                user=request.user,
                full_name=full_name,
                address=address,
                phone=phone,
                total_amount=total,
            )

            for product, quantity in items:
                current = locked[product.pk]
                OrderItem.objects.create(
                    order=order,
                    product=current,
                    quantity=quantity,
                    price=current.price,
                )
                current.stock -= quantity
                current.save(update_fields=['stock'])

        request.session['cart'] = {}
        return redirect('order_success', pk=order.pk)

    return render(request, 'store/checkout.html', {
        'items': items,
        'total': total,
    })


@login_required
def order_success(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, 'store/order_success.html', {'order': order})

    from django.contrib.auth.forms import UserCreationForm


def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = UserCreationForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Account created. Please log in.')
        return redirect('login')

    return render(request, 'registration/register.html', {
        'form': form
    })