import string
import re
import os
import logging
import random
import shutil

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.urls import reverse, reverse_lazy, resolve
from django.utils import timezone
from itertools import chain
import django.shortcuts
from django.apps import apps
from fuzzywuzzy import fuzz, process
from datetime import datetime, timedelta
from utils import config
from utils.views import write_output, getRole, paginator, get_author, get_family_list, getModels, pathinfo, get_random_sponsor
from core.models import Family, Subfamily, Tribe, Subtribe, Region, SubRegion
from orchidaceae.models import Genus, Subgenus, Section, Subsection, Series, Intragen, HybImages
from accounts.models import User, Photographer
from .forms import UploadFileForm, UploadSpcWebForm, UploadHybWebForm, AcceptedInfoForm, HybridInfoForm, \
    SpeciesForm, RenameSpeciesForm

epoch = 1740
logger = logging.getLogger(__name__)
GenusRelation = []
Accepted = []
Synonym = []
alpha_list = config.alpha_list
applications = config.applications

def getAllGenera():
    # Call this when Family is not provided
    OrGenus = apps.get_model('orchidaceae', 'Genus')
    OtGenus = apps.get_model('other', 'Genus')
    FuGenus = apps.get_model('fungi', 'Genus')
    return OrGenus, OtGenus


def getFamilyImage(family):
    SpcImages = apps.get_model(family.application, 'SpcImages')
    return SpcImages.objects.filter(rank__lt=7).order_by('-rank','quality', '?')[0:1][0]


def home(request):
    all_list = []
    role = getRole(request)
    num_samples = 4

    # Get a sample image of orchids
    SpcImages = apps.get_model('orchidaceae', 'SpcImages')
    orcimage = SpcImages.objects.filter(rank__lt=7).filter(rank__gt=0).order_by('-rank','quality', '?')[0:1][0]
    all_list = all_list + [['orchidaceae', orcimage]]

    # Get random other families
    SpcImages = apps.get_model('other', 'SpcImages')
    Genus = apps.get_model('other', 'Genus')
    sample_families = Genus.objects.filter(num_spcimage__gt=0).distinct().values_list('family', flat=True).order_by('?')[0:num_samples]
    for fam in sample_families:
        try:
            other_obj = SpcImages.objects.filter(family=fam).order_by('?')[0:1][0]
        except:
            continue
        all_list = all_list + [[other_obj.pid.family, other_obj]]

    # get random suculents
    sample_genus = Genus.objects.filter(is_succulent=True).filter(num_spcimage__gt=0).order_by('?')[0:1][0]
    try:
        succulent_obj = SpcImages.objects.filter(genus=sample_genus).order_by('?')[0:1][0]
    except:
        succulent_obj = ''
    all_list = all_list + [['Succulent', succulent_obj]]

    # get random carnivorous
    sample_genus = Genus.objects.filter(is_carnivorous=True).filter(num_spcimage__gt=0).order_by('?')[0:1][0]
    carnivorous_obj = SpcImages.objects.filter(genus=sample_genus).order_by('?')[0:1][0]
    all_list = all_list + [['Carnivorous', carnivorous_obj]]

    # get random parasitic
    sample_genus = Genus.objects.filter(is_parasitic=True).filter(num_spcimage__gt=0).order_by('?')[0:1][0]
    parasitic_obj = SpcImages.objects.filter(genus=sample_genus).order_by('?')[0:1][0]
    all_list = all_list + [['Parasitic', parasitic_obj]]

    num_samples = 1
    # Get random fungi families
    SpcImages = apps.get_model('fungi', 'SpcImages')
    Genus = apps.get_model('fungi', 'Genus')
    sample_families = Genus.objects.filter(num_spcimage__gt=0).distinct().values_list('family', flat=True).order_by('?')[0:num_samples]
    for fam in sample_families:
        try:
            fungi_obj = SpcImages.objects.filter(family=fam).order_by('?')[0:1][0]
        except:
            continue
        all_list = all_list + [["Fungi", fungi_obj]]

    num_samples = 1
    # Get random bird families
    SpcImages = apps.get_model('aves', 'SpcImages')
    Genus = apps.get_model('aves', 'Genus')
    sample_families = Genus.objects.filter(num_spcimage__gt=0).distinct().values_list('family', flat=True).order_by('?')[0:num_samples]
    for fam in sample_families:
        try:
            aves_obj = SpcImages.objects.filter(family=fam).order_by('?')[0:1][0]
        except:
            continue
        all_list = all_list + [["Aves", aves_obj]]

    num_samples = 1
    # Get random bird families
    SpcImages = apps.get_model('animalia', 'SpcImages')
    Genus = apps.get_model('animalia', 'Genus')
    sample_families = Genus.objects.filter(num_spcimage__gt=0).distinct().values_list('family', flat=True).order_by('?')[0:num_samples]
    for fam in sample_families:
        try:
            animalia_obj = SpcImages.objects.filter(family=fam).order_by('?')[0:1][0]
        except:
            continue
        all_list = all_list + [["Aves", animalia_obj]]

    # Advertisement
    num_blocks = 5
    ads_insert = int(random.random() * num_blocks) + 1
    sponsor = get_random_sponsor()
    random.shuffle(all_list)

    context = {'orcimage': orcimage, 'all_list': all_list, 'succulent_obj': succulent_obj,
               'carnivorous_obj': carnivorous_obj, 'parasitic_obj': parasitic_obj,
               'ads_insert': ads_insert, 'sponsor': sponsor, 'role': role }
    return render(request, 'home.html', context)


def require_get(view_func):
    def wrap(request, *args, **kwargs):
        if request.method != "GET":
            return HttpResponseBadRequest("Expecting GET request")
        return view_func(request, *args, **kwargs)
    wrap.__doc__ = view_func.__doc__
    wrap.__dict__ = view_func.__dict__
    wrap.__name__ = view_func.__name__
    return wrap

@login_required
def taxonomy(request):
    family_list, alpha = get_family_list(request)
    context = {'family_list': family_list,
               }
    return render(request, "common/taxonomy.html", context)

