from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('accounts', '0003_mfachallenge_mfadevice_recoverycode_securityevent')]
    operations = [
        migrations.AlterField(
            model_name='user',
            name='currency_preference',
            field=models.CharField(default='NPR', max_length=3),
        ),
    ]
