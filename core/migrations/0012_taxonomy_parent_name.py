# Generated by Django 3.0.9 on 2021-03-20 19:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_taxonomy_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxonomy',
            name='parent_name',
            field=models.CharField(default='', max_length=50),
        ),
    ]