@login_required
def genera(request):
    myspecies = ''
    author = ''
    path = resolve(request.path).url_name
    app = request.GET['app']
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)

    family_list, alpha = get_family_list(request)
    if 'myspecies' in request.GET:
        myspecies = request.GET['myspecies']
        if myspecies:
            author = Photographer.objects.get(user_id=request.user)
    if family:
        if subtribe:
            genus_list = Genus.objects.filter(subtribe=subtribe)
        elif tribe:
            genus_list = Genus.objects.filter(tribe=tribe)
        elif subfamily:
            genus_list = Genus.objects.filter(subfamily=subfamily)
        elif family:
            genus_list = Genus.objects.filter(family=family)
    else:
        # No family (e.g. first landing on this page), show all non-Orchidaceae genera
        OrGenus, OtGenus = getAllGenera()
        if alpha:
            fam_list = family_list.values_list('family', flat=True)
            otgenus_list = OtGenus.objects.filter(family__in=fam_list)
        else:
            otgenus_list = OtGenus.objects.all()
        genus_list = otgenus_list
    # If private request
    if myspecies and author:
        pid_list = SpcImages.objects.filter(author_id=author).values_list('gen', flat=True).distinct()
        genus_list = genus_list.filter(pid__in=pid_list)


    # Complete building genus list
    # Define sort
    talpha = ''
    if 'talpha' in request.GET:
        talpha = request.GET['talpha']
    if talpha:
        genus_list = genus_list.filter(genus__istartswith=talpha)
    if request.GET.get('sort'):
        sort = request.GET['sort']
        sort.lower()

    total = len(genus_list)
    write_output(request, str(family))
    if genus_list:
        context = {
            'genus_list': genus_list,  'app': app, 'total':total, 'talpha': talpha,
            'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
            'family_list': family_list, 'myspecies': myspecies,
            'alpha_list': alpha_list, 'alpha': alpha,
            'path': path
        }
        return render(request, "common/genera.html", context)
    else:
        context = {
            'genus_list': genus_list,  'app': app, 'total':total, 'talpha': talpha,
            'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
            'family_list': family_list, 'myspecies': myspecies,
            'alpha_list': alpha_list, 'alpha': alpha,
            'path': path
        }
        return render(request, "common/family.html", context)


@login_required
def xspecies(request):
    # path = resolve(request.path).url_name
    myspecies = ''
    author = ''
    genus_obj = ''
    from_path = pathinfo(request)
    genus = ''
    talpha = ''
    path_link = 'information'
    if str(request.user) == 'chariya':
        path_link = 'photos'
    role = getRole(request)
    if 'app' in request.GET:
        app = request.GET['app']
        if not app:
            app = 'other'

    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    if 'genus' in request.GET:
        genus = request.GET['genus']
        if genus:
            try:
                genus_obj = Genus.objects.get(genus=genus)
            except Genus.DoesNotExist:
                genus_obj = ''
    if 'myspecies' in request.GET:
        myspecies = request.GET['myspecies']
        if myspecies:
            author = Photographer.objects.get(user_id=request.user)

    # If Orchidaceae, go to full table.
    if family and family.family == 'Orchidaceae':
        url = "%s?role=%s&family=%s" % (reverse('orchidaceae:species'), role, family)
        if genus_obj:
            url = url + "&genus=" + str(genus_obj)
        return HttpResponseRedirect(url)
    max_items = 3000

    syn = ''
    if 'syn' in request.GET:
        syn = request.GET['syn']

    if genus_obj:
        species_list = Species.objects.filter(type='species').filter(
            cit_status__isnull=True).exclude(cit_status__exact='').filter(genus=genus_obj)
        # new genus has been selected. Now select new species/hybrid
    elif from_path == 'research':
        species_list = []
    elif family and from_path != 'research':
        species_list = Species.objects.filter(type='species').filter(
            cit_status__isnull=True).exclude(cit_status__exact='')
        genus_list = Genus.objects.filter(family=family)
        if subtribe:
            genus_list = genus_list.filter(subtribe=subtribe)
        elif tribe:
            genus_list = genus_list.filter(tribe=tribe)
        elif subfamily:
            genus_list = genus_list.filter(subfamily=subfamily)
        genus_list = genus_list.values_list('genus', flat=True)
        species_list = species_list.filter(genus__in=genus_list)
    else:
        # app = 'other' or 'fungi'
        species_list = Species.objects.filter(type='species')
        species_list = species_list.filter(gen__family__application=app)

    if syn == 'N':
        species_list = species_list.exclude(status='synonym')
        syn = 'N'
    else:
        syn = 'Y'

    total_species = len(species_list)
    if 'talpha' in request.GET:
        talpha = request.GET['talpha']
    if talpha != '':
        species_list = species_list.filter(species__istartswith=talpha)
    if myspecies and author:
        pid_list = SpcImages.objects.filter(author_id=author).values_list('pid', flat=True).distinct()
        species_list = species_list.filter(pid__in=pid_list)


    total = len(species_list)
    msg = ''

    if total > max_items:
        species_list = species_list[0:max_items]
        msg = "List too long, truncated to " + str(max_items) + ". Please refine your search criteria."
        total = max_items

    write_output(request, str(family))
    context = {
        'genus': genus, 'species_list': species_list, 'app': app, 'total':total, 'syn': syn, 'max_items': max_items,
        'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe, 'role': role,
        'alpha_list': alpha_list, 'talpha': talpha, 'myspecies': myspecies, 'total_species': total_species,
        'msg': msg, 'path_link': path_link, 'from_path': 'species',
    }
    return render(request, "common/species.html", context)

def species(request):
    # path = resolve(request.path).url_name
    myspecies = ''
    syn = ''
    type = ''
    talpha = ''
    req_genus = ''
    req_family = ''
    path_link = 'information'
    if str(request.user) == 'chariya':
        path_link = 'photos'
    if 'type' in request.GET:
        req_type = request.GET['type']
    if 'family' in request.GET:
        req_family = request.GET['family']
    if 'genus' in request.GET:
        req_genus = request.GET['genus']
        print("req_genus = ", req_genus)
    if 'myspecies' in request.GET:
        myspecies = request.GET['myspecies']
        if myspecies:
            author = Photographer.objects.get(user_id=request.user)
    if 'talpha' in request.GET:
        talpha = request.GET['talpha']
    if 'syn' in request.GET:
        syn = request.GET['syn']

    # If Orchidaceae, go to full table.
    if req_family == 'Orchidaceae':
        if req_type == 'hybrid':
            url = "%s?family=%s&genus=%s&type=hybrid" % (reverse('orchidaceae:hybrid'), req_family, req_genus)
        else:
            url = "%s?family=%s&genus=%s&type=species" % (reverse('orchidaceae:species'), req_family, req_genus)

        return HttpResponseRedirect(url)
    max_items = 3000
    genus_list = []
    species_list = []
    if req_family:
        try:
            req_family = Family.objects.get(family=req_family)
            app = req_family.application
        except Family.DoesNotExist:
            app = ''
            req_family = ''
    if req_family and req_family != '':
        Genus = apps.get_model(app, 'Genus')
        Species = apps.get_model(app, 'Species')
        if req_genus != '':
            try:
                req_genus = Genus.objects.get(genus=req_genus)
            except Genus.DoesNotExist:
                req_genus = ''
            if req_genus != '':
                species_list = Species.objects.filter(genus=req_genus).filter(family=req_family)
                if req_type != '':
                    species_list = species_list.filter(type=req_type)
                if talpha != '':
                    species_list = species_list.filter(species__istartswith=talpha)
                if syn == 'N':
                    species_list = species_list.exclude(status='synonym')
                    syn = 'N'
                else:
                    syn = 'Y'
        if req_genus == '':
            # If requested genus in not valid return list of genera
            genus_list = Genus.objects.filter(family=req_family)
    elif req_genus != '':
        print("req_genus = ", req_genus)
        # Get list of req_genus species from all applications
        species_list = []
        for app in applications:
            print("app = ", app)
            # Go through all applications
            Genus = apps.get_model(app, 'Genus')
            Species = apps.get_model(app, 'Species')
            try:
                req_genus = Genus.objects.get(genus=req_genus)
                print("req_genus = ", req_genus)
            except Genus.DoesNotExist:
                continue
            species_list = None
            if req_genus != '':
                this_species_list = Species.objects.filter(genus=req_genus)
                if req_type != '':
                    this_species_list = this_species_list.filter(type=req_type)
                if talpha != '':
                    this_species_list = this_species_list.filter(species__istartswith=talpha)
                if syn == 'N':
                    this_species_list = this_species_list.exclude(status='synonym')
                    syn = 'N'
                else:
                    syn = 'Y'
                if this_species_list:
                    if not species_list:
                        species_list = this_species_list
                    else:
                        species_list = species_list.union(this_species_list)
                print("species_list = ", len(species_list))

    if not genus_list and not species_list:
        #     No filter requested, return empty list
        msg = 'select a valid family and/or a valid genus'
        context = {'msg': msg, 'path_link': path_link, 'from_path': 'species',}
        return render(request, "common/species.html", context)

    total = len(species_list)
    msg = ''

    if total > max_items:
        species_list = species_list[0:max_items]
        msg = "List too long, truncated to " + str(max_items) + ". Please refine your search criteria."
        total = max_items

    write_output(request, str(req_family))
    context = {
        'genus': req_genus, 'genus_list': genus_list, 'species_list': species_list, 'app': app, 'total':total,
        'syn': syn, 'type': req_type,
        'family': req_family,
        # 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe, 'role': role,
        'alpha_list': alpha_list, 'talpha': talpha, 'myspecies': myspecies,
        'msg': msg, 'path_link': path_link, 'from_path': 'species',
    }
    return render(request, "common/species.html", context)

