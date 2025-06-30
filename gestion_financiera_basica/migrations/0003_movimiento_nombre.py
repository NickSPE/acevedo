from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("gestion_financiera_basica", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="movimiento",
            name="nombre",
            field=models.CharField(default="none", max_length=50),
            preserve_default=False,
        ),
    ]