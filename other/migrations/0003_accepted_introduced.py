# Generated by Django 3.2.13 on 2022-05-11 11:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('other', '0002_auto_20220106_1453'),
    ]

    operations = [
        migrations.AddField(
            model_name='accepted',
            name='introduced',
            field=models.TextField(blank=True),
        ),
    ]
