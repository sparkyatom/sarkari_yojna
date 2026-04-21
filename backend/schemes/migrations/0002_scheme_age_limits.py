from django.db import migrations, models


def backfill_age_limits(apps, schema_editor):
    """
    Best-effort backfill for existing data.
    If a scheme name/description implies senior citizen eligibility, set min_age=60.
    """
    Scheme = apps.get_model('schemes', 'Scheme')
    qs = Scheme.objects.all()
    for s in qs.iterator():
        if s.min_age is not None or s.max_age is not None:
            continue
        name = (s.name or '').lower()
        desc = (s.description or '').lower()
        if 'senior citizen' in name or 'senior citizen' in desc or 'above 60' in desc or '60 years' in desc:
            s.min_age = 60
            s.save(update_fields=['min_age'])


class Migration(migrations.Migration):
    dependencies = [
        ('schemes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheme',
            name='min_age',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='scheme',
            name='max_age',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_age_limits, migrations.RunPython.noop),
    ]

