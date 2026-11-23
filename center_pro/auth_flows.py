import base64
import hashlib
import json
import secrets
import time
from datetime import timedelta
from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login
from django.core.mail import send_mail
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
import pyotp
from .models import MagicLink, Membership, AuthLimit, AdminMFA
from .views import identity


def cipher():
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256((settings.SECRET_KEY+'center-pro-mfa').encode()).digest()))


def payload(request):
    try:
        value=json.loads(request.body)
        return value if isinstance(value,dict) else {}
    except (ValueError,UnicodeDecodeError):
        return {}


@transaction.atomic
def allowed(key,maximum):
    now=timezone.now()
    item,_=AuthLimit.objects.get_or_create(key=hashlib.sha256(key.encode()).hexdigest(),defaults={'resets_at':now+timedelta(minutes=15)})
    item=AuthLimit.objects.select_for_update().get(pk=item.pk)
    if item.resets_at<=now:
        item.count=0;item.resets_at=now+timedelta(minutes=15)
    item.count+=1
    item.save(update_fields=['count','resets_at'])
    return item.count<=maximum


@require_POST
@csrf_protect
def request_link(request):
    email=str(payload(request).get('email','')).strip().lower()[:254]
    if not allowed('magic-ip:'+request.META.get('REMOTE_ADDR',''),30) or not allowed('magic-email:'+email,5):
        return JsonResponse({'detail':'Please wait before requesting another link.'},status=429)
    result={'detail':'If this email has center access, a sign-in link will be sent.'}
    if not settings.DEBUG and not settings.EMAIL_HOST:
        return JsonResponse({'detail':'Email delivery is not configured. Contact your administrator.'},status=503)
    users=get_user_model().objects.filter(email__iexact=email,is_active=True,is_superuser=False)
    if '@' not in email or users.count()!=1:
        return JsonResponse(result)
    user=users.first()
    if not Membership.objects.filter(user=user).exists():
        return JsonResponse(result)
    if not settings.DEBUG and not settings.EMAIL_HOST:
        return JsonResponse({'detail':'Email delivery is not configured. Contact your administrator.'},status=503)
    raw=secrets.token_urlsafe(32)
    link=MagicLink.objects.create(user=user,digest=hashlib.sha256(raw.encode()).hexdigest(),expires_at=timezone.now()+timedelta(minutes=15))
    url=settings.FRONTEND_ORIGIN+'/#/verify/'+raw
    if settings.DEBUG:
        result['development_url']=url
        result['detail']='Local development link created. No email was sent.'
    else:
        try:
            send_mail('Your MySelfPay Center Pro sign-in link','Open this single-use link within 15 minutes: '+url,settings.DEFAULT_FROM_EMAIL,[email],fail_silently=False)
        except Exception:
            link.delete()
            return JsonResponse({'detail':'Email delivery failed. Please try again later.'},status=503)
    return JsonResponse(result)


@require_POST
@csrf_protect
@transaction.atomic
def verify_link(request):
    raw=str(payload(request).get('token',''))[:256]
    link=MagicLink.objects.select_for_update().select_related('user').filter(digest=hashlib.sha256(raw.encode()).hexdigest(),used_at__isnull=True,expires_at__gt=timezone.now()).first()
    if not link or not link.user.is_active or link.user.is_superuser or not Membership.objects.filter(user=link.user).exists():
        return JsonResponse({'detail':'This sign-in link is invalid, expired or no longer has access.'},status=400)
    link.used_at=timezone.now();link.save(update_fields=['used_at'])
    login(request,link.user,backend='django.contrib.auth.backends.ModelBackend')
    return JsonResponse(identity(request))


@require_POST
@csrf_protect
def admin_login(request):
    data=payload(request)
    if not allowed('admin-ip:'+request.META.get('REMOTE_ADDR',''),10):
        return JsonResponse({'detail':'Too many attempts. Try again later.'},status=429)
    user=authenticate(request,username=str(data.get('username',''))[:150],password=str(data.get('password',''))[:256])
    if not user or not user.is_superuser:
        return JsonResponse({'detail':'Invalid credentials or authentication code.'},status=400)
    with transaction.atomic():
        profile=AdminMFA.objects.select_for_update().filter(user=user).first()
        if not profile:
            return JsonResponse({'detail':'MFA enrollment is required. Contact your system administrator.'},status=403)
        totp=pyotp.TOTP(cipher().decrypt(profile.encrypted_secret.encode()).decode())
        code=str(data.get('code',''))
        if len(code)!=6 or not code.isascii() or not code.isdecimal():
            return JsonResponse({'detail':'Invalid credentials or authentication code.'},status=400)
        current=int(time.time()//30)
        matching=next((counter for counter in (current-1,current,current+1) if counter>profile.last_counter and secrets.compare_digest(totp.at(counter*30),code)),None)
        if matching is None:
            return JsonResponse({'detail':'Invalid credentials or authentication code.'},status=400)
        profile.last_counter=matching;profile.save(update_fields=['last_counter'])
    login(request,user);request.session['pro_admin_mfa']=True
    return JsonResponse(identity(request))
