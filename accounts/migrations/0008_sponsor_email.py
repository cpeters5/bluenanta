# Generated by Django 3.2.15 on 2022-11-01 13:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_sponsor_short_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='sponsor',
            name='email',
            field=models.EmailField(default=None, max_length=255, null=True, verbose_name='email address'),
        ),
    ]
