from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from center_pro.models import Center, Membership, Slot, BookingRequest

class Command(BaseCommand):
    help = 'Create synthetic local data only; never connect this command to a company database.'
    @transaction.atomic
    def handle(self, *args, **kwargs):
        if not settings.DEBUG or not settings.ENABLE_DEV_LOGIN:
            raise CommandError('Demo seeding requires DJANGO_DEBUG=true and ENABLE_DEV_LOGIN=true.')
        centers = [Center.objects.get_or_create(name='Demo Imaging · '+city)[0] for city in ('Dayton', 'Cincinnati')]
        for role in ('owner', 'staff'):
            user, created = get_user_model().objects.get_or_create(username='demo-'+role, defaults={'first_name': 'Demo '+role.title()})
            if created:
                user.set_unusable_password(); user.save()
            for center in centers:
                Membership.objects.get_or_create(user=user, center=center, defaults={'role': role})
        start = (timezone.now()+timedelta(days=1)).replace(hour=14, minute=0, second=0, microsecond=0)
        for center in centers:
            for i in range(40):
                at = start+timedelta(days=i//8, minutes=30*(i%8))
                Slot.objects.get_or_create(center=center, resource='Demo scanner 1', starts_at=at, defaults={'ends_at': at+timedelta(minutes=30)})
            for i in range(125):
                BookingRequest.objects.get_or_create(reference=f'DEMO-{center.id}-{i+1:04}', defaults={'center': center, 'patient_name': f'Sample Patient {i+1:03}', 'exam': ['Lumbar MRI','Brain MRI','CT abdomen / pelvis'][i%3], 'source': ['myselfpay','cash_rescue','qr_referral'][i%3], 'preferred_windows': ['Morning','Afternoon'], 'price_snapshot': ['395.00','475.00','525.00'][i%3]})
        for center in centers:
            choices=list(Slot.objects.filter(center=center,blocked=False,starts_at__gt=timezone.now()).order_by('starts_at','id').values_list('id',flat=True))
            if len(choices)>=3:
                for index,booking in enumerate(BookingRequest.objects.filter(center=center,status='pending',reference__startswith=f'DEMO-{center.id}-').order_by('id')):
                    booking.preferred_slot_ids=[choices[(index+j)%len(choices)] for j in range(3)]
                    booking.preferred_windows=[]
                    booking.save(update_fields=['preferred_slot_ids','preferred_windows'])
        self.stdout.write(self.style.SUCCESS('Local sample centers, memberships, slots and 250 requests are ready.'))
