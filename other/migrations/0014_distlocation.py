# Generated by Django 3.2.15 on 2022-10-24 21:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('other', '0013_rename_distlocation_location'),
    ]

    operations = [
        migrations.CreateModel(
            name='DistLocation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dist', models.CharField(max_length=200)),
                ('pid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='distpid', to='other.species')),
            ],
        ),
    ]