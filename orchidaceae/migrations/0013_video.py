# Generated by Django 3.2.15 on 2023-11-23 13:25

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0036_subfamily_status'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0012_auto_20230716_2258'),
        ('orchidaceae', '0012_species_comment'),
    ]

    operations = [
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('binomial', models.CharField(blank=True, max_length=100, null=True)),
                ('credit_to', models.CharField(blank=True, max_length=100, null=True)),
                ('status', models.CharField(default='TBD', max_length=10)),
                ('quality', models.IntegerField(choices=[(1, 'Top'), (2, 'High'), (3, 'Average'), (4, 'Low')], default=3)),
                ('source_url', models.CharField(blank=True, max_length=1000, null=True)),
                ('video_url', models.CharField(blank=True, max_length=500, null=True)),
                ('text_data', models.TextField(blank=True, null=True)),
                ('description', models.CharField(blank=True, max_length=100, null=True)),
                ('location', models.CharField(blank=True, max_length=100, null=True)),
                ('video_file', models.CharField(blank=True, max_length=100, null=True)),
                ('video_file_path', models.ImageField(blank=True, null=True, upload_to='utils/images/photos')),
                ('download_date', models.DateField(blank=True, null=True)),
                ('created_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_date', models.DateTimeField(auto_now=True, null=True)),
                ('approved_by', models.ForeignKey(blank=True, db_column='approved_by', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='orcvideoapproved_by', to=settings.AUTH_USER_MODEL)),
                ('author', models.ForeignKey(db_column='author', on_delete=django.db.models.deletion.DO_NOTHING, related_name='orcvideoauthor', to='accounts.photographer')),
                ('family', models.ForeignKey(db_column='family', on_delete=django.db.models.deletion.DO_NOTHING, related_name='orcvideofamily', to='core.family')),
                ('pid', models.ForeignKey(db_column='pid', on_delete=django.db.models.deletion.DO_NOTHING, related_name='orcvideopid', to='orchidaceae.species')),
                ('user_id', models.ForeignKey(blank=True, db_column='user_id', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='orcvideouser_id', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
