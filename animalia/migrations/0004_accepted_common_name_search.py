# Generated by Django 3.2.15 on 2023-04-22 15:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('animalia', '0003_auto_20230331_1225'),
    ]

    operations = [
        migrations.AddField(
            model_name='accepted',
            name='common_name_search',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]
