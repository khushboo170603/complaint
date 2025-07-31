from django.core.management.base import BaseCommand
from django.utils.timezone import now
from datetime import timedelta

from complaint.models import Complaint


class Command(BaseCommand):
    help = 'Automatically update complaints to pending if not assigned or unresolved within deadlines.'

    
    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Preview changes without saving')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        current_time = now()

        deadline_24h = current_time - timedelta(hours=24)
        unassigned_qs = Complaint.objects.filter(
            status='open',
            assigned_engineer__isnull=True,
            created_at__lte=deadline_24h
        )
        count_unassigned = unassigned_qs.count()

        deadline_48h = current_time - timedelta(hours=48)
        assigned_qs = Complaint.objects.filter(
            status='in_progress',
            assigned_engineer__isnull=False,
            assigned_date__lte=deadline_48h,
            resolved_date__isnull=True
        )
        count_assigned = assigned_qs.count()

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"[Dry Run] Would update {count_unassigned} unassigned and {count_assigned} assigned complaints to 'pending'."
            ))
        else:
            unassigned_qs.update(status='pending')
            assigned_qs.update(status='pending')
            self.stdout.write(self.style.SUCCESS(
                f"✅ Updated {count_unassigned} unassigned and {count_assigned} assigned complaints to 'pending'."
            ))

