# Generated by Django 3.2.15 on 2023-10-12 13:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orchidaceae', '0011_accepted_common_name_search'),
    ]

    operations = [
        migrations.AddField(
            model_name='species',
            name='comment',
            field=models.TextField(blank=True, null=True),
        ),
    ]