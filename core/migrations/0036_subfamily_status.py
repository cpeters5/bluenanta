# Generated by Django 3.2.15 on 2023-08-01 18:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0035_family_clss'),
    ]

    operations = [
        migrations.AddField(
            model_name='subfamily',
            name='status',
            field=models.CharField(choices=[('accepted', 'accepted'), ('registered', 'registered'), ('nonregistered', 'nonregistered'), ('unplaced', 'unplaced'), ('published', 'published'), ('trade', 'trade')], default='', max_length=20),
        ),
    ]
