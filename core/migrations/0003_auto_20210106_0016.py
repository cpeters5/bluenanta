# Generated by Django 3.0.9 on 2021-01-06 00:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_delete_geoloc'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subfamily',
            name='author',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
    ]
