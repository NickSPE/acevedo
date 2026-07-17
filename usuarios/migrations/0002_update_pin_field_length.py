from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuario',
            name='pin_acceso_rapido',
            field=models.CharField(default='000000', max_length=128),
        ),
    ]