@login_required
def hybrid(request):
    myspecies = ''
    author = ''
    path = resolve(request.path).url_name
    path = 'genera'
    genus = ''
    talpha = ''
    role = getRole(request)
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    if 'genus' in request.GET:
        genus = request.GET['genus']
    if genus:
        try:
            genus = Genus.objects.get(genus=genus)
        except Genus.DoesNotExist:
            genus = ''
    if family and family.family == 'Orchidaceae':
        url = "%s?role=%s&family=%s" % (reverse('orchidaceae:hybrid'), role, family)
        if genus:
            url = url + "&genus=" + str(genus)
        return HttpResponseRedirect(url)
    if 'myspecies' in request.GET:
        myspecies = request.GET['myspecies']
        if myspecies:
            author = Photographer.objects.get(user_id=request.user)

    hybrid_list = []
    syn = ''
    primary = ''
    msg = ''
    max_items = 3000

    if 'syn' in request.GET:
        syn = request.GET['syn']
    if 'primary' in request.GET:
        primary = request.GET['primary']
    if genus:
        hybrid_list = Species.objects.filter(type='hybrid').filter(genus=genus)
    elif family:
        hybrid_list = Species.objects.filter(type='hybrid')
        genus_list = Genus.objects.filter(family=family)
        if subtribe:
            genus_list = genus_list.filter(subtribe=subtribe)
        elif tribe:
            genus_list = genus_list.filter(tribe=tribe)
        elif subfamily:
            genus_list = genus_list.filter(subfamily=subfamily)
        genus_list = genus_list.values_list('genus', flat=True)
        hybrid_list = hybrid_list.filter(genus__in=genus_list)
    else:
        hybrid_list = Species.objects.filter(type='hybrid')


    if syn == 'N':
        hybrid_list = hybrid_list.exclude(status='synonym')
        syn = 'N'
    else:
        syn = 'Y'
    if primary == 'Y':
        hybrid_list = hybrid_list.filter(hybrid__seed_type='species').filter(hybrid__pollen_type='species')
        primary = 'Y'
    else:
        primary = 'N'

    if 'talpha' in request.GET:
        talpha = request.GET['talpha']
    if talpha != '':
        hybrid_list = hybrid_list.filter(species__istartswith=talpha)
    if myspecies and author:
        if family and family.family == 'Orchidaceae':
            pid_list = HybImages.objects.filter(author_id=author).values_list('pid', flat=True).distinct()
        else:
            pid_list = SpcImages.objects.filter(author_id=author).values_list('pid', flat=True).distinct()
        hybrid_list = hybrid_list.filter(pid__in=pid_list)

    total = len(hybrid_list)
    if total > max_items:
        hybrid_list = hybrid_list[0:max_items]
        msg = "List too long. Only show first " + str(max_items) + " items"
        total = max_items
    write_output(request, str(family))
    context = {
        'genus': genus, 'hybrid_list': hybrid_list, 'app': app, 'total':total, 'syn': syn, 'max_items': max_items,
        'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe, 'role': role,
        'alpha_list': alpha_list, 'talpha': talpha, 'myspecies': myspecies,
        'msg': msg, 'path': path, 'primary': primary,
    }
    return render(request, "common/hybrid.html", context)


@login_required
def uploadfile(request, pid):
    if request.user.tier.tier < 2 or not request.user.photographer.author_id:
        message = 'You dont have access to upload files. Please update your profile to gain access. ' \
                  'Or contact admin@orchidroots.org'
        return HttpResponse(message)
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    role = getRole(request)

    author, author_list = get_author(request)
    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        message = 'This name does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)
    app = species.gen.family.application
    if species.status == 'synonym':
        synonym = Synonym.objects.get(pk=pid)
        pid = synonym.acc_id
        species = Species.objects.get(pk=pid)
    role = getRole(request)
    form = UploadFileForm(initial={'author': request.user.photographer.author_id, 'role': role})
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            write_output(request, species.textname())
            spc = form.save(commit=False)
            if isinstance(species, Species):
                spc.pid = species.pid
            spc.family = family
            spc.type = species.type
            spc.user_id = request.user
            spc.text_data = spc.text_data.replace("\"", "\'\'")
            spc.save()
            url = "%s?role=%s&family=%s" % (reverse('display:photos', args=(species.pid,)), role, species.gen.family)
            return HttpResponseRedirect(url)
        else:
            return HttpResponse('save failed')

    context = {'form': form, 'species': species, 'web': 'active', 'family': species.gen.family,
               'author_list': author_list, 'author': author,
               'role': role, 'app': app,}
    return render(request, app + '/uploadfile.html', context)


