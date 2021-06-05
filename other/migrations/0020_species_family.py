# Generated by Django 3.1.6 on 2021-04-17 07:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_auto_20210329_1547'),
        ('other', '0019_auto_20210417_0617'),
    ]

    operations = [
        migrations.AddField(
            model_name='species',
            name='family',
            field=models.ForeignKey(db_column='family', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='spcotfamily', to='core.family'),
        ),
    ]
