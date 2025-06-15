import json
import os

from django.core.management.base import BaseCommand

from Account.models import Entity, Role


class Command(BaseCommand):
    help = "Populate database with initial data from JSON"

    def handle(self, *args, **kwargs):
        file_path = os.path.join(os.path.dirname(__file__), "../../fixtures/data.json")

        # Load JSON data
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        self.stdout.write(self.style.SUCCESS("📂 Loading JSON data..."))

        # Populate Model1
        if not Entity.objects.exists():
            for item in data.get("Entity", []):
                Entity.objects.create(**item)
            self.stdout.write(self.style.SUCCESS("✅ Enity data populated"))

        # Populate Model2
        if not Role.objects.exists():
            for item in data.get("Role", []):
                Role.objects.create(**item)
            self.stdout.write(self.style.SUCCESS("✅ Role data populated"))

        # # Populate Model3
        # if not Model3.objects.exists():
        #     for item in data.get("model3", []):
        #         Model3.objects.create(**item)
        #     self.stdout.write(self.style.SUCCESS("✅ Model3 data populated"))

        # # Populate Model4
        # if not Model4.objects.exists():
        #     for item in data.get("model4", []):
        #         Model4.objects.create(**item)
        #     self.stdout.write(self.style.SUCCESS("✅ Model4 data populated"))

        self.stdout.write(self.style.SUCCESS("🎉 Database seeding complete!"))