@login_required
# This is not working.  Must define a different UploadSpcWebForm for each domain (Orchidaceae, Bromeliaceae, Other, etc...)
def uploadcommonweb(request, pid, orid=None):
    sender = 'web'
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    role = getRole(request)
    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        return HttpResponse(redirect_message)

    if request.method == 'POST':
        form = UploadSpcWebForm(request.POST)

        if form.is_valid():
            spc = form.save(commit=False)
            if not spc.author and not spc.credit_to:
                return HttpResponse("Please select an author, or enter a new name for credit allocation.")
            spc.user_id = request.user
            spc.pid = species
            spc.text_data = spc.text_data.replace("\"", "\'\'")
            if orid and orid > 0:
                spc.id = orid
            # set rank to 0 if private status is requested
            if spc.is_private is True or request.user.tier.tier < 3:
                spc.rank = 0

            # If new author name is given, set rank to 0 to give it pending status. Except curator (tier = 3)
            if spc.author.user_id and request.user.tier.tier < 3:
                if (spc.author.user_id.id != spc.user_id.id) or role == 'pri':
                    spc.rank = 0
            if spc.image_url == 'temp.jpg':
                spc.image_url = None
            if spc.image_file == 'None':
                spc.image_file = None
            if spc.created_date == '' or not spc.created_date:
                spc.created_date = timezone.now()
            spc.save()

            url = "%s?role=cur&family=%s" % (reverse('display:photos', args=(species.pid,)), species.gen.family)
            write_output(request, species.textname())
            return HttpResponseRedirect(url)

    if not orid:  # upload, initialize author. Get image count
        if species.type == 'species':
            form = UploadSpcWebForm(initial={'author': request.user.photographer.author_id})
        else:
            form = UploadHybWebForm(initial={'author': request.user.photographer.author_id})
        img = ''
    else:  # update. initialize the form iwht current image
        img = SpcImages.objects.get(pk=orid)
        if not img.image_url:
            sender = 'file'
            img.image_url = "temp.jpg"
        else:
            sender = 'web'
        form = UploadSpcWebForm(instance=img)

    context = {'form': form, 'img': img, 'sender': sender, 'loc': 'active',
               'species': species, 'family': family,
               'role': role, 'app': app,}
    return render(request, app + '/uploadweb.html', context)


def rank_update(request, SpcImages):
    rank = 0
    if 'rank' in request.GET:
        rank = request.GET['rank']
        rank = int(rank)
        if 'id' in request.GET:
            orid = request.GET['id']
            orid = int(orid)
            image = ''
            try:
                image = SpcImages.objects.get(pk=orid)
            except SpcImages.DoesNotExist:
                return 0
                # acc = Accepted.objects.get(pk=pid)
            image.rank = rank
            image.save()
    return rank


def quality_update(request, SpcImages):
    if request.user.is_authenticated and request.user.tier.tier > 2 and 'quality' in request.GET:
        quality = request.GET['quality']
        quality = int(quality)
        if 'id' in request.GET:
            orid = request.GET['id']
            orid = int(orid)
            image = ''
            try:
                image = SpcImages.objects.get(pk=orid)
            except SpcImages.DoesNotExist:
                return 3
            image.quality = quality
            image.save()
    return


def getphotolist(author, family, species, Species, UploadFile, SpcImages, HybImages):
    # Get species and hybrid lists that the user has at least one photo
    myspecies_list = Species.objects.exclude(status='synonym').filter(type='species')
    myhybrid_list = Species.objects.exclude(status='synonym').filter(type='hybrid')

    upl_list = list(UploadFile.objects.filter(author=author).values_list('pid', flat=True).distinct())
    spc_list = list(SpcImages.objects.filter(author=author).values_list('pid', flat=True).distinct())
    if app == 'orchidaceae' and species.type == 'hybrid':
        hyb_list = list(HybImages.objects.filter(author=author).values_list('pid', flat=True).distinct())
    else:
        hyb_list = []
    myspecies_list = myspecies_list.filter(Q(pid__in=upl_list) | Q(pid__in=spc_list)).order_by('genus', 'species')
    myhybrid_list = myhybrid_list.filter(Q(pid__in=upl_list) | Q(pid__in=hyb_list)).order_by('genus', 'species')

    if species:
        upload_list = UploadFile.objects.filter(author=author).filter(pid=species.pid)  # Private photos
        if app == 'orchidaceae' and species.type == 'hybrid':
            public_list = HybImages.objects.filter(pid=species.pid)  # public photos
        else:
            public_list = SpcImages.objects.filter(pid=species.pid)  # public photos

        private_list = public_list.filter(rank=0)  # rejected photos
        public_list  = public_list.filter(rank__gt=0)    # rejected photos
    else:
        private_list = public_list = upload_list = []

    return private_list, public_list, upload_list, myspecies_list, myhybrid_list


def getmyphotos(author, app, species, Species, UploadFile, SpcImages, HybImages, role):
    # Get species and hybrid lists that the user has at least one photo
    myspecies_list = Species.objects.exclude(status='synonym').filter(type='species')
    myhybrid_list = Species.objects.exclude(status='synonym').filter(type='hybrid')

    my_upl_list = list(UploadFile.objects.filter(author=author).values_list('pid', flat=True).distinct())
    my_spc_list = list(SpcImages.objects.filter(author=author).values_list('pid', flat=True).distinct())
    if app == 'orchidaceae':
        my_hyb_list = list(HybImages.objects.filter(author=author).values_list('pid', flat=True).distinct())
    else:
        my_hyb_list = []
    # list for dropdown select
    myspecies_list = myspecies_list.filter(Q(pid__in=my_upl_list) | Q(pid__in=my_spc_list)).order_by('genus', 'species')
    myhybrid_list = myhybrid_list.filter(Q(pid__in=my_upl_list) | Q(pid__in=my_hyb_list)).order_by('genus', 'species')

    # Get list for display
    if species:
        if app == 'orchidaceae' and species.type == 'hybrid':
            public_list = HybImages.objects.filter(pid=species.pid)  # public photos
        else:
            public_list = SpcImages.objects.filter(pid=species.pid)  # public photos
        upload_list = UploadFile.objects.filter(pid=species.pid)  # All upload photos
        private_list = public_list.filter(rank=0)  # rejected photos
        if role == 'pri':
            upload_list = upload_list.filter(author=author) # Private photos
            private_list = private_list.filter(author=author) # Private photos

        # Display all rank > 0 or rank = 0 if author matches
        public_list  = public_list.filter(Q(rank__gt=0) | Q(author=author))
    else:
        private_list = public_list = upload_list = []

    return private_list, public_list, upload_list, myspecies_list, myhybrid_list


