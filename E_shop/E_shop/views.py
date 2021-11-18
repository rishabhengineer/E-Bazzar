from django.shortcuts import render,redirect,HttpResponse
from app.models import Category, Product, Contact_us, Order, Brand

from django.contrib.auth import authenticate,login
from app.models import UserCreateForm
from django.contrib.auth.models import User

#add to cart
from django.contrib.auth.decorators import login_required
from cart.cart import Cart
import razorpay
from E_shop.settings import RAZORPAY_API_KEY, RAZORPAY_API_SECRET_KEY


def Master(request):
    return render(request,'master.html')

def Index(request):
    category = Category.objects.all()
    brand = Brand.objects.all()
    categoryID=request.GET.get('category')
    brandID=request.GET.get('brand')
    if categoryID:
        product = Product.objects.filter(sub_category=categoryID).order_by('-id')
    elif brandID:
        product = Product.objects.filter(brand=brandID).order_by('-id')
    else:
        product = Product.objects.all()

    context = {
        'category':category,
        'product':product,
        'brand':brand,
    }
    return render(request,'index.html',context)

def signup(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            new_user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1']
            )
            login(request,new_user)
            return redirect('index')
    else:
        form=UserCreateForm()

    context={
        'form':form,
    }
    return render(request,'registration/signup.html',context)


#add to cart
@login_required(login_url="/accounts/login/")
def cart_add(request, id):
    cart = Cart(request)
    product = Product.objects.get(id=id)
    cart.add(product=product)
    return redirect("index")


@login_required(login_url="/accounts/login/")
def item_clear(request, id):
    cart = Cart(request)
    product = Product.objects.get(id=id)
    cart.remove(product)
    return redirect("cart_detail")


@login_required(login_url="/accounts/login/")
def item_increment(request, id):
    cart = Cart(request)
    product = Product.objects.get(id=id)
    cart.add(product=product)
    return redirect("cart_detail")


@login_required(login_url="/accounts/login/")
def item_decrement(request, id):
    cart = Cart(request)
    product = Product.objects.get(id=id)
    cart.decrement(product=product)
    return redirect("cart_detail")


@login_required(login_url="/accounts/login/")
def cart_clear(request):
    cart = Cart(request)
    cart.clear()
    return redirect("cart_detail")


@login_required(login_url="/accounts/login/")
def cart_detail(request):
    return render(request, 'cart/cart_detail.html')


#contact us
def contact_page(request):
    if request.method == 'POST':
        contact = Contact_us(
            name=request.POST.get('name'),
            email=request.POST.get('email'),
            subject=request.POST.get('subject'),
            message=request.POST.get('message'),
        )
        contact.save()
    return render(request,'contact.html')

#checkout
client = razorpay.Client(auth=(RAZORPAY_API_KEY, RAZORPAY_API_SECRET_KEY))
def Checkout(request):
    if request.method == 'POST':
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        pincode = request.POST.get('pincode')
        cart = request.session.get('cart')
        uid = request.session.get('_auth_user_id')
        user = User.objects.get(pk = uid)

        request.session['address'] = address,
        request.session['phone'] = phone,
        request.session['pincode'] = pincode,


        for i in cart:
            a=int(cart[i]['price'])
            b=cart[i]['quantity']
            total=a*b

        payment_order = client.order.create(dict(amount=total*100,currency="INR",payment_capture=1))
        order_id = payment_order['id']

        request.session['order_id'] = order_id

        context = {
            "address": address,
            "phone": phone,
            "pincode": pincode,
            "cart": cart,
            "uid": uid,
            "user": user,
            "amount":total,
            "api_key":RAZORPAY_API_KEY,
            "order_id":order_id
        }
        return render(request,'payment_view/payment.html',context)
    return HttpResponse('this is checkout page')

#order
def Your_order(request):
    uid = request.session.get('_auth_user_id')
    user = User.objects.get(pk=uid)

    order = Order.objects.filter(user = user)
    print(user,order)
    context = {
        'order':order,
    }
    return render(request,'order.html',context)


#product page
def Product_Page(request):
    category = Category.objects.all()
    brand = Brand.objects.all()
    categoryID = request.GET.get('category')
    brandID = request.GET.get('brand')
    if categoryID:
        product = Product.objects.filter(sub_category=categoryID).order_by('-id')
    elif brandID:
        product = Product.objects.filter(brand=brandID).order_by('-id')
    else:
        product = Product.objects.all()

    context = {
        'category': category,
        'product': product,
        'brand': brand,
    }
    return render(request,'product_page.html',context)


#product details
def Product_Details(request,id):
    product_id = Product.objects.filter(id = id).first()
    context = {
        'product_id':product_id,
    }
    return render(request,'product_details.html',context)

#search
def Search(request):
    query = request.GET['query']
    product=Product.objects.filter(name__icontains = query)
    context={
        'product':product
    }
    return render(request,'search.html',context)

#payment
def payment(request):
    """order = Order(
        user=user,
        product=cart[i]['name'],
        price=cart[i]['price'],
        quantity=cart[i]['quantity'],
        image=cart[i]['image'],
        address=address,
        phone=phone,
        pincode=pincode,
        total=total,
    )"""
    request.session['cart'] = {}
    return render(request,'payment_view/payment.html')

#payment_success
def payment_success(request):
    address = request.session.get('address')
    order_id = request.session.get('order_id')
    phone = request.session.get('phone')
    pincode = request.session.get('pincode')
    cart = request.session.get('cart')
    uid = request.session.get('_auth_user_id')
    user = User.objects.get(pk=uid)

    for i in cart:
        a = int(cart[i]['price'])
        b = cart[i]['quantity']
        total = a * b

    payment_id = request.POST.get('razorpay_payment_id', '')
    order = Order(
        user = user,
        product=cart[i]['name'],
        price=cart[i]['price'],
        quantity=cart[i]['quantity'],
        image=cart[i]['image'],
        address = address,
        phone = phone,
        pincode = pincode,
        order_id = order_id,
        total=total,
    )
    order.save()
    request.session['cart'] = {}
    return render(request,'payment_view/payment_success.html')





