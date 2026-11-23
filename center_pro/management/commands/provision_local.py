import secrets
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help='Provision local sample emails and a development-only admin account.'
    def handle(self,*args,**kwargs):
        if not settings.DEBUG or not settings.ENABLE_DEV_LOGIN:raise CommandError('Local development only.')
        for role in ('owner','staff'):
            user=get_user_model().objects.filter(username='demo-'+role).first()
            if user:
                user.email=role+'@example.test';user.save(update_fields=['email'])
        admin,created=get_user_model().objects.get_or_create(username='demo-admin',defaults={'first_name':'Sample administrator','is_staff':True,'is_superuser':True})
        if created:
            admin.set_unusable_password();admin.save()
        self.stdout.write('Sample emails and development admin are ready. No credentials or messages were sent.')
