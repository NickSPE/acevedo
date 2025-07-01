from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ("cuentas", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cuenta",
            name="descripcion",
            field=models.CharField(max_length=300),
        ),
    ]