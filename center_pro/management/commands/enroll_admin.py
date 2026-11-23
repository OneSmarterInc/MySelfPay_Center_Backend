import getpass
import pyotp
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from center_pro.models import AdminMFA
from center_pro.auth_flows import cipher

class Command(BaseCommand):
    help='Enroll an existing superuser using an authenticator, from a private interactive terminal.'
    def add_arguments(self,parser):parser.add_argument('username')
    def handle(self,*args,**kwargs):
        user=get_user_model().objects.filter(username=kwargs['username'],is_superuser=True,is_active=True).first()
        if not user:raise CommandError('Active superuser not found. Use createsuperuser first.')
        if AdminMFA.objects.filter(user=user).exists():raise CommandError('Already enrolled. MFA recovery requires a separate reviewed administrator procedure.')
        secret=pyotp.random_base32();totp=pyotp.TOTP(secret)
        self.stdout.write('Private authenticator enrollment URI (do not share or paste into chat):')
        self.stdout.write(totp.provisioning_uri(name=user.username,issuer_name='MySelfPay Center Pro'))
        code=getpass.getpass('Enter the current authenticator code to verify enrollment: ')
        if not totp.verify(code,valid_window=1):raise CommandError('Code did not match. Enrollment was not saved.')
        AdminMFA.objects.create(user=user,encrypted_secret=cipher().encrypt(secret.encode()).decode())
        self.stdout.write(self.style.SUCCESS('MFA enrollment saved.'))
