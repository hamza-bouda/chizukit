
from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Cart, CartItem, Order, OrderItem, Review
from django.conf import settings
import stripe
import logging
from django.http import JsonResponse
from django.core.mail import EmailMessage
from .forms import OrderForm, UserRegisterForm, UserLoginForm, ReviewForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.utils.crypto import get_random_string
from django.core.files.storage import FileSystemStorage
from decimal import Decimal
import requests
from requests.auth import HTTPBasicAuth
from django.contrib import messages
from django.urls import reverse
from django.core.files.storage import FileSystemStorage
from django.core.mail import EmailMessage

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import UserRegisterForm, UserLoginForm, ReviewForm
from .models import Product, Review

stripe.api_key = settings.STRIPE_SECRET_KEY

logging.basicConfig(level=logging.DEBUG)

def index(request):
    products = Product.objects.all()
    cart_item_count = get_cart_item_count(request)
    return render(request, 'store/index.html', {'products': products, 'cart_item_count': cart_item_count})

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:5]
    cart_item_count = get_cart_item_count(request)
    reviews = product.reviews.all()
    form = ReviewForm()
    rating_range = range(1, 6)
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'You must be logged in to leave a review'}, status=403)
        
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            return JsonResponse({
                'user': review.user.username,
                'comment': review.comment,
                'rating': review.rating,
                'created_at': review.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
    
    context = {
        'product': product,
        'cart_item_count': cart_item_count,
        'related_products': related_products,
        'reviews': reviews,
        'form': form,
        'rating_range': rating_range,
    }
    return render(request, 'store/product_detail.html', context)


def all_jerseys(request):
    products = Product.objects.all()
    cart_item_count = get_cart_item_count(request)
    return render(request, 'store/index.html', {'products': products, 'cart_item_count': cart_item_count})

def icon_jerseys(request):
    products = Product.objects.filter(is_iconic=True)
    cart_item_count = get_cart_item_count(request)
    return render(request, 'store/index.html', {'products': products, 'cart_item_count': cart_item_count})

def new_jerseys(request):
    products = Product.objects.filter(is_new=True)
    cart_item_count = get_cart_item_count(request)
    return render(request, 'store/index.html', {'products': products, 'cart_item_count': cart_item_count})

def search_jerseys(request):
    query = request.GET.get('q')
    products = Product.objects.filter(name__icontains=query)
    cart_item_count = get_cart_item_count(request)
    return render(request, 'store/index.html', {'products': products, 'cart_item_count': cart_item_count})

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_cart(request)
    
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not created:
        # Si l'article existe déjà, ne rien faire
        pass

    items = cart.items.all()
    total = sum(item.product.price for item in items)
    cart_item_count = items.count()

    return render(request,'store/cart_partial.html', {
        'items': items,
        'total': total,
        'cart_item_count': cart_item_count
    })


def get_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart



def cart(request):
    cart = get_cart(request)
    items = cart.items.all()
    total = sum(item.product.price for item in items)
    cart_item_count = cart.items.count()
    return render(request, 'store/cart.html', {'cart': cart, 'items': items, 'total': total, 'cart_item_count': cart_item_count})

def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart=get_cart(request))
    cart_item.delete()
    return redirect('cart')

def place_order(request):
    cart = get_cart(request)  # Récupérer le panier
    cart_items = cart.items.all()
    total_amount = sum(item.product.price for item in cart_items)

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
                telephone=form.cleaned_data['telephone'],
                address=form.cleaned_data['street_address'],
                city=form.cleaned_data['city'],
                postal_code=form.cleaned_data['postal_code'],
                country=form.cleaned_data['country'],
                total_amount=total_amount
            )

            # Créer des OrderItem pour chaque article dans le panier
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    price=cart_item.product.price,
                )

            # Réinitialisation du panier
            cart.items.all().delete()
            
            return redirect('payment_page', order_id=order.id)
    else:
        form = OrderForm()

    shipping = Decimal('45.00')  # Exemple de frais de port fixe
    tax = Decimal('0.95')  # Exemple de taxe fixe
    grand_total = total_amount + shipping + tax

    context = {
        'form': form,
        'cart_items': cart_items,
        'total_amount': total_amount,
        'shipping': shipping,
        'tax': tax,
        'grand_total': grand_total
    }

    return render(request, 'store/place_order.html', context)