def newbrowse(request):
    # Application must be in request
    display = ''
    family = ''
    talpha = ''
    if 'talpha' in request.GET:
        talpha = request.GET['talpha']

    # app must be in browse request
    app = request.GET['app']
    if 'family' in request.GET:
        family = request.GET['family']
    if app == 'orchidaceae':
        # Special case for orchids
        family = 'Orchidaceae'

    if app in applications:
        #     If app is requested, find family_list and sample image by family
        if 'display' in request.GET:
            display = request.GET['display']
        if not display:
            display = ''

        # If family is requested, get sample list by genera
        if 'genus' in request.GET:
            # App and family must also be in the request.
            Genus = apps.get_model(app.lower(), 'Genus')
            Species = apps.get_model(app.lower(), 'Species')
            genus = request.GET['genus']
            if genus:
                try:
                    genus = Genus.objects.get(genus=genus)
                except Genus.DoesNotExist:
                    Genus = ''
                if Genus:
                    species = Species.objects.filter(genus=genus)
                    if display == 'checked':
                        species = species.filter(num_image__gt=0)
                    if talpha:
                        species = species.filter(species__istartswith=talpha)
                    if len(species) > 500:
                        species = species[0: 500]
                    species = species.order_by('species')
                    species_list = []
                    for x in species:
                        spcimage = x.get_best_img()
                        if spcimage:
                            species_list = species_list + [spcimage]
                    context = {'species_list': species_list, 'family': genus.family, 'app': genus.family.application, 'genus': genus, 'display': display,  'talpha': talpha, 'alpha_list': alpha_list,}
                    return render(request, 'common/newbrowse.html', context)
        if family:
            try:
                family = Family.objects.get(family=family)
            except Family.DoesNotExist:
                family = None
            if family:
                Genus = apps.get_model(app.lower(), 'Genus')
                Species = apps.get_model(app.lower(), 'Species')
                genera = Genus.objects.filter(family=family)
                if talpha:
                    genera = genera.filter(genus__istartswith=talpha)
                genera = genera.order_by('genus')
                if len(genera) > 100:
                    genera = genera[0: 1000]
                genus_list = []
                for x in genera:
                    spcimage = Species.objects.filter(genus=x)
                    if display == 'checked':
                        spcimage = spcimage.filter(num_image__gt=0)
                    spcimage = spcimage.order_by('?')[0:1]
                    if len(spcimage) > 0:
                        genus_list = genus_list + [(spcimage[0], spcimage[0].get_best_img())]
                context = {'genus_list': genus_list, 'family': family, 'app': family.application, 'display': display,  'talpha': talpha, 'alpha_list': alpha_list,}
                return render(request, 'common/newbrowse.html', context)

        # Building sample by families
        families = Family.objects.filter(application=app)
        if talpha:
            families = families.filter(family__istartswith=talpha)
        families = families.order_by('family')
        Genus = apps.get_model(app.lower(), 'Genus')
        family_list = []
        for fam in families:
            genimage = Genus.objects.filter(family=fam.family)
            if display == 'checked':
                genimage = genimage.filter(num_spcimage__gt=0)
            genimage = genimage.order_by('?')[0:1]
            if len(genimage) > 0:
                family_list = family_list + [(genimage[0], genimage[0].get_best_img())]
        context = {'family_list': family_list, 'app': app, 'display': display, 'talpha': talpha, 'alpha_list': alpha_list,}
        return render(request, 'common/newbrowse.html', context)

    # Bad application, and neither families nor genus are valid, list all genera in the app
    write_output(request, str(family))
    return HttpResponseRedirect('/')

    # Now we get family_list of sample genera


def getPartialPid(reqgenus, type, status, app):
    if app == 'orchidaceae':
        Genus = apps.get_model(app.lower(), 'Genus')
        Species = apps.get_model(app.lower(), 'Species')
        Intragen = apps.get_model(app.lower(), 'Intragen')
        intragen_list = Intragen.objects.all()
        if status == 'synonym' or type == 'hybrid':
            intragen_list = []
    else:
        Genus = apps.get_model(app.lower(), 'Genus')
        Species = apps.get_model(app.lower(), 'Species')
        intragen_list = []

    pid_list = []
    pid_list = Species.objects.filter(type=type)
    pid_list = pid_list.exclude(status='synonym')

    if reqgenus:
        if reqgenus[0] != '*' and reqgenus[-1] != '*':
            try:
                genus = Genus.objects.get(genus=reqgenus)
            except Genus.DoesNotExist:
                genus = ''
            if genus:
                pid_list = pid_list.filter(genus=genus)
                if intragen_list:
                    intragen_list = intragen_list.filter(genus=genus)
            return genus, pid_list, intragen_list

        elif reqgenus[0] == '*' and reqgenus[-1] != '*':
            mygenus = reqgenus[1:]
            pid_list = pid_list.filter(genus__iendswith=mygenus)
            if intragen_list:
                intragen_list = intragen_list.filter(genus__iendswith=mygenus)

        elif reqgenus[0] != '*' and reqgenus[-1] == '*':
            mygenus = reqgenus[:-1]
            pid_list = pid_list.filter(genus__istartswith=mygenus)
            if intragen_list:
                intragen_list = intragen_list.filter(genus__istartswith=mygenus)
        elif reqgenus[0] == '*' and reqgenus[-1] == '*':
            mygenus = reqgenus[1:-1]
            pid_list = pid_list.filter(genus__icontains=mygenus)
            if intragen_list:
                intragen_list = intragen_list.filter(genus__icontains=mygenus)
    else:
        reqgenus = ''
    return reqgenus, pid_list, intragen_list


@login_required
def research(request):
    family = ''
    if 'family' in request.GET:
        family = request.GET['family']

    from_path = pathinfo(request)
    write_output(request, '')
    context = { 'family': family, 'from_path': from_path,}
    return render(request, "common/research.html", context)


