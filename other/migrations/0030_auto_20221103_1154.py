# Generated by Django 3.2.15 on 2022-11-03 11:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('other', '0029_alter_distribution_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='accepted',
            name='location',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='genus',
            name='location',
            field=models.TextField(null=True),
        ),
    ]
