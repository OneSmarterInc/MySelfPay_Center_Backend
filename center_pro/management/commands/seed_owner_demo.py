from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from center_pro.models import Center, Offer, OutreachTarget


class Command(BaseCommand):
    help = 'Seed owner-module sample data for the existing local demo centers only.'
    @transaction.atomic
    def handle(self, *args, **kwargs):
        if not settings.DEBUG or not settings.ENABLE_DEV_LOGIN:
            raise CommandError('Demo seeding requires DEBUG and ENABLE_DEV_LOGIN.')
        centers = Center.objects.filter(name__in=['Demo Imaging · Dayton', 'Demo Imaging · Cincinnati'])
        if not centers.exists():
            raise CommandError('Run seed_demo first.')
        for center in centers:
            for exam, price, benchmark in [('Lumbar MRI','395.00','385.00'), ('Brain MRI','475.00','465.00'), ('CT abdomen / pelvis','525.00','450.00')]:
                Offer.objects.get_or_create(center=center, exam=exam, defaults={'price':price, 'benchmark_price':benchmark, 'benchmark_source':'Synthetic comparison — not a verified market rate', 'benchmark_checked_at':timezone.localdate()})
            for name, category, distance in [('Sample Oak Grove','DPC clinic','2.4'),('Sample Northstar','Chiropractor','3.1'),('Sample Riverside','Law firm','4.6'),('Sample West Dayton','Urgent care','6.2'),('Sample Moraine','Employer','8.7')]:
                OutreachTarget.objects.get_or_create(center=center,name=name,defaults={'category':category,'distance_miles':distance})
        self.stdout.write(self.style.SUCCESS('Sample offers and outreach targets are ready; existing changes were retained.'))
