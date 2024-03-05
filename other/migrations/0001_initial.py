# Generated by Django 3.2.15 on 2024-03-04 17:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('common', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Genus',
            fields=[
                ('pid', models.BigAutoField(primary_key=True, serialize=False)),
                ('orig_pid', models.CharField(blank=True, max_length=20, null=True)),
                ('is_hybrid', models.CharField(max_length=1, null=True)),
                ('genus', models.CharField(default='', max_length=50, unique=True)),
                ('author', models.CharField(blank=True, max_length=200)),
                ('citation', models.CharField(default='', max_length=200)),
                ('cit_status', models.CharField(max_length=20, null=True)),
                ('is_succulent', models.BooleanField(default=False, null=True)),
                ('is_carnivorous', models.BooleanField(default=False, null=True)),
                ('is_extinct', models.BooleanField(default=False, null=True)),
                ('is_parasitic', models.BooleanField(default=False, null=True)),
                ('status', models.CharField(blank=True, max_length=20)),
                ('type', models.CharField(default='', max_length=20)),
                ('common_name', models.CharField(blank=True, max_length=200, null=True)),
                ('description', models.TextField(null=True)),
                ('location', models.TextField(null=True)),
                ('distribution', models.TextField(null=True)),
                ('text_data', models.TextField(null=True)),
                ('source', models.CharField(blank=True, max_length=50)),
                ('abrev', models.CharField(blank=True, max_length=50)),
                ('year', models.IntegerField(blank=True, null=True)),
                ('num_species', models.IntegerField(default=0, null=True)),
                ('num_species_synonym', models.IntegerField(default=0, null=True)),
                ('num_species_total', models.IntegerField(default=0, null=True)),
                ('num_hybrid', models.IntegerField(default=0, null=True)),
                ('num_hybrid_synonym', models.IntegerField(default=0, null=True)),
                ('num_hybrid_total', models.IntegerField(default=0, null=True)),
                ('num_synonym', models.IntegerField(default=0, null=True)),
                ('num_spcimage', models.IntegerField(default=0, null=True)),
                ('num_spc_with_image', models.IntegerField(default=0, null=True)),
                ('pct_spc_with_image', models.DecimalField(decimal_places=2, default=0, max_digits=7, null=True)),
                ('num_hybimage', models.IntegerField(default=0, null=True)),
                ('num_hyb_with_image', models.IntegerField(default=0, null=True)),
                ('pct_hyb_with_image', models.DecimalField(decimal_places=2, default=0, max_digits=7, null=True)),
                ('notepad', models.CharField(default='', max_length=500)),
                ('created_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_date', models.DateTimeField(auto_now=True, null=True)),
                ('family', models.ForeignKey(blank=True, db_column='family', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='otfamily', to='common.family')),
                ('subfamily', models.ForeignKey(blank=True, db_column='subfamily', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='poolsubfamily', to='common.subfamily')),
                ('subtribe', models.ForeignKey(blank=True, db_column='subtribe', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='poolsubtribe', to='common.subtribe')),
                ('tribe', models.ForeignKey(blank=True, db_column='tribe', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='pooltribe', to='common.tribe')),
            ],
            options={
                'ordering': ('genus',),
            },
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dist', models.CharField(blank=True, max_length=200, unique=True)),
                ('name', models.CharField(blank=True, max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Species',
            fields=[
                ('pid', models.BigAutoField(primary_key=True, serialize=False)),
                ('orig_pid', models.CharField(blank=True, max_length=20, null=True)),
                ('source', models.CharField(blank=True, max_length=10)),
                ('genus', models.CharField(blank=True, max_length=50, null=True)),
                ('is_hybrid', models.CharField(max_length=1, null=True)),
                ('species', models.CharField(blank=True, max_length=50, null=True)),
                ('infraspr', models.CharField(blank=True, max_length=20, null=True)),
                ('infraspe', models.CharField(blank=True, max_length=50, null=True)),
                ('author', models.CharField(blank=True, max_length=200)),
                ('originator', models.CharField(blank=True, max_length=100)),
                ('binomial', models.CharField(blank=True, max_length=500)),
                ('citation', models.CharField(max_length=200)),
                ('is_succulent', models.BooleanField(default=False, null=True)),
                ('is_carnivorous', models.BooleanField(default=False, null=True)),
                ('is_parasitic', models.BooleanField(default=False, null=True)),
                ('cit_status', models.CharField(max_length=20, null=True)),
                ('conservation_status', models.CharField(max_length=20, null=True)),
                ('status', models.CharField(choices=[('accepted', 'accepted'), ('registered', 'registered'), ('nonregistered', 'nonregistered'), ('unplaced', 'unplaced'), ('published', 'published'), ('trade', 'trade'), ('synonym', 'synonym')], default='', max_length=20)),
                ('type', models.CharField(choices=[('species', 'species'), ('hybrid', 'hybrid')], default='', max_length=10)),
                ('year', models.IntegerField(blank=True, null=True)),
                ('date', models.DateField(null=True)),
                ('distribution', models.TextField(blank=True)),
                ('physiology', models.CharField(blank=True, max_length=200)),
                ('url', models.CharField(blank=True, max_length=200)),
                ('url_name', models.CharField(blank=True, max_length=100)),
                ('num_image', models.IntegerField(blank=True)),
                ('num_ancestor', models.IntegerField(blank=True, null=True)),
                ('num_species_ancestor', models.IntegerField(blank=True, null=True)),
                ('num_descendant', models.IntegerField(blank=True, null=True)),
                ('num_dir_descendant', models.IntegerField(blank=True, null=True)),
                ('notepad', models.CharField(default='', max_length=500)),
                ('created_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_date', models.DateTimeField(auto_now=True, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('family', models.ForeignKey(db_column='family', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='spcotfamily', to='common.family')),
                ('gen', models.ForeignKey(db_column='gen', default=0, on_delete=django.db.models.deletion.DO_NOTHING, related_name='poolgen', to='other.genus')),
            ],
        ),
        migrations.CreateModel(
            name='TestSpecies',
            fields=[
                ('pid', models.BigAutoField(primary_key=True, serialize=False)),
                ('genus', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='GenusRelation',
            fields=[
                ('gen', models.OneToOneField(db_column='gen', on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='other.genus')),
                ('genus', models.CharField(default='', max_length=50)),
                ('parentlist', models.CharField(max_length=500, null=True)),
                ('formula', models.CharField(max_length=500, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('binomial', models.CharField(blank=True, max_length=100, null=True)),
                ('credit_to', models.CharField(blank=True, max_length=100, null=True)),
                ('name', models.CharField(blank=True, max_length=100, null=True)),
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
                ('approved_by', models.ForeignKey(blank=True, db_column='approved_by', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='othvideoapproved_by', to=settings.AUTH_USER_MODEL)),
                ('author', models.ForeignKey(db_column='author', on_delete=django.db.models.deletion.DO_NOTHING, related_name='othvideoauthor', to='accounts.photographer')),
                ('family', models.ForeignKey(db_column='family', on_delete=django.db.models.deletion.DO_NOTHING, related_name='othvideofamily', to='common.family')),
                ('pid', models.ForeignKey(db_column='pid', on_delete=django.db.models.deletion.DO_NOTHING, related_name='othvideopid', to='other.species')),
                ('user_id', models.ForeignKey(blank=True, db_column='user_id', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='othvideouser_id', to=settings.AUTH_USER_MODEL)),
            ],
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
            name='SpcImages',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('binomial', models.CharField(blank=True, max_length=100, null=True)),
                ('credit_to', models.CharField(blank=True, max_length=100, null=True)),
                ('status', models.CharField(default='TBD', max_length=10)),
                ('quality', models.IntegerField(choices=[(1, 'Top'), (2, 'High'), (3, 'Average'), (4, 'Low')], default=3)),
                ('name', models.CharField(blank=True, max_length=100, null=True)),
                ('source_url', models.CharField(blank=True, max_length=1000, null=True)),
                ('image_url', models.CharField(blank=True, max_length=500, null=True)),
                ('text_data', models.TextField(blank=True, null=True)),
                ('certainty', models.CharField(blank=True, max_length=20, null=True)),
                ('rank', models.IntegerField(choices=[(0, '0'), (1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '6'), (7, '7'), (8, '8'), (9, '9')], default=5)),
                ('form', models.CharField(blank=True, max_length=50, null=True)),
                ('source_file_name', models.CharField(blank=True, max_length=100, null=True)),
                ('description', models.CharField(blank=True, max_length=100, null=True)),
                ('variation', models.CharField(blank=True, max_length=50, null=True)),
                ('location', models.CharField(blank=True, max_length=100, null=True)),
                ('type', models.CharField(blank=True, max_length=20, null=True)),
                ('image_file', models.CharField(blank=True, max_length=100, null=True)),
                ('image_file_path', models.ImageField(blank=True, null=True, upload_to='utils/images/photos')),
                ('download_date', models.DateField(blank=True, null=True)),
                ('genus', models.CharField(max_length=50)),
                ('species', models.CharField(blank=True, max_length=50, null=True)),
                ('block_id', models.IntegerField(blank=True, null=True)),
                ('created_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_date', models.DateTimeField(auto_now=True, null=True)),
                ('approved_by', models.ForeignKey(blank=True, db_column='approved_by', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='poolapproved_by', to=settings.AUTH_USER_MODEL)),
                ('author', models.ForeignKey(db_column='author', on_delete=django.db.models.deletion.DO_NOTHING, related_name='poolspcauthor', to='accounts.photographer')),
                ('family', models.ForeignKey(db_column='family', on_delete=django.db.models.deletion.DO_NOTHING, related_name='poolspcfamily', to='common.family')),
                ('gen', models.ForeignKey(blank=True, db_column='gen', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='poolspcgen', to='other.genus')),
                ('pid', models.ForeignKey(db_column='pid', on_delete=django.db.models.deletion.DO_NOTHING, related_name='poolpid', to='other.species')),
                ('user_id', models.ForeignKey(blank=True, db_column='user_id', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='pooluser_id', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Synonym',
            fields=[
                ('spid', models.OneToOneField(db_column='spid', on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='cacspid', serialize=False, to='other.species')),
                ('comment', models.TextField(blank=True, null=True)),
                ('created_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_date', models.DateTimeField(auto_now=True, null=True)),
                ('acc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cacaccid', to='other.species', verbose_name='accepted genus')),
            ],
        ),
        migrations.CreateModel(
            name='Hybrid',
            fields=[
                ('pid', models.OneToOneField(db_column='pid', on_delete=django.db.models.deletion.DO_NOTHING, primary_key=True, serialize=False, to='other.species')),
                ('binomial', models.CharField(blank=True, max_length=150, null=True)),
                ('is_hybrid', models.CharField(blank=True, max_length=5, null=True)),
                ('author', models.CharField(blank=True, max_length=200, null=True)),
                ('seed_genus', models.CharField(blank=True, max_length=50, null=True)),
                ('seed_species', models.CharField(blank=True, max_length=50, null=True)),
                ('seed_type', models.CharField(blank=True, max_length=10, null=True)),
                ('pollen_genus', models.CharField(blank=True, max_length=50, null=True)),
                ('pollen_species', models.CharField(blank=True, max_length=50, null=True)),
                ('pollen_type', models.CharField(blank=True, max_length=10, null=True)),
                ('year', models.IntegerField(blank=True, null=True)),
                ('date', models.DateField(blank=True, null=True)),
                ('status', models.CharField(blank=True, max_length=20, null=True)),
                ('originator', models.CharField(blank=True, max_length=100, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('comment', models.TextField(blank=True, null=True)),
                ('history', models.TextField(blank=True, null=True)),
                ('culture', models.TextField(blank=True, null=True)),
                ('etymology', models.TextField(blank=True, null=True)),
                ('num_image', models.IntegerField(blank=True, null=True)),
                ('num_ancestor', models.IntegerField(blank=True, null=True)),
                ('num_species_ancestor', models.IntegerField(blank=True, null=True)),
                ('num_descendant', models.IntegerField(blank=True, null=True)),
                ('created_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_date', models.DateTimeField(auto_now=True, null=True)),
                ('gen', models.ForeignKey(db_column='gen', default=0, on_delete=django.db.models.deletion.DO_NOTHING, related_name='othhybgen', to='other.genus')),
                ('pollen_gen', models.ForeignKey(db_column='pollgen', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='othpollgen', to='other.genus')),
                ('pollen_id', models.ForeignKey(blank=True, db_column='pollen_id', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='othpollen_id', to='other.species')),
                ('seed_gen', models.ForeignKey(db_column='seedgen', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='othseedgen', to='other.genus')),
                ('seed_id', models.ForeignKey(blank=True, db_column='seed_id', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='othseed_id', to='other.species')),
                ('user_id', models.ForeignKey(blank=True, db_column='user_id', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='othuser_id1', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Gensyn',
            fields=[
                ('pid', models.OneToOneField(db_column='pid', on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='other.genus')),
                ('created_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_date', models.DateTimeField(auto_now=True, null=True)),
                ('acc', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='gen_id', to='other.genus', verbose_name='genus')),
            ],
        ),
        migrations.CreateModel(
            name='Distribution',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dist', models.ForeignKey(db_column='dist', default='', on_delete=django.db.models.deletion.DO_NOTHING, to='other.location')),
                ('pid', models.ForeignKey(db_column='pid', default='', on_delete=django.db.models.deletion.DO_NOTHING, related_name='othdist_pid', to='other.species')),
            ],
            options={
                'unique_together': {('pid', 'dist')},
            },
        ),
        migrations.CreateModel(
            name='Accepted',
            fields=[
                ('pid', models.OneToOneField(db_column='pid', on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='other.species')),
                ('binomial', models.CharField(max_length=150, null=True)),
                ('distribution', models.TextField(blank=True)),
                ('location', models.TextField(blank=True)),
                ('introduced', models.TextField(blank=True)),
                ('is_type', models.BooleanField(default=False, null=True)),
                ('physiology', models.CharField(blank=True, max_length=200, null=True)),
                ('url', models.CharField(blank=True, max_length=200, null=True)),
                ('url_name', models.CharField(blank=True, max_length=100, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('common_name', models.CharField(blank=True, max_length=500, null=True)),
                ('common_name_search', models.CharField(blank=True, max_length=500, null=True)),
                ('local_name', models.CharField(blank=True, max_length=100, null=True)),
                ('bloom_month', models.CharField(blank=True, max_length=200, null=True)),
                ('size', models.CharField(blank=True, max_length=50, null=True)),
                ('color', models.CharField(blank=True, max_length=50, null=True)),
                ('fragrance', models.CharField(blank=True, max_length=50, null=True)),
                ('altitude', models.CharField(blank=True, max_length=50, null=True)),
                ('comment', models.TextField(blank=True, null=True)),
                ('etymology', models.TextField(blank=True, null=True)),
                ('culture', models.TextField(blank=True, null=True)),
                ('subgenus', models.CharField(blank=True, max_length=50, null=True)),
                ('section', models.CharField(blank=True, max_length=50, null=True)),
                ('subsection', models.CharField(blank=True, max_length=50, null=True)),
                ('series', models.CharField(blank=True, max_length=50, null=True)),
                ('num_image', models.IntegerField(blank=True, null=True)),
                ('num_descendant', models.IntegerField(blank=True, null=True)),
                ('created_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_date', models.DateTimeField(auto_now=True, null=True)),
                ('gen', models.ForeignKey(blank=True, db_column='gen', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='othgen_id', to='other.genus')),
                ('operator', models.ForeignKey(db_column='operator', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='othoperator', to=settings.AUTH_USER_MODEL)),
            ],
        ),
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
