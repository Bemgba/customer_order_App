"""
Management command to create inventory consumption tracking system.
This adds a new model for tracking ingredient usage history.
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Setup script - inventory consumption tracking is now built into the models'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(
                'Inventory consumption tracking is implemented via the IngredientConsumption model.\n'
                'Run: python manage.py makemigrations\n'
                'Then: python manage.py migrate\n'
                'To apply the new database schema.'
            )
        )
