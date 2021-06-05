# Generated by Django 3.1.6 on 2021-04-01 18:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('other', '0009_auto_20210329_0137'),
    ]

    operations = [
        migrations.CreateModel(
            name='AncestorDescendant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('anctype', models.CharField(default='hybrid', max_length=10)),
                ('pct', models.FloatField(blank=True, null=True)),
                ('aid', models.ForeignKey(db_column='aid', on_delete=django.db.models.deletion.CASCADE, related_name='oraid', to='other.species')),
                ('did', models.ForeignKey(db_column='did', on_delete=django.db.models.deletion.CASCADE, related_name='ordid', to='other.hybrid')),
            ],
            options={
                'unique_together': {('did', 'aid')},
            },
        ),
    ]
