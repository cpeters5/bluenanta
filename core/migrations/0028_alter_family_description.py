# Generated by Django 3.2.13 on 2022-05-19 22:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_family_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='family',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
