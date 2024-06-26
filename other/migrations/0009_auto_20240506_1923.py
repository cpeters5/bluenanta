# Generated by Django 3.2.15 on 2024-05-06 19:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('other', '0008_auto_20240506_1906'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accepted',
            name='binomial',
            field=models.CharField(max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='hybrid',
            name='binomial',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='spcimages',
            name='binomial',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='species',
            name='binomial',
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AlterField(
            model_name='uploadfile',
            name='binomial',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='video',
            name='binomial',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]
