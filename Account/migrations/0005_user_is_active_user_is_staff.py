# Generated by Django 5.2 on 2025-05-04 18:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Account', '0004_remove_dataset_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='user',
            name='is_staff',
            field=models.BooleanField(default=False),
        ),
    ]
