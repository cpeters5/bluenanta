# Generated by Django 3.0.9 on 2021-03-18 03:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('other', '0003_hybrid'),
    ]

    operations = [
        migrations.AddField(
            model_name='genus',
            name='is_succulent',
            field=models.BooleanField(default=False, null=True),
        ),
    ]
