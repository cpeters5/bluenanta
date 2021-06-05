# Generated by Django 3.1.6 on 2021-03-28 03:49

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0016_family_application'),
        ('other', '0005_synonym'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hybrid',
            name='user_id',
            field=models.ForeignKey(blank=True, db_column='user_id', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='othuser_id1', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='UploadFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('credit_to', models.CharField(blank=True, max_length=100, null=True)),
                ('source_url', models.CharField(blank=True, max_length=1000, null=True)),
                ('source_file_name', models.CharField(blank=True, max_length=100, null=True)),
                ('name', models.CharField(blank=True, max_length=100, null=True)),
                ('awards', models.CharField(blank=True, max_length=200, null=True)),
                ('variation', models.CharField(blank=True, max_length=50, null=True)),
                ('forma', models.CharField(blank=True, max_length=50, null=True)),
                ('originator', models.CharField(blank=True, max_length=50, null=True)),
                ('text_data', models.TextField(blank=True, null=True)),
                ('description', models.CharField(blank=True, max_length=100, null=True)),
                ('certainty', models.CharField(blank=True, max_length=20, null=True)),
                ('type', models.CharField(blank=True, max_length=20, null=True)),
                ('location', models.CharField(blank=True, max_length=100, null=True)),
                ('rank', models.IntegerField(choices=[(0, '0'), (1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '6'), (7, '7'), (8, '8'), (9, '9')], default=0)),
                ('image_file_path', models.ImageField(blank=True, null=True, upload_to='images/')),
                ('image_file', models.CharField(blank=True, max_length=100, null=True)),
                ('is_private', models.BooleanField(default=False, null=True)),
                ('approved', models.BooleanField(default=False, null=True)),
                ('compressed', models.BooleanField(default=False, null=True)),
                ('block_id', models.IntegerField(blank=True, null=True)),
                ('created_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_date', models.DateTimeField(auto_now=True, null=True)),
                ('author', models.ForeignKey(blank=True, db_column='author', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='othauthor', to='accounts.photographer')),
                ('pid', models.ForeignKey(blank=True, db_column='pid', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='othpid', to='other.species')),
                ('user_id', models.ForeignKey(blank=True, db_column='user_id', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='othuser_id', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Distribution',
            fields=[
                ('id', models.AutoField(default=10, primary_key=True, serialize=False)),
                ('source', models.CharField(blank=True, max_length=10)),
                ('dist_code', models.CharField(max_length=10, null=True)),
                ('localregion_code', models.CharField(max_length=10, null=True)),
                ('comment', models.CharField(blank=True, max_length=500)),
                ('created_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_date', models.DateTimeField(auto_now=True, null=True)),
                ('localregion_id', models.ForeignKey(blank=True, db_column='localregion_id', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='othnatlocalregion_id', to='core.localregion')),
                ('pid', models.ForeignKey(db_column='pid', on_delete=django.db.models.deletion.CASCADE, related_name='othdist_pid', to='other.species')),
                ('region_id', models.ForeignKey(db_column='region_id', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='othnatregion_id', to='core.region')),
                ('subregion_code', models.ForeignKey(db_column='subregion_code', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='othnatsubregion_id', to='core.subregion')),
            ],
            options={
                'unique_together': {('pid', 'region_id', 'subregion_code', 'localregion_id')},
            },
        ),
    ]