from django.core.mail import send_mail

def process_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    error_message = None
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        if payment_method == 'paypal':
            return redirect('create_payment', order_id=order.id)
        elif payment_method == 'cod':
            if 'bank_transfer_image' in request.FILES:
                image = request.FILES['bank_transfer_image']
                fs = FileSystemStorage()
                filename = fs.save(image.name, image)
                order.bank_transfer_image = filename
                order.save()

                # Envoyer un email de confirmation
                send_order_confirmation_email(order)

                return redirect('order_success')
            else:
               error_message = "Veuillez télécharger une preuve de virement."
    context = {
        'order': order,
        'cart_items': order.items.all(),
        'total_amount': order.get_total(),
        'shipping': order.get_shipping_cost(),
        'tax': order.get_tax(),
        'grand_total': order.get_grand_total(),
        'error_message': error_message,
    }
    return render(request, 'store/payment_page.html', context)

def send_order_confirmation_email(order):
    # Préparation du contenu de l'email
    subject = 'Nouvelle commande de {}'.format(order.first_name + " " + order.last_name)
    message = 'Détails de la commande :\n\n'
    message += 'Nom complet: {}\n'.format(order.first_name + " " + order.last_name)
    message += 'Email: {}\n'.format(order.email)
    message += 'Téléphone: {}\n'.format(order.telephone)
    message += 'Adresse: {}\n'.format(order.address)
    message += 'Ville: {}\n'.format(order.city)
    message += 'Code postal: {}\n'.format(order.postal_code)
    message += 'Pays: {}\n'.format(order.country)
    message += '\nProduits commandés:\n'
    for item in order.items.all():
        message += 'Produit: {}\n'.format(item.product.name)
        message += 'Prix unitaire: {} DH\n'.format(item.price)
    message += 'Total: {} DH\n\n'.format(order.get_grand_total())

    # Envoi de l'email
    email = EmailMessage(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [settings.DEFAULT_FROM_EMAIL],
    )
    if order.bank_transfer_image:
        fs = FileSystemStorage()
        file_path = fs.path(order.bank_transfer_image.name)
        email.attach_file(file_path)

    email.send(fail_silently=False)


