# Generated by Django 3.2.15 on 2023-11-23 13:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aves', '0005_video'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
