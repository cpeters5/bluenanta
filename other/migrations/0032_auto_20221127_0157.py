# Generated by Django 3.2.15 on 2022-11-27 01:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('other', '0031_spcimages_binomial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='spcimages',
            name='is_private',
        ),
        migrations.RemoveField(
            model_name='spcimages',
            name='spid',
        ),
        migrations.RemoveField(
            model_name='spcimages',
            name='zoom',
        ),
        migrations.AddField(
            model_name='spcimages',
            name='species',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
