# Generated by Django 3.2.15 on 2022-12-07 14:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_rename_user_id_sponsor_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sponsor',
            name='country_code',
            field=models.CharField(blank=True, max_length=3, null=True),
        ),
    ]
