# Generated by Django 5.2 on 2025-06-14 20:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_ruta'),
    ]

    operations = [
        migrations.CreateModel(
            name='Alerta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('descripcion', models.TextField()),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('activa', models.BooleanField(default=True)),
            ],
        ),
    ]
