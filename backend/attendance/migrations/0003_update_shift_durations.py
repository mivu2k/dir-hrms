# Generated manually on 2026-06-17

from django.db import migrations

def update_shifts(apps, schema_editor):
    Shift = apps.get_model('attendance', 'Shift')
    # Update all existing shifts to the 7.00 hours full day / 3.50 hours half day requirement
    Shift.objects.all().update(min_hours_full_day=7.00, min_hours_half_day=3.50)

def reverse_update_shifts(apps, schema_editor):
    Shift = apps.get_model('attendance', 'Shift')
    Shift.objects.all().update(min_hours_full_day=8.00, min_hours_half_day=4.00)

class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(update_shifts, reverse_update_shifts),
    ]
