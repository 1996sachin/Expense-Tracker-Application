# Generated manually for the Pocketly account enhancements.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('accounts', '0004_user_currency_default_npr')]

    operations = [
        migrations.AddField(model_name='user', name='apple_id', field=models.CharField(blank=True, max_length=255, null=True, unique=True)),
        migrations.AddField(model_name='user', name='date_of_birth', field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name='user', name='language', field=models.CharField(default='en', max_length=12)),
        migrations.AddField(model_name='user', name='onboarding_complete', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='user', name='sex', field=models.CharField(blank=True, max_length=24)),
    ]
