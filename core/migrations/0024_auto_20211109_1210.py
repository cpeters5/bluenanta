# Generated by Django 3.2.5 on 2021-11-09 12:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_family_common_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='family',
            name='kingdom',
            field=models.CharField(max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='family',
            name='order',
            field=models.CharField(max_length=20, null=True),
        ),
    ]