# Generated by Django 3.2.15 on 2022-12-26 10:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0034_alter_family_orig_pid'),
    ]

    operations = [
        migrations.AddField(
            model_name='family',
            name='clss',
            field=models.CharField(max_length=20, null=True),
        ),
    ]
