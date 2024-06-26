# Generated by Django 3.2.15 on 2024-05-06 19:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fungi', '0004_alter_video_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploadfile',
            name='binomial',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='accepted',
            name='binomial',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='hybrid',
            name='binomial',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='spcimages',
            name='binomial',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='species',
            name='binomial',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='video',
            name='binomial',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
