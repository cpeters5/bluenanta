# Generated by Django 3.2.15 on 2022-11-27 01:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fungi', '0003_auto_20221127_0045'),
    ]

    operations = [
        migrations.AddField(
            model_name='spcimages',
            name='gen',
            field=models.ForeignKey(blank=True, db_column='gen', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='poolspcgen', to='fungi.genus'),
        ),
        migrations.AddField(
            model_name='spcimages',
            name='genus',
            field=models.CharField(default='', max_length=50),
            preserve_default=False,
        ),
    ]