def payment_page(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        if payment_method == 'paypal':
            return redirect('create_payment', order_id=order.id)
        elif payment_method == 'cod':
            # Logique pour Cash on Delivery (COD)
            return redirect('order_success')
    context = {
        'order': order,
        'cart_items': order.items.all(),
        'total_amount': order.get_total(),
        'shipping': order.get_shipping_cost(),
        'tax': order.get_tax(),
        'grand_total': order.get_grand_total(),
    }
    return render(request, 'store/payment_page.html', context)

def order_success(request):
    return render(request, 'store/order_success.html')

def get_cart_item_count(request):
    cart = request.session.get('cart', {})
    return sum(cart.values())




def account(request):
    login_form = UserLoginForm()
    register_form = UserRegisterForm()

    if request.method == 'POST':
        if 'username' in request.POST and 'password1' in request.POST:
            register_form = UserRegisterForm(request.POST)
            if register_form.is_valid():
                user = register_form.save()
                login(request, user)
                return redirect('index')
            else:
                messages.error(request, 'Error creating account. Please check the details and try again.')
                logging.debug(f"Register form errors: {register_form.errors}")

        elif 'username' in request.POST and 'password' in request.POST:
            login_form = UserLoginForm(request, data=request.POST)
            if login_form.is_valid():
                user = login_form.get_user()
                login(request, user)
                return redirect('index')
            else:
                messages.error(request, 'Invalid login credentials.')
                logging.debug(f"Login form errors: {login_form.errors}")

    return render(request, 'store/account.html', {
        'login_form': login_form,
        'register_form': register_form
    })






from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Review
from .forms import ReviewForm

from django.contrib.auth.decorators import login_required

@login_required
def add_review(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'You must be logged in to leave a review'}, status=403)
    
    if request.user.is_superuser:
        return JsonResponse({'error': 'Superusers are not allowed to leave reviews'}, status=403)
    
    product = get_object_or_404(Product, id=product_id)
    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.product = product
        review.user = request.user
        review.save()
        return JsonResponse({
            'user': review.user.username,
            'comment': review.comment,
            'rating': review.rating,
            'created_at': review.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    else:
        return JsonResponse({'error': form.errors}, status=400)


def user_logout(request):
    logout(request)
    return redirect('index')

#_____________________paypal________________________________________________
import paypalrestsdk
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from .models import Order, OrderItem, Product, Cart, CartItem
from django.urls import reverse
import logging
import requests
from decimal import Decimal
import json
from requests.auth import HTTPBasicAuth


def get_exchange_rate(from_currency, to_currency):
    url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
    response = requests.get(url)
    rates = response.json().get("rates", {})
    return rates.get(to_currency, 1)


# Configure the logger
logging.basicConfig(level=logging.DEBUG)

# PayPal Configuration
paypalrestsdk.configure({
  "mode": "sandbox",  # change to "live" for production
  "client_id": settings.PAYPAL_CLIENT_ID,
  "client_secret": settings.PAYPAL_CLIENT_SECRET
})


def get_access_token():
    url = "https://api.sandbox.paypal.com/v1/oauth2/token"
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US"
    }
    data = {
        "grant_type": "client_credentials"
    }
    response = requests.post(url, headers=headers, data=data, auth=HTTPBasicAuth(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET))
    return response.json()['access_token']

def create_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Convert MAD to EUR for PayPal
    exchange_rate = Decimal(get_exchange_rate('MAD', 'EUR'))
    total_amount_eur = order.total_amount * exchange_rate
    total_amount_eur = total_amount_eur.quantize(Decimal('0.01'))  # Round to 2 decimal places

    access_token = get_access_token()
    url = "https://api.sandbox.paypal.com/v1/payments/payment"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    payload = {
        "intent": "sale",
        "redirect_urls": {
            "return_url": f"http://localhost:8000{reverse('execute_payment')}",
            "cancel_url": f"http://localhost:8000{reverse('payment_cancelled')}"
        },
        "payer": {
            "payment_method": "paypal"
        },
        "transactions": [{
            "amount": {
                "total": str(total_amount_eur),
                "currency": "EUR"  # Use EUR for the transaction
            },
            "description": f"Order ID: {order.id}",
            "item_list": {
                "items": [{
                    "name": f"Order {order.id}",
                    "sku": "item",
                    "price": str(total_amount_eur),
                    "currency": "EUR",  # Use EUR for the transaction
                    "quantity": 1
                }]
            }
        }]
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.status_code == 201:
        payment = response.json()
        for link in payment['links']:
            if (link['rel'] == 'approval_url'):
                approval_url = link['href']
                return redirect(approval_url)
    else:
        return render(request, 'store/payment_error.html', {'error': response.json()})

def execute_payment(request):
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')

    payment = paypalrestsdk.Payment.find(payment_id)

    if payment.execute({"payer_id": payer_id}):
        order = get_object_or_404(Order, id=payment.transactions[0].item_list.items[0].name.split()[-1])
        send_order_confirmation_email(order)
        return render(request, 'store/order_success.html', {'payment': payment})
    else:
        return render(request, 'store/payment_error.html', {'error': payment.error})

def payment_cancelled(request):
    return render(request, 'store/payment_cancelled.html')