def distribution(request):
    # For non-orchids only
    talpha = ''
    distribution = ''
    genus = ''
    commonname = ''
    crit = 0
    from_path = pathinfo(request)
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    if 'role' in request.GET:
        role = request.GET['role']
    else:
        role = 'pub'
    if 'family' in request.GET:
        reqfamily = request.GET['family']
        family = Family.objects.get(family=reqfamily)
        if family != '' and family.family != 'Orchidaceae':
            crit = 1
    if 'genus' in request.GET:
        reqgenus = request.GET['genus']
        try:
            genus = Genus.objects.get(genus=reqgenus)
            crit = 1
        except Genus.DoesNotExist:
            genus = ''
    if 'distribution' in request.GET:
        distribution = request.GET['distribution']
        if distribution != '': crit = 1
    if 'commonname' in request.GET:
        commonname = request.GET['commonname']
        if commonname != '': crit = 1

    species_list = []
    if crit:
        # initialize species_list if family is not orchidaceae
        if family != '' and family != 'Orchidaceae':            # Avoid large dataset in case of orchids
            species_list = Species.objects.filter(family=family)
        elif family != 'Orchidaceae':
            species_list = Species.objects.filter(family__application='other')

        # filter species list if Genus is requested
        if not genus:
            genus = ''
        if genus != '':
            if species_list:
                species_list = species_list.filter(genus=genus)
            else:
                # this is orchid case with a requested genus
                species_list = Species.objects.filter(genus=genus)
        if distribution:
            # build distribution list
            if family.family != 'Orchidaceae':
                dist_list = Distribution.objects.filter(dist_id__dist__icontains=distribution).values_list('pid', flat=True)
                species_list = Species.objects.filter(pid__in=dist_list)
            else:
                # Orchidaceae has a different Distribution class
                # Build distribution list
                dist_list = []
                subreg_list = SubRegion.objects.filter(name__icontains=distribution).values_list('code', flat=True)
                if len(subreg_list) > 0:
                    dist_list = Distribution.objects.filter(subregion_code__in=subreg_list).values_list('pid', flat=True)
                # requested distribution could elther be region or subregion
                reg_list = Region.objects.filter(name__icontains=distribution).values_list('id', flat=True)
                if len(reg_list) > 0:
                    dist_list = dist_list + Distribution.objects.filter(region_id__in=reg_list).values_list('pid', flat=True)
                dist_list = list(set(dist_list))

                # Filter species list
                if species_list:
                    species_list = species_list.filter(pid__in=dist_list)
                else:
                    species_list = Species.objects.filter(pid__in=dist_list)

        if commonname:
            name_list = Accepted.objects.filter(common_name__icontains=commonname).values_list('pid', flat=True)
            if species_list:
                species_list = species_list.filter(pid__in=name_list)
            else:
                # Orchidaceae with only common name requested
                species_list = Species.objects.filter(pid__in=name_list)
        if species_list:
            if 'talpha' in request.GET:
                talpha = request.GET['talpha']
            if talpha != '':
                species_list = species_list.filter(species__istartswith=talpha)
            species_list = species_list.order_by('species')
        total = len(species_list)
    context = {'species_list': species_list, 'distribution': distribution, 'commonname': commonname,
               'family': family, 'genus': genus,
               'role': role, 'app': 'other', 'talpha': talpha, 'alpha_list': alpha_list, 'from_path': from_path}
    write_output(request, str(distribution))
    return render(request, "common/distribution.html", context)


def mypaginator(request, full_list, page_length, num_show):
    page_list = []
    first_item = 0
    last_item = 0
    next_page = 0
    prev_page = 0
    last_page = 0
    page = 1
    page_range = ''
    total = len(full_list)
    if page_length > 0:
        paginator = Paginator(full_list, page_length)
        if 'page' in request.GET:
            page = request.GET.get('page', '1')
        else:
            page = 0
        if not page or page == 0:
            page = 1
        else:
            page = int(page)

        try:
            page_list = paginator.page(page)
            last_page = paginator.num_pages
            if page > last_page:
                page = last_page
        except EmptyPage:
            page_list = paginator.page(1)
            last_page = 1
        next_page = page+1
        if next_page > last_page:
            next_page = last_page
        prev_page = page - 1
        if prev_page < 1:
            prev_page = 1
        first_item = (page - 1) * page_length + 1
        last_item = first_item + page_length - 1
        if last_item > total:
            last_item = total
        # Get the index of the current page
        index = page_list.number - 1  # edited to something easier without index
        # This value is maximum index of your pages, so the last page - 1
        max_index = len(paginator.page_range)
        # You want a range of 7, so lets calculate where to slice the list
        start_index = index - num_show if index >= num_show else 0
        end_index = index + num_show if index <= max_index - num_show else max_index
        # My new page range
        page_range = paginator.page_range[start_index:end_index]
    return page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item


@login_required
def deletephoto(request, orid, pid):
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    next = ''

    try:
        image = UploadFile.objects.get(pk=orid)
    except UploadFile.DoesNotExist:
        message = 'This hybrid does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)

    try:
        species = Species.objects.get(pk=image.pid)
    except Species.DoesNotExist:
        message = 'This hybrid does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)

    if species.status == 'synonym':
        synonym = Synonym.objects.get(pk=species.pid)
        pid = synonym.acc_id
        species = Species.objects.get(pk=pid)

    upl = UploadFile.objects.get(id=orid)
    filename = os.path.join(settings.MEDIA_ROOT, str(upl.image_file_path))
    upl.delete()
    if 'next' in request.GET:
        next = request.GET['next']
    role = getRole(request)
    if next == 'photos':
        url = "%s?role=%s&family=%s" % (reverse('display:photos', args=(species.pid,)), role, family)
    else:
        url = "%s?role=%s&family=%s" % (reverse('common:curate_newupload'), role, family)

    # Finally remove file if exist
    if os.path.isfile(filename):
        os.remove(filename)

    write_output(request, str(family))
    return HttpResponseRedirect(url)


@login_required
def deletewebphoto(request, pid):
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    species = Species.objects.get(pk=pid)
    if species.status == 'synonym':
        synonym = Synonym.objects.get(pk=pid)
        pid = synonym.acc_id
        species = Species.objects.get(pk=pid)
    spc = ''

    if 'page' in request.GET:
        page = request.GET['page']
    else:
        page = "1"

    if 'id' in request.GET:
        orid = request.GET['id']
        orid = int(orid)

        if family.family == 'Orchidaceae' and species.type == 'hybrid':
            try:
                spc = HybImages.objects.get(id=orid)
            except HybImages.DoesNotExist:
                pass
        else:
            try:
                spc = SpcImages.objects.get(id=orid)
            except SpcImages.DoesNotExist:
                pass
        if spc:
            if spc.image_file:
                filename = os.path.join(settings.STATIC_ROOT, "utils/images/hybrid", str(spc.image_file))
                if os.path.isfile(filename):
                    os.remove(filename)
            spc.delete()
    days = 7
    area = ''
    role = getRole(request)
    if 'area' in request.GET:
        area = request.GET['area']
    if 'days' in request.GET:
        days = request.GET['days']
    if area == 'allpending':  # from curate_pending (all rank 0)
        url = "%s?role=%s&page=%s&type=%s&days=%s" % (reverse('detail:curate_pending'), role, page, type, days)
    else:
        url = "%s?role=%s&family=%s" % (reverse('display:photos', args=(species.pid,)), role, family)
    write_output(request, str(family))
    return HttpResponseRedirect(url)


