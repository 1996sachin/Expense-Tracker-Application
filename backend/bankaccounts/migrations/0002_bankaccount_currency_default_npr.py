from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('bankaccounts', '0001_initial')]
    operations = [
        migrations.AlterField(
            model_name='bankaccount',
            name='currency',
            field=models.CharField(default='NPR', max_length=3),
        ),
    ]
