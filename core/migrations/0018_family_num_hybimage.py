# Generated by Django 3.1.6 on 2021-03-29 15:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_family_num_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='family',
            name='num_hybimage',
            field=models.IntegerField(null=True),
        ),
    ]