# Generated by Django 3.2.15 on 2022-10-24 22:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('other', '0015_auto_20221024_2132'),
    ]

    operations = [
        migrations.AlterField(
            model_name='distlocation',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='location',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
