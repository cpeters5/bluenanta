# Generated by Django 3.2.13 on 2022-05-21 03:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_auto_20220519_2257'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subfamily',
            name='year',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='tribe',
            name='status',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='tribe',
            name='year',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
