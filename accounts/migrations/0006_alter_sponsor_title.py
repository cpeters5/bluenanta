# Generated by Django 3.2.15 on 2022-10-28 11:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_sponsor_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sponsor',
            name='title',
            field=models.CharField(default='', max_length=100),
        ),
    ]