@login_required
def approvemediaphoto(request, pid):
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    species = Species.objects.get(pk=pid)
    if species.status == 'synonym':
        synonym = Synonym.objects.get(pk=pid)
        pid = synonym.acc_id
        species = Species.objects.get(pk=pid)

    # Only curator can approve
    role = getRole(request)
    if role != "cur":
        message = 'You do not have privilege to approve photos.'
        return HttpResponse(message)

    if 'id' in request.GET:
        orid = request.GET['id']
        orid = int(orid)
    else:
        message = 'This photo does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)
    try:
        upl = UploadFile.objects.get(pk=orid)
    except UploadFile.DoesNotExist:
        msg = "uploaded file #" + str(orid) + "does not exist"
        url = "%s?role=%s&msg=%s&family=%s" % (reverse('display:photos', args=(species.pid,)), role, msg, family)
        return HttpResponseRedirect(url)
    upls = UploadFile.objects.filter(pid=pid)

    for upl in upls:
        old_name = os.path.join(settings.MEDIA_ROOT, str(upl.image_file_path))
        tmp_name = os.path.join("/webapps/static/tmp/", str(upl.image_file_path))

        filename, ext = os.path.splitext(str(upl.image_file_path))
        if family.family != 'Orchidaceae' or species.type == 'species':
            if family.family == 'Orchidaceae':
                spc = SpcImages(pid=species.accepted, author=upl.author, user_id=upl.user_id, name=upl.name, awards=upl.awards,
                            source_file_name=upl.source_file_name, variation=upl.variation, form=upl.forma, rank=0,
                            description=upl.description, location=upl.location, created_date=upl.created_date, source_url=upl.source_url)
            else:
                spc = SpcImages(pid=species, author=upl.author, user_id=upl.user_id, name=upl.name, awards=upl.awards,
                            source_file_name=upl.source_file_name, variation=upl.variation, form=upl.forma, rank=0,
                            description=upl.description, location=upl.location, created_date=upl.created_date, source_url=upl.source_url)
            spc.approved_by = request.user
            if family.family == 'Orchidaceae':
                newdir = os.path.join(settings.STATIC_ROOT, "utils/images/species")
            else:
                newdir = os.path.join(settings.STATIC_ROOT, "utils/images/" + str(family))

            image_file = "spc_"
        else:
            spc = HybImages(pid=species.hybrid, author=upl.author, user_id=upl.user_id, name=upl.name, awards=upl.awards,
                            source_file_name=upl.source_file_name, variation=upl.variation, form=upl.forma, rank=0,
                            description=upl.description, location=upl.location, created_date=upl.created_date, source_url=upl.source_url)
            spc.approved_by = request.user
            if family.family == 'Orchidaceae':
                newdir = os.path.join(settings.STATIC_ROOT, "utils/images/hybrid")
            else:
                newdir = os.path.join(settings.STATIC_ROOT, "utils/images/" + str(family))
            image_file = "hyb_"

        image_file = image_file + str(format(upl.pid, "09d")) + "_" + str(format(upl.id, "09d"))
        new_name = os.path.join(newdir, image_file)
        if not os.path.exists(new_name + ext):
            try:
                shutil.copy(old_name, tmp_name)
                shutil.move(old_name, new_name + ext)
            except shutil.Error:
                url = "%s?role=%s&family=%s" % (reverse('display:photos', args=(species.pid,)), role, family)
                return HttpResponseRedirect(url)
            spc.image_file = image_file + ext
        else:
            i = 1
            while True:
                image_file = image_file + "_" + str(i) + ext
                x = os.path.join(newdir, image_file)
                if not os.path.exists(x):
                    try:
                        shutil.copy(old_name, tmp_name)
                        shutil.move(old_name, x)
                    except shutil.Error:
                        upl.delete()
                        url = "%s?role=%s&family=%s" % (reverse('display:photos', args=(species.pid,)), role, family)
                        return HttpResponseRedirect(url)
                    spc.image_file = image_file
                    break
                i += 1

        spc.save()
        upl.approved = True
        upl.delete(0)
    write_output(request, str(family))
    url = "%s?role=%s&family=%s" % (reverse('display:photos', args=(species.pid,)), role, family)
    return HttpResponseRedirect(url)


@login_required
def myphoto(request, pid):
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    role = getRole(request)

    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        message = 'This hybrid does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)
    if not role or request.user.tier.tier < 2:
        url = "%s?role=%s&family=%s" % (reverse('display:information', args=(pid,)), role, species.gen.family)
        return HttpResponseRedirect(url)
    else:
        author, author_list = get_author(request)

    if species.status == 'synonym':
        synonym = Synonym.objects.get(pk=pid)
        pid = synonym.acc_id
        species = Species.objects.get(pk=pid)

    private_list, public_list, upload_list, myspecies_list, myhybrid_list = getmyphotos(author, app, species, Species, UploadFile, SpcImages, HybImages, role)
    author = Photographer.objects.get(user_id=request.user)
    if author:
        public_list = public_list.filter(author=author)
        private_list = private_list.filter(author=author)
    context = {'species': species, 'private_list': private_list, 'public_list': public_list, 'upload_list': upload_list,
               'myspecies_list': myspecies_list, 'myhybrid_list': myhybrid_list, 'author_list': author_list,
               'pri': 'active', 'role': role, 'author': author, 'family': family,
               'app': family.application,
               }
    write_output(request, str(family))
    return render(request, 'common/myphoto.html', context)


def myphoto_list(request):
    author, author_list = get_author(request)
    role = getRole(request)
    if 'family' in request.GET:
        family = request.GET['family']

    # If change family
    app_list = ['Orchidaceae', 'other', 'fungi', 'aves', 'animalia']
    my_hyb_list = []
    my_list = []
    if role == 'pub':
        return HttpResponseRedirect('/')
    if role == 'cur' and 'author' in request.GET:
        author = request.GET['author']
        author = Photographer.objects.get(pk=author)
    else:
        try:
            author = Photographer.objects.get(user_id=request.user)
        except Photographer.DoesNotExist:
            author = Photographer.objects.get(author_id='anonymous')
    if family:
        app_list = [family]

    for family in app_list:
    # for family in ['Orchidaceae']:
        Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request, family)
        # private_list, public_list, upload_list, myspecies_list, myhybrid_list = getmyphotos(author, app, '', Species, UploadFile, SpcImages, HybImages, role)
        my_tmp_list = Species.objects.exclude(status='synonym')

        my_upl_list = list(UploadFile.objects.filter(author=author).values_list('pid', flat=True).distinct())
        my_spc_list = list(SpcImages.objects.filter(author=author).values_list('pid', flat=True).distinct())
        if app == 'orchidaceae':
            my_hyb_list = list(HybImages.objects.filter(author=author).values_list('pid', flat=True).distinct())

        my_tmp_list = my_tmp_list.filter(Q(pid__in=my_upl_list) | Q(pid__in=my_spc_list) | Q(pid__in=my_hyb_list))
        if len(my_tmp_list) > 0:
            for x in my_tmp_list:
                x.family = x.gen.family
            my_tmp_list = my_tmp_list.values('pid', 'binomial', 'family', 'author', 'year', 'type')
            if (family and family.family == 'Orchidaceae') or len(app_list) == 1:
                my_list = my_tmp_list
            else:
                my_list = my_list.union(my_tmp_list)

    family_list, alpha = get_family_list(request)

    context = {'my_list': my_list, 'family': family, 'app': app,
               'my_list': my_list,
               'role': role, 'brwspc': 'active', 'author': author,
               'author_list': author_list,
               'family_list': family_list, 'alpha_list': alpha_list, 'alpha': alpha, 'mylist': 'active',
               }
    write_output(request, str(family))
    return render(request, 'common/myphoto_list.html', context)


