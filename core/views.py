
from django.shortcuts import get_object_or_404, render

from .models import Product


from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from decimal import Decimal

from django.shortcuts import get_object_or_404, redirect, render

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.views.decorators.http import require_http_methods
from .models import Product, Order, OrderItem


def home(request):
    return render(request, "core/home.html")


def product_list(request):
    products = Product.objects.filter(
        is_available=True,
        stock__gt=0,
    )
    return render(
        request,
        "core/product_list.html",
        {"products": products},
    )


def product_detail(request, pk):
    product = get_object_or_404(
        Product,
        pk=pk,
        is_available=True,
        stock__gt=0,
    )
    return render(
        request,
        "core/product_detail.html",
        {"product": product},
    )




def register(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = UserCreationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Registration successful.")
        return redirect("home")

    return render(request, "core/register.html", {"form": form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        messages.success(request, "You are now logged in.")
        return redirect("home")

    return render(request, "core/login.html", {"form": form})


@require_POST
def user_logout(request):
    logout(request)
    messages.success(request, "You have logged out.")
    return redirect("home")




def _get_cart(request):
    return request.session.get("cart", {})


def cart_detail(request):
    cart = _get_cart(request)
    items = []
    total = Decimal("0.00")

    for product_id, quantity in cart.items():
        try:
            quantity = int(quantity)
            if quantity < 1 or quantity > 100:
                continue
            product = Product.objects.get(
                pk=int(product_id),
                is_available=True,
                stock__gt=0,
            )
        except (Product.DoesNotExist, ValueError, TypeError):
            continue

        quantity = min(quantity, product.stock)
        subtotal = product.price * quantity
        total += subtotal
        items.append({
            "product": product,
            "quantity": quantity,
            "subtotal": subtotal,
        })

    return render(
        request,
        "core/cart.html",
        {"items": items, "total": total},
    )


@require_POST
def cart_add(request, pk):
    product = get_object_or_404(
        Product, pk=pk, is_available=True, stock__gt=0
    )
    try:
        quantity = int(request.POST.get("quantity", 1))
    except (ValueError, TypeError):
        messages.error(request, "Invalid quantity.")
        return redirect("product_detail", pk=pk)

    if not 1 <= quantity <= 100:
        messages.error(request, "Quantity must be between 1 and 100.")
        return redirect("product_detail", pk=pk)

    cart = _get_cart(request).copy()
    new_quantity = cart.get(str(pk), 0) + quantity

    if new_quantity > min(product.stock, 100):
        messages.error(request, "Requested quantity exceeds available stock.")
        return redirect("product_detail", pk=pk)

    cart[str(pk)] = new_quantity
    request.session["cart"] = cart
    messages.success(request, "Product added to cart.")
    return redirect("cart_detail")


@require_POST
def cart_update(request, pk):
    cart = _get_cart(request).copy()

    if str(pk) not in cart:
        return redirect("cart_detail")

    product = get_object_or_404(Product, pk=pk)

    try:
        quantity = int(request.POST.get("quantity", 0))
    except (ValueError, TypeError):
        quantity = 0

    if quantity == 0:
        cart.pop(str(pk))
    elif (
        1 <= quantity <= 100
        and product.is_available
        and quantity <= product.stock
    ):
        cart[str(pk)] = quantity
    else:
        messages.error(request, "Invalid quantity or insufficient stock.")

    request.session["cart"] = cart
    return redirect("cart_detail")


@require_POST
def cart_remove(request, pk):
    cart = _get_cart(request).copy()
    cart.pop(str(pk), None)
    request.session["cart"] = cart
    messages.success(request, "Item removed from cart.")
    return redirect("cart_detail")


@login_required
@require_http_methods(["GET", "POST"])
def checkout(request):
    cart = request.session.get("cart", {})

    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect("cart_detail")

    if request.method == "GET":
        items = []
        total = 0

        for product_id, quantity in cart.items():
            try:
                product = Product.objects.get(
                    pk=int(product_id),
                    is_available=True,
                    stock__gt=0,
                )
                quantity = int(quantity)

                if not 1 <= quantity <= min(product.stock, 100):
                    raise ValueError

            except (Product.DoesNotExist, ValueError, TypeError):
                messages.error(
                    request,
                    "Your cart has invalid items or quantities. Please review it.",
                )
                return redirect("cart_detail")

            subtotal = product.price * quantity
            total += subtotal
            items.append({
                "product": product,
                "quantity": quantity,
                "subtotal": subtotal,
            })

        return render(
            request,
            "core/checkout.html",
            {"items": items, "total": total},
        )

    with transaction.atomic():
        product_ids = []

        try:
            for product_id, quantity in cart.items():
                product_ids.append(int(product_id))
                quantity = int(quantity)

                if not 1 <= quantity <= 100:
                    raise ValueError
        except (ValueError, TypeError):
            messages.error(request, "Invalid cart. Please review it.")
            return redirect("cart_detail")

        products = {
            product.pk: product
            for product in Product.objects.select_for_update().filter(
                pk__in=product_ids
            )
        }

        if len(products) != len(set(product_ids)):
            messages.error(request, "A product no longer exists.")
            return redirect("cart_detail")

        for product_id, quantity in cart.items():
            product = products[int(product_id)]
            quantity = int(quantity)

            if not product.is_available or quantity > product.stock:
                messages.error(
                    request,
                    f"Insufficient stock for {product.name}. Please review your cart.",
                )
                return redirect("cart_detail")

        order = Order.objects.create(customer=request.user)

        for product_id, quantity in cart.items():
            product = products[int(product_id)]
            quantity = int(quantity)

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                unit_price=product.price,
            )

            product.stock -= quantity
            product.save(update_fields=["stock"])

    request.session["cart"] = {}
    messages.success(request, f"Order #{order.pk} placed successfully.")
    return redirect("home")

@login_required
def order_history(request):
    orders = Order.objects.filter(
        customer=request.user
    ).prefetch_related("items__product")

    return render(
        request,
        "core/order_history.html",
        {"orders": orders},
    )


@login_required
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.prefetch_related("items__product"),
        pk=pk,
        customer=request.user,
    )

    return render(
        request,
        "core/order_detail.html",
        {"order": order},
    )