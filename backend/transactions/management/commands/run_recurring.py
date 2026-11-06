from django.core.management.base import BaseCommand
from transactions.tasks import generate_recurring_transactions


class Command(BaseCommand):
    help = 'Generate recurring transactions (run daily via ECS scheduled task)'

    def handle(self, *args, **options):
        count = generate_recurring_transactions()
        self.stdout.write(self.style.SUCCESS(f'Created {count} recurring transactions'))
