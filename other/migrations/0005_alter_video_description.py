# Generated by Django 3.2.15 on 2024-05-02 17:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('other', '0004_auto_20240430_2142'),
    ]

    operations = [
        migrations.AlterField(
            model_name='video',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]