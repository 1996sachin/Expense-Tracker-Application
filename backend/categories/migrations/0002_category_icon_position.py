from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('categories', '0001_initial')]

    operations = [
        migrations.AddField(model_name='category', name='icon', field=models.CharField(blank=True, max_length=40)),
        migrations.AddField(model_name='category', name='position', field=models.PositiveIntegerField(default=0)),
    ]