@login_required
def myphoto_browse_spc(request):
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    author, author_list = get_author(request)
    role = getRole(request)

    if role == 'pub':
        return HttpResponseRedirect('/')
    if role == 'cur' and 'author' in request.GET:
        author = request.GET['author']
        author = Photographer.objects.get(pk=author)
    else:
        try:
            author = Photographer.objects.get(user_id=request.user)
        except Photographer.DoesNotExist:
            author = Photographer.objects.get(author_id='anonymous')

    private_list, public_list, upload_list, myspecies_list, myhybrid_list = getmyphotos(author, app, '', Species, UploadFile, SpcImages, HybImages, role)

    pid_list = SpcImages.objects.filter(author=author).values_list('pid', flat=True).distinct()

    img_list = Species.objects.filter(pid__in=pid_list)
    if img_list:
        img_list = img_list.order_by('genus', 'species')

    num_show = 5
    page_length = 20
    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item = mypaginator(
        request, img_list, page_length, num_show)

    my_list = []
    for x in page_list:
        img = x.get_best_img_by_author(request.user.photographer.author_id)
        if img:
            my_list.append(img)

    context = {'my_list': my_list, 'type': 'species', 'family': family, 'app': app,
               'myspecies_list': myspecies_list, 'myhybrid_list': myhybrid_list,
               'role': role, 'brwspc': 'active', 'author': author,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page, 'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'author_list': author_list,  'myspc': 'active',
               }
    write_output(request, str(family))
    return render(request, 'common/myphoto_browse_spc.html', context)


@login_required
def myphoto_browse_hyb(request):
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    if not family:
        family = 'other'
    role = getRole(request)
    if role == 'pub':
        return HttpResponseRedirect('/')
    author, author_list = get_author(request)
    if role == 'cur' and 'author' in request.GET:
        author = request.GET['author']
        author = Photographer.objects.get(pk=author)
    else:
        try:
            author = Photographer.objects.get(user_id=request.user)
        except Photographer.DoesNotExist:
            author = Photographer.objects.get(author_id='anonymous')

    private_list, public_list, upload_list, myspecies_list, myhybrid_list = getmyphotos(author, app, '', Species, UploadFile, SpcImages, HybImages, role)

    if family and family == 'other':
        pid_list = SpcImages.objects.filter(author=author).filter(gen__family__application='other').filter(pid__type='hybrid').values_list('pid', flat=True).distinct()
    else:
        if family.family == 'Orchidaceae':
            pid_list = HybImages.objects.filter(author=author).values_list('pid', flat=True).distinct()
        else:
            pid_list = SpcImages.objects.filter(author=author).filter(gen__family=family.family).filter(pid__type='hybrid').values_list('pid', flat=True).distinct()

    img_list = Species.objects.filter(pid__in=pid_list)
    if img_list:
        img_list = img_list.order_by('genus', 'species')

    num_show = 5
    page_length = 20
    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item = mypaginator(
        request, img_list, page_length, num_show)
    my_list = []
    for x in page_list:
        img = x.get_best_img_by_author(request.user.photographer.author_id)
        if img:
            my_list.append(img)

    context = {'my_list': my_list, 'type': 'hybrid', 'family': family, 'app': app,
               'myspecies_list': myspecies_list, 'myhybrid_list': myhybrid_list,
               'role': role, 'brwhyb': 'active', 'author': author,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page, 'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'author_list': author_list,
               }
    write_output(request, str(family))
    return render(request, 'common/myphoto_browse_hyb.html', context)


@login_required
def curate_newupload(request):
    if request.user.is_authenticated and request.user.tier.tier < 2:
        return HttpResponseRedirect('/')
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)

    file_list = UploadFile.objects.all().order_by('-created_date')
    days = 7
    num_show = 5
    page_length = 20
    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item = mypaginator(
        request, file_list, page_length, num_show)
    role = getRole(request)

    write_output(request, str(family))
    context = {'file_list': page_list, 'family': family,
               'tab': 'upl', 'role': role, 'upl': 'active', 'days': days,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page, 'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'app': app,
               }
    return render(request, "common/curate_newupload.html", context)


@login_required
def curate_pending(request):
    # This page is for curators to perform mass delete. It contains all rank 0 photos sorted by date reverse.
    if request.user.is_authenticated and request.user.tier.tier < 2:
        return HttpResponseRedirect('/')
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/login/')
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)

    ortype = ''
    if 'type' in request.GET:
        ortype = request.GET['type']
    if not ortype:
        ortype = 'species'

    days = 7
    if 'days' in request.GET:
        days = int(request.GET['days'])
    if not days:
        days = 7

    if ortype == 'hybrid' and family and family.family == 'Orchidaceae':
        file_list = SpcImages.objects.filter(rank=0).exclude(approved_by=1)
    else:
        file_list = HybImages.objects.filter(rank=0).exclude(approved_by=1)

    file_list = file_list.filter(modified_date__gte=timezone.now() - timedelta(days=days))
    if days >= 30:
        file_list = file_list.filter(modified_date__gte=timezone.now() - timedelta(days=days)).exclude(modified_date__gte=timezone.now() - timedelta(days=20))
    elif days >= 20:
        file_list = file_list.filter(modified_date__gte=timezone.now() - timedelta(days=days)).exclude(modified_date__gte=timezone.now() - timedelta(days=7))
    file_list = file_list.order_by('-created_date')

    num_show = 5
    page_length = 100
    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item = mypaginator(
        request, file_list, page_length, num_show)

    role = getRole(request)
    write_output(request, str(family))
    context = {'file_list': page_list, 'type': ortype, 'family': family,
               'tab': 'pen', 'role': role, 'pen': 'active', 'days': days,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page,
               'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'app': app,
               }
    return render(request, 'common/curate_pending.html', context)


@login_required
def curate_newapproved(request):
    # This page is for curators to perform mass delete. It contains all rank 0 photos sorted by date reverse.
    species = ''
    image = ''
    ortype = 'species'
    if request.user.is_authenticated and request.user.tier.tier < 2:
        return HttpResponseRedirect('/')

    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)

    if 'type' in request.GET:
        ortype = request.GET['type']
        # Request to change rank/quality
        if 'id' in request.GET:
            orid = int(request.GET['id'])
            try:
                image = SpcImages.objects.get(pk=orid)
            except SpcImages.DoesNotExist:
                species = ''
        if image:
            species = Species.objects.get(pk=image.pid_id)

    days = 3
    if 'days' in request.GET:
        days = int(request.GET['days'])
    file_list = SpcImages.objects.filter(rank__gt=0).exclude(approved_by=request.user)

    if days:
        file_list = file_list.filter(created_date__gte=timezone.now() - timedelta(days=days))
    file_list = file_list.order_by('-created_date')
    if species:
        rank_update(request, species)
        quality_update(request, species)

    num_show = 5
    page_length = 20
    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item = mypaginator(
        request, file_list, page_length, num_show)

    role = getRole(request)
    write_output(request, str(family))
    context = {'file_list': page_list, 'type': ortype, 'family': family,
               'tab': 'pen', 'role': role, 'pen': 'active', 'days': days,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page,
               'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'app': app,
               }
    return render(request, 'common/curate_newapproved.html', context)

