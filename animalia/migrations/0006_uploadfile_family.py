# Generated by Django 3.2.15 on 2024-05-06 16:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_initial'),
        ('animalia', '0005_auto_20240503_2346'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploadfile',
            name='family',
            field=models.ForeignKey(blank=True, db_column='family', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='aniuplfamily', to='common.family'),
        ),
    ]
