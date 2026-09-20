from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.timezone import now
from django.http import JsonResponse
from django.db import models
import random
from .models import User, Stock, Distribution, OTP, FamilyMember, Notification
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings


def login_view(request):
    if request.method == "POST":
        mobile = request.POST.get('username')
        password = request.POST.get('password')
        user = User.objects.filter(mobile=mobile, password=password).first()
        if user:
            request.session['user_id'] = user.id
            request.session['role'] = user.role
            if user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'shopkeeper':
                return redirect('shop_dashboard')
            else:
                return redirect('user_dashboard')
        else:
            messages.error(request, "Invalid login")
    return render(request, 'login.html')


def admin_dashboard(request):
    search = request.GET.get('search')
    if search:
        users = User.objects.filter(name__icontains=search)
    else:
        users = User.objects.filter(role='user')

    stocks = Stock.objects.all()
    otps   = OTP.objects.select_related('user').order_by('-id')[:10]

    return render(request, 'admin_dashboard.html', {
        'users': users,
        'stocks': stocks,
        'otps': otps,
    })


def shop_dashboard(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    user = User.objects.get(id=user_id)
    if user.role != 'shopkeeper':
        return redirect('login')

    rice  = Stock.objects.filter(item_name='Rice').first()
    wheat = Stock.objects.filter(item_name='Wheat').first()
    sugar = Stock.objects.filter(item_name='Sugar').first()

    rice_qty  = rice.quantity  if rice  else 0
    wheat_qty = wheat.quantity if wheat else 0
    sugar_qty = sugar.quantity if sugar else 0

    if rice_qty  < 5: messages.warning(request, "Rice stock is low ⚠️")
    if wheat_qty < 5: messages.warning(request, "Wheat stock is low ⚠️")
    if sugar_qty < 5: messages.warning(request, "Sugar stock is low ⚠️")

    return render(request, 'shop_dashboard.html', {'rice': rice, 'wheat': wheat, 'sugar': sugar})


def distribute_ration(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    if request.method == 'POST':
        verified_user_id = request.POST.get('user')
        rice  = int(request.POST.get('rice',  0))
        wheat = int(request.POST.get('wheat', 0))
        sugar = int(request.POST.get('sugar', 0))

        user = User.objects.get(id=verified_user_id)

        history = Distribution.objects.filter(
            user=user, date__month=now().month, date__year=now().year
        )
        total_rice  = sum(h.quantity for h in history if h.item_name == 'Rice')
        total_wheat = sum(h.quantity for h in history if h.item_name == 'Wheat')
        total_sugar = sum(h.quantity for h in history if h.item_name == 'Sugar')

        members = max(1, FamilyMember.objects.filter(user=user).count())
        remaining_rice  = (members * 5) - total_rice
        remaining_wheat = (members * 5) - total_wheat
        remaining_sugar = (members * 2) - total_sugar

        errors = []
        if rice  > 0 and rice  > remaining_rice:  errors.append("❌ Rice exceeds monthly limit")
        if wheat > 0 and wheat > remaining_wheat: errors.append("❌ Wheat exceeds monthly limit")
        if sugar > 0 and sugar > remaining_sugar: errors.append("❌ Sugar exceeds monthly limit")

        if errors:
            users = User.objects.filter(role='user')
            return render(request, 'distribute.html', {
                'users': users, 'errors': errors,
                'remaining_rice': remaining_rice,
                'remaining_wheat': remaining_wheat,
                'remaining_sugar': remaining_sugar,
            })

        if rice  > 0:
            Distribution.objects.create(user=user, item_name='Rice',  quantity=rice)
            Stock.objects.filter(item_name='Rice').update(quantity=models.F('quantity') - rice)
        if wheat > 0:
            Distribution.objects.create(user=user, item_name='Wheat', quantity=wheat)
            Stock.objects.filter(item_name='Wheat').update(quantity=models.F('quantity') - wheat)
        if sugar > 0:
            Distribution.objects.create(user=user, item_name='Sugar', quantity=sugar)
            Stock.objects.filter(item_name='Sugar').update(quantity=models.F('quantity') - sugar)

        request.session['receipt'] = {
            'name':  user.name,
            'date':  now().strftime('%d %b %Y, %I:%M %p'),
            'rice':  rice,
            'wheat': wheat,
            'sugar': sugar,
        }

        # Send email receipt to user
        if user.email:
            try:
                send_mail(
                    subject='✅ Ration Distributed - Receipt',
                    message=f"""Dear {user.name},

Your ration has been successfully distributed.

📋 Receipt Details:
━━━━━━━━━━━━━━━━━━━━
📅 Date & Time : {now().strftime('%d %b %Y, %I:%M %p')}
👤 Name        : {user.name}
🌾 Rice        : {rice} kg
🌾 Wheat       : {wheat} kg
🍬 Sugar       : {sugar} kg
━━━━━━━━━━━━━━━━━━━━

Thank you.
- Ration System""",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                )
            except Exception as e:
                print(f'Receipt email error: {e}')

        return redirect('receipt')

    users = User.objects.filter(role='user')
    return render(request, 'distribute.html', {'users': users})


def get_user_allowance(request, user_id):
    user = get_object_or_404(User, id=user_id)
    history = Distribution.objects.filter(
        user=user, date__month=now().month, date__year=now().year
    )
    total_rice  = sum(h.quantity for h in history if h.item_name == 'Rice')
    total_wheat = sum(h.quantity for h in history if h.item_name == 'Wheat')
    total_sugar = sum(h.quantity for h in history if h.item_name == 'Sugar')
    members = max(1, FamilyMember.objects.filter(user=user).count())
    return JsonResponse({
        'remaining_rice':  max(0, members * 5 - total_rice),
        'remaining_wheat': max(0, members * 5 - total_wheat),
        'remaining_sugar': max(0, members * 2 - total_sugar),
    })


def user_history(request):
    distributions = Distribution.objects.all().order_by('-date')
    return render(request, 'user_history.html', {'distributions': distributions})


def send_otp(request):
    users = User.objects.filter(role='user')
    if request.method == "POST":
        user_id = request.POST.get('user')
        user = User.objects.get(id=user_id)
        otp = str(random.randint(1000, 9999))
        OTP.objects.create(user=user, otp=otp)

        email_sent = False
        if user.email:
            try:
                send_mail(
                    subject='Your Ration OTP',
                    message=f'Dear {user.name},\n\nYour OTP for ration collection is: {otp}\n\nDo not share this with anyone.\n\n- Ration System',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                )
                email_sent = True
            except Exception as e:
                print(f'Email error: {e}')

        return render(request, 'send_otp.html', {
            'users': users, 'otp': otp,
            'user_name': user.name, 'user_email': user.email,
            'email_sent': email_sent,
        })
    return render(request, 'send_otp.html', {'users': users})


def verify_otp(request):
    if request.method == "POST":
        entered_otp = request.POST.get('otp')
        try:
            otp_obj = OTP.objects.get(otp=entered_otp, is_verified=False)
            otp_obj.is_verified = True
            otp_obj.save()
            request.session['verified_user_id'] = otp_obj.user.id
            return redirect('distribute_ration')
        except OTP.DoesNotExist:
            return render(request, 'verify_otp.html', {'error': 'Invalid OTP'})
    return render(request, 'verify_otp.html')


def transparency(request):
    user_id = request.session.get('user_id')
    user = User.objects.get(id=user_id) if user_id else None
    records = Distribution.objects.all().order_by('-date')
    return render(request, 'transparency.html', {'records': records, 'user': user})


def delete_record(request, id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    user = User.objects.get(id=user_id)
    if user.role != 'admin':
        return redirect('login')
    record = get_object_or_404(Distribution, id=id)
    record.delete()
    return redirect('transparency')


def user_dashboard(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    user = User.objects.get(id=user_id)

    rice = Stock.objects.filter(item_name='Rice').first()
    message = None
    if rice and rice.available_from:
        if now() < rice.available_from:
            message = f"⏳ Stock updated. Come after {rice.available_from.strftime('%d %b %Y, %I:%M %p')}"
        else:
            message = "✅ Stock available now"

    history = Distribution.objects.filter(
        user=user, date__month=now().month, date__year=now().year
    )
    total_rice  = sum(h.quantity for h in history if h.item_name == 'Rice')
    total_wheat = sum(h.quantity for h in history if h.item_name == 'Wheat')
    total_sugar = sum(h.quantity for h in history if h.item_name == 'Sugar')

    members = FamilyMember.objects.filter(user=user).count()
    family_members = FamilyMember.objects.filter(user=user)
    allowed_members = max(1, members)

    allowed_rice  = allowed_members * 5
    allowed_wheat = allowed_members * 5
    allowed_sugar = allowed_members * 2

    notifications = Notification.objects.filter(
        is_active=True, show_from__lte=now()
    ).order_by('-created_at')[:3]

    return render(request, 'user_dashboard.html', {
        'user': user, 'history': history, 'last': history.first(),
        'members': members, 'family_members': family_members,
        'notifications': notifications,
        'total_rice': total_rice, 'total_wheat': total_wheat, 'total_sugar': total_sugar,
        'allowed_rice': allowed_rice, 'allowed_wheat': allowed_wheat, 'allowed_sugar': allowed_sugar,
        'remaining_rice':  max(0, allowed_rice  - total_rice),
        'remaining_wheat': max(0, allowed_wheat - total_wheat),
        'remaining_sugar': max(0, allowed_sugar - total_sugar),
        'message': message,
    })


def add_user(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    all_users = User.objects.filter(role='user')
    if request.method == 'POST':
        name = request.POST.get('name')
        mobile = request.POST.get('mobile')
        email = request.POST.get('email')
        password = request.POST.get('password')
        ration_card_no = request.POST.get('ration_card_no')
        address = request.POST.get('address')
        if User.objects.filter(mobile=mobile).exists():
            messages.error(request, 'Mobile number already registered ❌')
        elif User.objects.filter(ration_card_no=ration_card_no).exists():
            messages.error(request, 'Ration card number already exists ❌')
        else:
            User.objects.create(
                name=name, mobile=mobile, email=email,
                password=password, ration_card_no=ration_card_no,
                address=address, role='user'
            )
            messages.success(request, f'User {name} added successfully ✅')
            return redirect('add_user')
    return render(request, 'add_user.html', {'all_users': all_users})


def edit_user(request, id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    user = get_object_or_404(User, id=id)
    if request.method == 'POST':
        user.name = request.POST.get('name')
        user.mobile = request.POST.get('mobile')
        user.email = request.POST.get('email')
        user.password = request.POST.get('password')
        user.ration_card_no = request.POST.get('ration_card_no')
        user.address = request.POST.get('address')
        user.save()
        messages.success(request, f'{user.name} updated successfully ✅')
        return redirect('add_user')
    return render(request, 'edit_user.html', {'u': user})


def add_member(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    user = User.objects.get(id=user_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        age = request.POST.get('age')
        if FamilyMember.objects.filter(name=name, user=user).exists():
            messages.error(request, 'Member already exists ❌')
        else:
            FamilyMember.objects.create(user=user, name=name, age=age)
            messages.success(request, 'Member added successfully ✅')
    members = FamilyMember.objects.filter(user=user)
    return render(request, 'add_member.html', {'members': members})


def delete_user(request, id):
    user = get_object_or_404(User, id=id)
    user.delete()
    messages.success(request, f'User deleted successfully ✅')
    # redirect back to whoever called it
    referer = request.META.get('HTTP_REFERER', '')
    if 'add-user' in referer:
        return redirect('add_user')
    return redirect('admin_dashboard')


def profile(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    user = User.objects.get(id=user_id)
    members = FamilyMember.objects.filter(user=user)
    return render(request, 'profile.html', {'user': user, 'members': members})


def logout(request):
    request.session.flush()
    return redirect('login')


def receipt(request):
    data = request.session.get('receipt')
    if not data:
        return redirect('shop_dashboard')
    return render(request, 'receipt.html', {'data': data})


def update_stock(request):
    if request.method == 'POST':
        item = request.POST.get('item')
        quantity = int(request.POST.get('quantity'))
        stock, _ = Stock.objects.get_or_create(item_name=item, defaults={'quantity': 0})
        stock.quantity += quantity
        stock.available_from = now() + timedelta(days=2)
        stock.save()

        collect_datetime = (now() + timedelta(days=2)).strftime('%d %b %Y at %I:%M %p')

        Notification.objects.create(
            message=f'{item} stock updated. Come and collect after {collect_datetime}.',
            show_from=now() + timedelta(days=2)
        )

        all_users = User.objects.filter(role='user')
        for u in all_users:
            if u.email:
                try:
                    send_mail(
                        subject=f'📦 {item} Stock Updated - Collect After 2 Days',
                        message=f"""Dear {u.name},

Great news! The ration stock has been updated for this month.

📦 Stock Update Details:
━━━━━━━━━━━━━━━━━━━━━━━━
🛒 Item Updated  : {item}
📅 Updated On    : {now().strftime('%d %b %Y at %I:%M %p')}
⏳ Collect After : {collect_datetime}
━━━━━━━━━━━━━━━━━━━━━━━━

Please visit your nearest ration shop after {collect_datetime} to collect your monthly ration.

Do not forget to carry your Ration Card.

Thank you.
- Ration System""",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[u.email],
                    )
                except Exception as e:
                    print(f'Email error for {u.name}: {e}')

        messages.success(request, f'Stock updated! Users notified to collect after {collect_datetime}.')
    return redirect('admin_dashboard')
