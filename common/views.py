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
from utils.views import write_output, getRole, paginator, get_author, get_family_list, getModels
from core.models import Family, Subfamily, Tribe, Subtribe
from orchidaceae.models import Subgenus, Section, Subsection, Series, Intragen, HybImages
from accounts.models import User, Photographer, Sponsor
from .forms import UploadFileForm, UploadSpcWebForm, UploadHybWebForm, AcceptedInfoForm, HybridInfoForm, \
    SpeciesForm, RenameSpeciesForm

epoch = 1740
alpha_list = string.ascii_uppercase
logger = logging.getLogger(__name__)
GenusRelation = []
Accepted = []
Synonym = []
alpha_list = config.alpha_list


def getAllGenera():
    # Call this when Family is not provided
    OrGenus = apps.get_model('orchidaceae', 'Genus')
    BrGenus = apps.get_model('bromeliaceae', 'Genus')
    CaGenus = apps.get_model('cactaceae', 'Genus')
    OtGenus = apps.get_model('other', 'Genus')
    return OrGenus, BrGenus, CaGenus, OtGenus


def getFamilyImage(family):
    SpcImages = apps.get_model(family.application, 'SpcImages')
    return SpcImages.objects.filter(rank__lt=7).filter(status='approved').order_by('-rank','quality', '?')[0:1][0]


def orchid_home(request):
    ads_insert = 0
    sponsor = ''

    role = getRole(request)
    if 'newfamily' in request.GET:
        family = request.GET['newfamily']

        url = "%s?role=%s&family=%s" % (reverse('common:genera'), role, family)
        return HttpResponseRedirect(url)

    num_samples = 5
    # 3 major families + succulent + carnivorous
    # (3 other families form the last row.)
    num_blocks = 5
    orcfamily = Family.objects.get(pk='Orchidaceae')
    orcimage = getFamilyImage(orcfamily)

    brofamily = Family.objects.get(pk='Bromeliaceae')
    broimage = getFamilyImage(brofamily)
    cacfamily = Family.objects.get(pk='Cactaceae')
    cacimage = getFamilyImage(cacfamily)

    # Get random other families
    SpcImages = apps.get_model('other', 'SpcImages')
    Genus = apps.get_model('other', 'Genus')
    sample_families = Genus.objects.filter(num_spcimage__gt=0).distinct().values_list('family', flat=True).order_by('?')[0:num_samples]
    other_list = []
    for fam in sample_families:
        try:
            other_obj = SpcImages.objects.filter(family=fam).order_by('?')[0:1][0]
        except:
            continue
        other_list.append(other_obj)
    del other_list[3:]
    # get random suculents
    sample_genus = Genus.objects.filter(is_succulent=True).filter(num_spcimage__gt=0).order_by('?')[0:1][0]
    try:
        succulent_obj = SpcImages.objects.filter(genus=sample_genus).order_by('?')[0:1][0]
    except:
        succulent_obj = ''

    ads_insert = int(random.random() * num_blocks) + 1
    sponsor = Sponsor.objects.filter(is_active=1).order_by('?')[0:1][0]

    # get random carnivorous
    sample_genus = Genus.objects.filter(is_carnivorous=True).filter(num_spcimage__gt=0).order_by('?')[0:1][0]
    carnivorous_obj = SpcImages.objects.filter(genus=sample_genus).order_by('?')[0:1][0]
    context = {'orcimage': orcimage, 'broimage': broimage, 'cacimage': cacimage,
               'other_list': other_list, 'succulent_obj': succulent_obj, 'carnivorous_obj': carnivorous_obj,
               'ads_insert': ads_insert, 'sponsor': sponsor,
                'title': 'orchid_home', 'role': role }
    return render(request, 'orchid_home.html', context)


def ode(request):
    author = 'JFowler'
    role = getRole(request)
    if 'newfamily' in request.GET:
        family = request.GET['newfamily']
        url = "%s?role=%s&family=%s" % (reverse('common:genera'), role, family)
        return HttpResponseRedirect(url)

    author = Photographer.objects.get(pk=author)
    OrSpcImg = apps.get_model('orchidaceae', 'SpcImages')
    OrHybImg = apps.get_model('orchidaceae', 'HybImages')
    BrImg = apps.get_model('bromeliaceae', 'SpcImages')
    CaImg = apps.get_model('cactaceae', 'SpcImages')
    OtImg = apps.get_model('other', 'SpcImages')

    or_spclist = OrSpcImg.objects.filter(author=author)
    or_Hyblist = OrHybImg.objects.filter(author=author)
    br_spclist = BrImg.objects.filter(author=author)
    ca_spclist = CaImg.objects.filter(author=author)
    ot_spclist = OtImg.objects.filter(author=author)

    context = {'author': author,
               'or_spclist': or_spclist,
               'or_Hyblist': or_Hyblist,
               'br_spclist': br_spclist,
               'ca_spclist': ca_spclist,
               'ot_spclist': ot_spclist,
               'title': 'ode', 'role': role }
    return render(request, 'ode.html', context)


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
def genera(request):
    path = resolve(request.path).url_name
    role = getRole(request)
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    family_list, alpha = get_family_list(request)

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
        # No family (e.g. first landing on this page), show all genera except Orchidaceae, Bromeliaceae and Cactaceae
        OrGenus, BrGenus, CaGenus, OtGenus = getAllGenera()
        # brgenus_list = BrGenus.objects.all().order_by('genus')
        # cagenus_list = CaGenus.objects.all().order_by('genus')
        if alpha:
            fam_list = family_list.values_list('family', flat=True)
            otgenus_list = OtGenus.objects.filter(family__in=fam_list)
        else:
            otgenus_list = OtGenus.objects.all()
        # orgenus_list = OrGenus.objects.all().order_by('genus')
        # genus_list = list(chain(otgenus_list, brgenus_list, cagenus_list)) #, orgenus_list))
        # genus_list = sorted(allgenus_list, key=operator.attrgetter('genus'))
        genus_list = otgenus_list
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
    context = {
        'genus_list': genus_list,  'app': app, 'total':total, 'talpha': talpha,
        'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe, 'role': role,
        'family_list': family_list,
        'title': 'taxonomy', 'alpha_list': alpha_list, 'alpha': alpha,
        'path': path
    }
    return render(request, "common/genera.html", context)


@login_required
def species(request):
    # path = resolve(request.path).url_name
    genus = ''
    talpha = ''
    alpha = ''
    path = 'information'
    if str(request.user) == 'chariya':
        path = 'photos'
    role = getRole(request)
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    if 'genus' in request.GET:
        genus = request.GET['genus']
        if genus:
            try:
                genus = Genus.objects.get(genus=genus)
            except Genus.DoesNotExist:
                genus = ''

    # If Orchidaceae, go to full table.
    if family and family.family == 'Orchidaceae':
        url = "%s?role=%s&family=%s" % (reverse('orchidaceae:species'), role, family)
        if genus:
            url = url + "&genus=" + str(genus)
        return HttpResponseRedirect(url)
    max_items = 3000

    syn = ''
    if 'syn' in request.GET:
        syn = request.GET['syn']

    if genus:
        species_list = Species.objects.filter(type='species').filter(
            cit_status__isnull=True).exclude(cit_status__exact='').filter(genus=genus)
        # new genus has been selected. Now select new species/hybrid
    elif family:
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
        # app = 'other'
        # Species = apps.get_model(app, 'Species')
        species_list = Species.objects.filter(type='species')
        # genus_list = Genus.objects.filter(family__application=app)
        # genus_list = genus_list.values_list('genus', flat=True)
        species_list = species_list.filter(gen__family__application=app)

    if syn == 'N':
        species_list = species_list.exclude(status='synonym')
        syn = 'N'
    else:
        syn = 'Y'
    if 'talpha' in request.GET:
        talpha = request.GET['talpha']
    if talpha != '':
        species_list = species_list.filter(species__istartswith=talpha)
    total = len(species_list)
    msg = ''

    if total > max_items:
        species_list = species_list[0:max_items]
        msg = "List too long, truncated to " + str(max_items) + ". Please refine your search criteria."
        total = max_items
    # if 'alpha' in request.GET:
    #     alpha = request.GET['alpha']
    # family_list, alpha = get_family_list(request)

    write_output(request, str(family))
    context = {
        'genus': genus, 'species_list': species_list, 'app': app, 'total':total, 'syn': syn, 'max_items': max_items,
        'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe, 'role': role,
        # 'family_list': family_list, 'alpha': alpha,
        'title': 'taxonomy', 'alpha_list': alpha_list, 'talpha': talpha,
        'msg': msg, 'path': path
    }
    return render(request, "common/species.html", context)


@login_required
def hybrid(request):
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
        # app = 'other'
        # Species = apps.get_model(app, 'Species')
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
    total = len(hybrid_list)
    # hybrid_list = hybrid_list.order_by('genus', 'species')
    if total > max_items:
        hybrid_list = hybrid_list[0:max_items]
        msg = "List too long. Only show first " + str(max_items) + " items"
        total = max_items
    # family_list, alpha = get_family_list(request)
    write_output(request, str(family))
    context = {
        'genus': genus, 'hybrid_list': hybrid_list, 'app': app, 'total':total, 'syn': syn, 'max_items': max_items,
        'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe, 'role': role,
        # 'family_list': family_list, 'alpha': alpha,
        'title': 'taxonomy', 'alpha_list': alpha_list, 'talpha': talpha,
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
               'role': role, 'app': app, 'title': 'uploadfile'}
    return render(request, app + '/uploadfile.html', context)


@login_required
def uploadcommonweb(request, pid, orid=None):
    sender = 'web'
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    role = getRole(request)
    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        return HttpResponse(redirect_message)

    if species.status == 'synonym':
        synonym = Synonym.objects.get(pk=pid)
        pid = synonym.acc_id
        species = Species.objects.get(pk=pid)

    if request.method == 'POST':
        form = UploadSpcWebForm(request.POST)

        if form.is_valid():
            print(">>> 2. form is valid")
            spc = form.save(commit=False)
            if not spc.author and not spc.credit_to:
                return HttpResponse("Please select an author, or enter a new name for credit allocation.")
            print(">>> spc.author = " + str(spc.author))
            print(">>> species.pid = " + str(species.pid))
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
               'role': role, 'app': app, 'title': 'uploadweb'}
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


def browse(request):
    app = ''
    talpha = ''
    num_show = 5
    page_length = 20
    ads_insert = 0
    sponsor = ''
    my_full_list = []
    if 'talpha' in request.GET:
        talpha = request.GET['talpha']
    if 'newfamily' in request.GET:
        family = request.GET['newfamily']
    elif 'family' in request.GET:
        family = request.GET['family']
    else:
        family = 'Orchidaceae'

    if family and family != 'other':
        family = Family.objects.get(family=family)
        app = family.application
    else:
        app = 'other'
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    # reqsubgenus = reqsection = reqsubsection = reqseries = ''
    # subgenus_obj = section_obj = subsection_obj = series_obj = ''
    # subgenus_list = section_list = subsection_list = series_list = []
    page_range = page_list = last_page = next_page = prev_page = page = first_item = last_item = total = ''
    display = ''
    seed_genus = pollen_genus = seed = pollen = ''
    reqgenus = ''
    group = ''
    # Get requested parameters
    role = getRole(request)
    if 'display' in request.GET:
        display = request.GET['display']
    if not display:
        display = ''
    if 'type' in request.GET:
        type = request.GET['type']
    else:
        type = 'species'
    if 'group' in request.GET:
        group = request.GET['group']
    # else:
    #     group = ''

    # if type == 'species':
    #     if 'subgenus' in request.GET:
    #         reqsubgenus = request.GET['subgenus']
    #         if reqsubgenus:
    #             try:
    #                 subgenus_obj = Subgenus.objects.get(pk=reqsubgenus)
    #             except Subgenus.DoesNotExist:
    #                 subgenus_obj = ''
    #     if 'section' in request.GET:
    #         reqsection = request.GET['section']
    #         if reqsection:
    #             try:
    #                 section_obj = Section.objects.get(pk=reqsection)
    #             except Section.DoesNotExist:
    #                 section_obj = ''
    #     if 'subsection' in request.GET:
    #         reqsubsection = request.GET['subsection']
    #         if reqsubsection:
    #             try:
    #                 subsection_obj = Subsection.objects.get(pk=reqsubsection)
    #             except Subsection.DoesNotExist:
    #                 subsection_obj = ''
    #     if 'series' in request.GET:
    #         reqseries = request.GET['series']
    #         if reqseries:
    #             try:
    #                 series_obj = Series.objects.get(pk=reqseries)
    #             except Series.DoesNotExist:
    #                 series_obj = ''
    if type == 'hybrid':
        if 'seed_genus' in request.GET:
            seed_genus = request.GET['seed_genus']
        if seed_genus == 'clear':
            seed_genus = ''
        if 'pollen_genus' in request.GET:
            pollen_genus = request.GET['pollen_genus']
        if pollen_genus == 'clear':
            pollen_genus = ''
        if 'seed' in request.GET:
            seed = request.GET['seed']
        if 'pollen' in request.GET:
            pollen = request.GET['pollen']
    if 'genus' in request.GET:
        reqgenus = request.GET['genus']
        if reqgenus == '------':
            reqgenus = ''

    # genus, pid_list, intragen_list = getPartialPid(reqgenus, type, 'accepted', app)

    if app == 'orchidaceae':
        Genus = apps.get_model(app.lower(), 'Genus')
        Species = apps.get_model(app.lower(), 'Species')
    else:
        Genus = apps.get_model(app.lower(), 'Genus')
        Species = apps.get_model(app.lower(), 'Species')

    pid_list = Species.objects.filter(type=type)
    # pid_list = pid_list.exclude(status='synonym')

    if subfamily:
        pid_list = pid_list.filter(gen__subfamily=subfamily)
    if subtribe:
        pid_list = pid_list.filter(gen__subtribe=subtribe)
    elif tribe:
        pid_list = pid_list.filter(gen__tribe=tribe)

    if reqgenus:
        try:
            genus = Genus.objects.get(genus=reqgenus)
        except Genus.DoesNotExist:
            genus = ''
        if genus:
            pid_list = pid_list.filter(genus=genus)
    else:
        reqgenus = ''
    if talpha:
        pid_list = pid_list.filter(species__istartswith=talpha)

    if pid_list and group:
        if group == 'succulent':
            pid_list = pid_list.filter(gen__is_succulent=True)
        elif group == 'carnivorous':
            pid_list = pid_list.filter(gen__is_carnivorous=True)

    if pid_list:
        if family:
            pid_list = pid_list.filter(gen__family=family.family)
        else:
            pid_list = pid_list.filter(gen__family__application='other')

        if display == 'checked':
            pid_list = pid_list.filter(num_image__gt=0)
        if type == 'species':
            pid_list = pid_list.filter(type='species')
        elif type == 'hybrid':
            pid_list = pid_list.filter(type='hybrid')
            if seed_genus and pollen_genus:
                pid_list = pid_list.filter(Q(hybrid__seed_genus=seed_genus) & Q(hybrid__pollen_genus=pollen_genus) | Q(
                        hybrid__seed_genus=pollen_genus) & Q(hybrid__pollen_genus=seed_genus))
            elif seed_genus:
                pid_list = pid_list.filter(Q(hybrid__seed_genus=seed_genus) | Q(hybrid__pollen_genus=seed_genus))
            elif pollen_genus:
                pid_list = pid_list.filter(Q(hybrid__seed_genus=pollen_genus) | Q(hybrid__pollen_genus=pollen_genus))
            if seed:
                pid_list = pid_list.filter(Q(hybrid__seed_species=seed) | Q(hybrid__pollen_species=seed))
            if pollen:
                pid_list = pid_list.filter(Q(hybrid__seed_species=pollen) | Q(hybrid__pollen_species=pollen))

        pid_list = pid_list.order_by('genus', 'species')
        total = len(pid_list)
        page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item \
            = mypaginator(request, pid_list, page_length, num_show)

        if len(page_list) > 5:
            ads_insert = int(random.random() * len(page_list)) + 1
            sponsor = Sponsor.objects.filter(is_active=1).order_by('?')[0:1][0]

        # if switch display, restart pagination
        if 'prevdisplay' in request.GET:
            page = 1

        for x in page_list:
            if x.get_best_img():
                if family and family.family == 'Orchidaceae':
                    if type == 'species':
                        x.image_dir = 'utils/images/species/'
                    else:
                        x.image_dir = 'utils/images/hybrid/'
                else:
                    x.image_dir = 'utils/images/' + str(x.gen.family) + '/'
                x.image_file = x.get_best_img().image_file
                my_full_list.append(x)
            else:
                x.image_file = 'utils/images/noimage_light.jpg'
                my_full_list.append(x)

    # family_list, alpha = get_family_list(request)
    genus_list = Genus.objects.all()
    if family:
        genus_list = genus_list.filter(family=family.family)
    if display == 'checked':
        if type == 'species':
            genus_list = genus_list.filter(num_spcimage__gt=0)
        else:
            genus_list = genus_list.filter(num_hybimage__gt=0)
    write_output(request, str(family))
    context = {'family':family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
        'page_list': my_full_list, 'type': type, 'genus': reqgenus, 'display': display, 'genus_list': genus_list,
        'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
        'page': page, 'total': total, 'talpha': talpha,
        'ads_insert': ads_insert, 'sponsor': sponsor,
        # 'family_list': family_list, 'alpha_list': alpha_list, 'alpha': alpha,
        'seed_genus': seed_genus, 'seed': seed, 'pollen_genus': pollen_genus, 'pollen': pollen,
        'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
        'title': 'browse', 'section': 'list', 'role': role,
    }

    return render(request, 'common/browse.html', context)


def search_orchid(request):
    # from itertools import chain
    Family = apps.get_model('core', 'Family')
    Genus = apps.get_model('orchidaceae', 'Genus')
    Species = apps.get_model('orchidaceae', 'Species')

    family = 'Orchidaceae'
    if 'family' in request.GET:
        family = request.GET['family']
    elif 'newfamily' in request.GET:
        family = request.GET['newfamily']

    role = 'pub'
    if 'role' in request.GET:
        role = request.GET['role']
    if 'spc_string' in request.GET:
        spc_string = request.GET['spc_string'].strip()
    else:
        spc_string = ''
    keyword = spc_string

    if family != 'Orchidaceae':
        url = "%s?role=%s&family=%s&spc_string=%s" % (
        reverse('common:search_species'), role, family, spc_string)
        return HttpResponseRedirect(url)
    genus = ''
    tail = ''
    spcount = ''
    y = ''
    search_list = ()
    partial_spc = ()
    partial_hyb = ()
    result_list = []
    spc_list = []
    hyb_list = []

    if request.user.is_authenticated:
        write_output(request, keyword)
    if keyword:
        rest = keyword.split(' ', 1)
        if len(rest) > 1:
            tail = rest[1]
        keys = keyword.split()
        if len(keys[0]) < 3 or keys[0].endswith('.'):
            keys = keys[1:]
            x = keys
        else:
            keyword = ' '.join(keys)
            x = keys[0]            # This could be genus or species (or hybrid)

        if len(x) > 7:
            x = x[: -2]  # Allow for some ending variation
        elif len(x) > 5:
            x = x[: -1]

        if len(keys) > 1:
            y = keys[1]            # This could be genus or species (or hybrid)

        if len(y) > 7:
            y = y[: -2]  # Allow for some ending variation
        elif len(y) > 5:
            y = y[: -1]

        if keys:
            genus = Genus.objects.filter(genus__iexact=keys[0])
            if len(genus) == 0:
                genus = ''
        else:
            genus = ''
        if genus and len(genus) > 0:
            genus = genus[0].genus
        else:
            genus = ''

        temp_list = Species.objects.exclude(status__iexact='pending')
        if spc_list:
            temp_list = temp_list.filter(pid__in=spc_list)
        if hyb_list:
            temp_list = temp_list.filter(pid__in=hyb_list)

        if len(keys) == 1:
            search_list = temp_list.filter(species__icontains=keys[0]).order_by('status', 'genus', 'species')
            mylist = search_list.values('pid')
            partial_spc = temp_list.filter(species__icontains=x).exclude(pid__in=mylist).order_by(
                'status', 'genus', 'species')

        elif len(keys) == 2:
            search_list = temp_list.filter(species__iexact=keys[1]).order_by('status', 'genus', 'species')
            mylist = search_list.values('pid')
            partial_spc = temp_list.filter(Q(species__icontains=x) | Q(infraspe__icontains=y)
                                           | Q(species__icontains=y)).exclude(pid__in=mylist).order_by(
                'status', 'genus', 'species')

        elif len(keys) == 3:
            search_list = temp_list.filter((Q(species__iexact=keys[0]) & Q(infraspe__iexact=keys[2])) |
                                           (Q(genus__iexact=keys[0]) & Q(species__iexact=keys[1]) &
                                            Q(infraspe__iexact=keys[2]))).order_by('status', 'genus', 'species')
            mylist = search_list.values('pid')
            partial_spc = temp_list.filter(Q(species__icontains=x) | Q(species__icontains=keys[1])).exclude(
                pid__in=mylist).order_by('status', 'genus', 'species')

        elif len(keys) >= 4:
            search_list = temp_list.filter((Q(species__iexact=keys[0]) & Q(infraspe__iexact=keys[2]))
                                           | (Q(genus__iexact=keys[0]) & Q(species__iexact=keys[1])
                                              & Q(infraspe__iexact=keys[2]))).order_by('status', 'genus', 'species')
            mylist = search_list.values('pid')
            partial_spc = temp_list.filter(Q(species__icontains=keys[1]) | Q(infraspe__icontains=keys[3])).exclude(
                pid__in=mylist).order_by('status', 'genus', 'species')
        spcount = len(search_list)

        all_list = list(chain(search_list, partial_hyb, partial_spc))
        for x in all_list:
            short_grex = x.short_grex().lower()
            score = fuzz.ratio(short_grex, keyword)     # compare against entire keyword
            if score < 60:
                score = fuzz.ratio(short_grex, keys[0])  # match against the first term after genus

            # if score < 100:
            grex = x.grex()
            score1 = fuzz.ratio(grex.lower(), keyword.lower())
            if score1 == 100:
                score1 = 200
            if score1 > score:
                score = score1
            if score >= 60:
                result_list.append([x, score])

    result_list.sort(key=lambda k: (-k[1], k[0].name()))
    family_list, alpha = get_family_list(request)
    family = Family.objects.get(pk='Orchidaceae')

    context = {'result_list': result_list, 'keyword': keyword, 'fuzzy': '1',
               'tail': tail, 'genus': genus, 'spcount': spcount, 'spc_string': spc_string,
               'family': family, 'family_list': family_list, 'alpha_list': alpha_list, 'alpha': alpha,
               'level': 'search_match', 'title': 'search_match', 'role': role, 'namespace': 'search', }
    return django.shortcuts.render(request, "common/search_orchid.html", context)


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


def get_species_list(application, family=None, subfamily=None, tribe=None, subtribe=None):
    Species = apps.get_model(application, 'Species')
    species_list = Species.objects.all()
    if subtribe:
        species_list = species_list.filter(gen__subtribe=subtribe)
    elif tribe:
        species_list = species_list.filter(gen__tribe=tribe)
    elif subfamily:
        species_list = species_list.filter(gen__subfamily=subfamily)
    return species_list
    # return species_list.values('pid', 'binomial', 'author', 'source', 'status', 'type', 'family')


def search_gen(request):
    min_score = 20
    genus_string = ''
    family = ''
    subfamily = ''
    tribe = ''
    subtribe = ''
    genus_list = []
    match_list = []
    perfect_list = []
    fuzzy_list = []
    fuzzy = ''
    if 'fuzzy' in request.GET:
        fuzzy = request.GET['fuzzy'].strip()
    # If no match found, perform fuzzy match

    role = getRole(request)
    if 'family' in request.GET:
        family = request.GET['family']
    elif 'newfamily' in request.GET:
        family = request.GET['newfamily']

    if family and family != 'other':
        family = Family.objects.get(pk=family)
        app = family.application
    else:
        family = ''
        app = 'other'
    # For other family search across all other families
    # if app == 'other':
    #     family = ''

    if 'spc_string' in request.GET:
        spc_string = request.GET['spc_string'].strip()
        if ' ' not in spc_string:
            genus_string = spc_string
    else:
        send_url = '/'
        return HttpResponseRedirect(send_url)

    # TODO:  WHERE IS THIS SENT TO????
    if not fuzzy and family and family.family == 'Orchidaceae':
        send_url = "%s?role=%s&app=orchidaceae&family=%s&spc_string=%s" % (reverse('common:search_special'), role, family, spc_string)
        return HttpResponseRedirect(send_url)

    # if suprageneric rank requested
    if 'subfamily' in request.GET:
        subfamily = request.GET['subfamily'].strip()
    if subfamily:
        subfamily = Subfamily.objects.get(subfamily=subfamily)
    if 'tribe' in request.GET:
        tribe = request.GET['tribe'].strip()
    if tribe:
        tribe = Tribe.objects.get(tribe=tribe)
    if 'subtribe' in request.GET:
        subtribe = request.GET['subtribe'].strip()
    if subtribe:
        subtribe = Subtribe.objects.get(subtribe=subtribe)


    spc = spc_string
    if family:
        if family.family == 'Cactaceae':
            species_list = get_species_list('cactaceae', family, subfamily, tribe, subtribe)
        elif family.family == 'Orchidaceae':
            species_list = get_species_list('orchidaceae', family, subfamily, tribe, subtribe)
        elif family.family == 'Bromeliaceae':
            species_list = get_species_list('bromeliaceae', family, subfamily, tribe, subtribe)
        else:
            species_list = get_species_list('other')
            species_list = species_list.filter(gen__family=family.family)
    else:
        # In case of app = other, search will scan through every family in the app.
        species_list = get_species_list('other')

    # Perform conventional match
    if not fuzzy:
        if genus_string:  # Seach genus table
            CaGenus = apps.get_model('cactaceae', 'Genus')
            OrGenus = apps.get_model('orchidaceae', 'Genus')
            OtGenus = apps.get_model('other', 'Genus')
            BrGenus = apps.get_model('bromeliaceae', 'Genus')
            genus_list = []
            cagenus_list = CaGenus.objects.all()
            cagenus_list = cagenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type',
                                               'description', 'num_species', 'num_hybrid')
            orgenus_list = OrGenus.objects.all()
            orgenus_list = orgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type',
                                               'description', 'num_species', 'num_hybrid')
            brgenus_list = BrGenus.objects.all()
            brgenus_list = brgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type',
                                               'description', 'num_species', 'num_hybrid')
            otgenus_list = OtGenus.objects.all()
            otgenus_list = otgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type',
                                               'description', 'num_species', 'num_hybrid')
            genus_list = cagenus_list.union(orgenus_list).union(otgenus_list).union(brgenus_list)
            search_list = []
            for x in genus_list:
                if x['genus']:
                    score = fuzz.ratio(x['genus'], genus_string)
                    if score >= min_score:
                        search_list.append([x, score])

            search_list.sort(key=lambda k: (-k[1], k[0]['genus']))
            del search_list[5:]
            genus_list = search_list

        # spc_string = spc_string.replace('.', '')
        spc_string = spc_string.replace(' mem ', ' Memoria ')
        words = spc_string.split()
        grex = spc_string.split(' ', 1)
        if len(grex) > 1:
            grex = grex[1]
        else:
             grex = grex[0]
        subgrex = grex.rsplit(' ', 1)[0]
        perfect_list = species_list.filter(binomial=spc_string)
        if len(perfect_list) == 0:
            if len(words) == 1:
                match_list = species_list.filter(Q(species__icontains=spc_string) | Q(infraspe__icontains=spc_string))
            else:
                match_list = species_list.filter(Q(binomial__icontains=spc_string) | Q(binomial__icontains=grex))
                # match_list = species_list.exclude(binomial=spc_string).filter(Q(binomial__icontains=spc_string) | Q(species__icontains=spc_string) | Q(species__icontains=grex) | Q(infraspe__icontains=words[-1]) | Q(binomial__icontains=grex) | Q(species__icontains=subgrex)  | Q(binomial__icontains=subgrex))
            if len(match_list) == 0:
                if not genus_list:
                    fuzzy = 1
                    url = "%s?role=%s&app=%s&family=%s&spc_string=%s&fuzzy=1" % (reverse('common:search_species'), role, app, family, spc_string)
                    return HttpResponseRedirect(url)

    # Perform Fuzzy search if requested (fuzzy = 1) or if no species match found:
    else:
        first_try = species_list.filter(species=spc)
        min_score = 60
        for x in species_list:
            if x.binomial:
                score = fuzz.ratio(x.binomial, spc)
                if score >= min_score:
                    fuzzy_list.append([x, score])
        fuzzy_list.sort(key=lambda k: (-k[1], k[0].binomial))
        del fuzzy_list[20:]
    path = 'information'
    if request.user == 'chariya':
        path = 'photos'
    family_list, alpha = get_family_list(request)

    write_output(request, spc_string)
    context = {'spc_string': spc_string, 'genus_list': genus_list,
               'perfect_list': perfect_list, 'match_list': match_list, 'fuzzy_list': fuzzy_list,
               'genus_total': len(genus_list), 'match_total': len(match_list), 'fuzzy_total': len(fuzzy_list), 'perfect_total': len(perfect_list),
               'family_list': family_list, 'family': family, 'alpha_list': alpha_list, 'alpha': alpha, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
               'app': app, 'fuzzy': fuzzy,
               'title': 'search', 'role': role, 'path': path}
    return django.shortcuts.render(request, "common/search_species.html", context)


def search_spc(request):
    min_score = 20
    genus_string = ''
    family = ''
    subfamily = ''
    tribe = ''
    subtribe = ''
    genus_list = []
    match_list = []
    perfect_list = []
    fuzzy_list = []
    fuzzy = ''
    if 'fuzzy' in request.GET:
        fuzzy = request.GET['fuzzy'].strip()
    # If no match found, perform fuzzy match

    role = getRole(request)
    if 'family' in request.GET:
        family = request.GET['family']
    elif 'newfamily' in request.GET:
        family = request.GET['newfamily']

    if family and family != 'other':
        family = Family.objects.get(pk=family)
        app = family.application
    else:
        family = ''
        app = 'other'
    # For other family search across all other families
    # if app == 'other':
    #     family = ''

    if 'spc_string' in request.GET:
        spc_string = request.GET['spc_string'].strip()
        if ' ' not in spc_string:
            genus_string = spc_string
    else:
        send_url = '/'
        return HttpResponseRedirect(send_url)

    if not fuzzy and family and family.family == 'Orchidaceae':
        send_url = "%s?role=%s&app=orchidaceae&family=%s&spc_string=%s" % (reverse('common:search_special'), role, family, spc_string)
        return HttpResponseRedirect(send_url)

    # if suprageneric rank requested
    if 'subfamily' in request.GET:
        subfamily = request.GET['subfamily'].strip()
    if subfamily:
        subfamily = Subfamily.objects.get(subfamily=subfamily)
    if 'tribe' in request.GET:
        tribe = request.GET['tribe'].strip()
    if tribe:
        tribe = Tribe.objects.get(tribe=tribe)
    if 'subtribe' in request.GET:
        subtribe = request.GET['subtribe'].strip()
    if subtribe:
        subtribe = Subtribe.objects.get(subtribe=subtribe)


    spc = spc_string
    if family:
        if family.family == 'Cactaceae':
            species_list = get_species_list('cactaceae', family, subfamily, tribe, subtribe)
        elif family.family == 'Orchidaceae':
            species_list = get_species_list('orchidaceae', family, subfamily, tribe, subtribe)
        elif family.family == 'Bromeliaceae':
            species_list = get_species_list('bromeliaceae', family, subfamily, tribe, subtribe)
        else:
            species_list = get_species_list('other')
            species_list = species_list.filter(gen__family=family.family)
    else:
        # In case of app = other, search will scan through every family in the app.
        species_list = get_species_list('other')

    # Perform conventional match
    if not fuzzy:
        if genus_string:  # Seach genus table
            CaGenus = apps.get_model('cactaceae', 'Genus')
            OrGenus = apps.get_model('orchidaceae', 'Genus')
            OtGenus = apps.get_model('other', 'Genus')
            BrGenus = apps.get_model('bromeliaceae', 'Genus')
            genus_list = []
            cagenus_list = CaGenus.objects.all()
            cagenus_list = cagenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type',
                                               'description', 'num_species', 'num_hybrid')
            orgenus_list = OrGenus.objects.all()
            orgenus_list = orgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type',
                                               'description', 'num_species', 'num_hybrid')
            brgenus_list = BrGenus.objects.all()
            brgenus_list = brgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type',
                                               'description', 'num_species', 'num_hybrid')
            otgenus_list = OtGenus.objects.all()
            otgenus_list = otgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type',
                                               'description', 'num_species', 'num_hybrid')
            genus_list = cagenus_list.union(orgenus_list).union(otgenus_list).union(brgenus_list)
            search_list = []
            for x in genus_list:
                if x['genus']:
                    score = fuzz.ratio(x['genus'], genus_string)
                    if score >= min_score:
                        search_list.append([x, score])

            search_list.sort(key=lambda k: (-k[1], k[0]['genus']))
            del search_list[5:]
            genus_list = search_list

        # spc_string = spc_string.replace('.', '')
        spc_string = spc_string.replace(' mem ', ' Memoria ')
        words = spc_string.split()
        grex = spc_string.split(' ', 1)
        if len(grex) > 1:
            grex = grex[1]
        else:
             grex = grex[0]
        subgrex = grex.rsplit(' ', 1)[0]
        perfect_list = species_list.filter(binomial=spc_string)
        if len(perfect_list) == 0:
            if len(words) == 1:
                match_list = species_list.filter(Q(species__icontains=spc_string) | Q(infraspe__icontains=spc_string))
            else:
                match_list = species_list.filter(Q(binomial__icontains=spc_string) | Q(binomial__icontains=grex))
                # match_list = species_list.exclude(binomial=spc_string).filter(Q(binomial__icontains=spc_string) | Q(species__icontains=spc_string) | Q(species__icontains=grex) | Q(infraspe__icontains=words[-1]) | Q(binomial__icontains=grex) | Q(species__icontains=subgrex)  | Q(binomial__icontains=subgrex))
            if len(match_list) == 0:
                if not genus_list:
                    fuzzy = 1
                    url = "%s?role=%s&app=%s&family=%s&spc_string=%s&fuzzy=1" % (reverse('common:search_species'), role, app, family, spc_string)
                    return HttpResponseRedirect(url)

    # Perform Fuzzy search if requested (fuzzy = 1) or if no species match found:
    else:
        first_try = species_list.filter(species=spc)
        min_score = 60
        for x in species_list:
            if x.binomial:
                score = fuzz.ratio(x.binomial, spc)
                if score >= min_score:
                    fuzzy_list.append([x, score])
        fuzzy_list.sort(key=lambda k: (-k[1], k[0].binomial))
        del fuzzy_list[20:]
    path = 'information'
    if request.user == 'chariya':
        path = 'photos'
    family_list, alpha = get_family_list(request)

    write_output(request, spc_string)
    context = {'spc_string': spc_string, 'genus_list': genus_list,
               'perfect_list': perfect_list, 'match_list': match_list, 'fuzzy_list': fuzzy_list,
               'genus_total': len(genus_list), 'match_total': len(match_list), 'fuzzy_total': len(fuzzy_list), 'perfect_total': len(perfect_list),
               'family_list': family_list, 'alpha_list': alpha_list, 'alpha': alpha, 'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
               'app': app, 'fuzzy': fuzzy,
               'title': 'search', 'role': role, 'path': path}
    return django.shortcuts.render(request, "common/search_species.html", context)


def search_hyb(request):
    min_score = 20
    genus_string = ''
    family = ''
    subfamily = ''
    tribe = ''
    subtribe = ''
    genus_list = []
    match_list = []
    perfect_list = []
    fuzzy_list = []
    fuzzy = ''
    if 'fuzzy' in request.GET:
        fuzzy = request.GET['fuzzy'].strip()
    # If no match found, perform fuzzy match

    role = getRole(request)
    if 'family' in request.GET:
        family = request.GET['family']
    elif 'newfamily' in request.GET:
        family = request.GET['newfamily']

    if family and family != 'other':
        family = Family.objects.get(pk=family)
        app = family.application
    else:
        family = ''
        app = 'other'
    # For other family search across all other families
    # if app == 'other':
    #     family = ''

    if 'spc_string' in request.GET:
        spc_string = request.GET['spc_string'].strip()
        if ' ' not in spc_string:
            genus_string = spc_string
    else:
        send_url = '/'
        return HttpResponseRedirect(send_url)

    if not fuzzy and family and family.family == 'Orchidaceae':
        send_url = "%s?role=%s&app=orchidaceae&family=%s&spc_string=%s" % (reverse('common:search_special'), role, family, spc_string)
        return HttpResponseRedirect(send_url)

    # if suprageneric rank requested
    if 'subfamily' in request.GET:
        subfamily = request.GET['subfamily'].strip()
    if subfamily:
        subfamily = Subfamily.objects.get(subfamily=subfamily)
    if 'tribe' in request.GET:
        tribe = request.GET['tribe'].strip()
    if tribe:
        tribe = Tribe.objects.get(tribe=tribe)
    if 'subtribe' in request.GET:
        subtribe = request.GET['subtribe'].strip()
    if subtribe:
        subtribe = Subtribe.objects.get(subtribe=subtribe)


    spc = spc_string
    if family:
        if family.family == 'Cactaceae':
            species_list = get_species_list('cactaceae', family, subfamily, tribe, subtribe)
        elif family.family == 'Orchidaceae':
            species_list = get_species_list('orchidaceae', family, subfamily, tribe, subtribe)
        elif family.family == 'Bromeliaceae':
            species_list = get_species_list('bromeliaceae', family, subfamily, tribe, subtribe)
        else:
            species_list = get_species_list('other')
            species_list = species_list.filter(gen__family=family.family)
    else:
        # In case of app = other, search will scan through every family in the app.
        species_list = get_species_list('other')

    # Perform conventional match
    if not fuzzy:
        if genus_string:  # Seach genus table
            CaGenus = apps.get_model('cactaceae', 'Genus')
            OrGenus = apps.get_model('orchidaceae', 'Genus')
            OtGenus = apps.get_model('other', 'Genus')
            BrGenus = apps.get_model('bromeliaceae', 'Genus')
            genus_list = []
            cagenus_list = CaGenus.objects.all()
            cagenus_list = cagenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type',
                                               'description', 'num_species', 'num_hybrid')
            orgenus_list = OrGenus.objects.all()
            orgenus_list = orgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type',
                                               'description', 'num_species', 'num_hybrid')
            brgenus_list = BrGenus.objects.all()
            brgenus_list = brgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type',
                                               'description', 'num_species', 'num_hybrid')
            otgenus_list = OtGenus.objects.all()
            otgenus_list = otgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type',
                                               'description', 'num_species', 'num_hybrid')
            genus_list = cagenus_list.union(orgenus_list).union(otgenus_list).union(brgenus_list)
            search_list = []
            for x in genus_list:
                if x['genus']:
                    score = fuzz.ratio(x['genus'], genus_string)
                    if score >= min_score:
                        search_list.append([x, score])

            search_list.sort(key=lambda k: (-k[1], k[0]['genus']))
            del search_list[5:]
            genus_list = search_list

        # spc_string = spc_string.replace('.', '')
        spc_string = spc_string.replace(' mem ', ' Memoria ')
        words = spc_string.split()
        grex = spc_string.split(' ', 1)
        if len(grex) > 1:
            grex = grex[1]
        else:
             grex = grex[0]
        subgrex = grex.rsplit(' ', 1)[0]
        perfect_list = species_list.filter(binomial=spc_string)
        if len(perfect_list) == 0:
            if len(words) == 1:
                match_list = species_list.filter(Q(species__icontains=spc_string) | Q(infraspe__icontains=spc_string))
            else:
                match_list = species_list.filter(Q(binomial__icontains=spc_string) | Q(binomial__icontains=grex))
                # match_list = species_list.exclude(binomial=spc_string).filter(Q(binomial__icontains=spc_string) | Q(species__icontains=spc_string) | Q(species__icontains=grex) | Q(infraspe__icontains=words[-1]) | Q(binomial__icontains=grex) | Q(species__icontains=subgrex)  | Q(binomial__icontains=subgrex))
            if len(match_list) == 0:
                if not genus_list:
                    fuzzy = 1
                    url = "%s?role=%s&app=%s&family=%s&spc_string=%s&fuzzy=1" % (reverse('common:search_species'), role, app, family, spc_string)
                    return HttpResponseRedirect(url)

    # Perform Fuzzy search if requested (fuzzy = 1) or if no species match found:
    else:
        first_try = species_list.filter(species=spc)
        min_score = 60
        for x in species_list:
            if x.binomial:
                score = fuzz.ratio(x.binomial, spc)
                if score >= min_score:
                    fuzzy_list.append([x, score])
        fuzzy_list.sort(key=lambda k: (-k[1], k[0].binomial))
        del fuzzy_list[20:]
    path = 'information'
    if request.user == 'chariya':
        path = 'photos'
    family_list, alpha = get_family_list(request)

    write_output(request, spc_string)
    context = {'spc_string': spc_string, 'genus_list': genus_list,
               'perfect_list': perfect_list, 'match_list': match_list, 'fuzzy_list': fuzzy_list,
               'genus_total': len(genus_list), 'match_total': len(match_list), 'fuzzy_total': len(fuzzy_list), 'perfect_total': len(perfect_list),
               'family_list': family_list, 'alpha_list': alpha_list, 'alpha': alpha, 'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
               'app': app, 'fuzzy': fuzzy,
               'title': 'search', 'role': role, 'path': path}
    return django.shortcuts.render(request, "common/search_species.html", context)


def search_match(request):
    # from itertools import chain
    genus = ''
    tail = ''
    y = ''
    min_score = 60
    qgenus = ''
    subfamily = ''
    tribe = ''
    subtribe = ''
    genus_string = ''
    search_list = ()
    partial_spc = ()
    partial_hyb = ()
    match_list = []
    spc_list = []
    hyb_list = []
    perfect_list = []
    genus_list = []
    Genus = apps.get_model('orchidaceae', 'Genus')
    Species = apps.get_model('orchidaceae', 'Species')
    if 'subfamily' in request.GET:
        subfamily = request.GET['subfamily'].strip()
    if subfamily:
        subfamily = Subfamily.objects.get(subfamily=subfamily)
    if 'tribe' in request.GET:
        tribe = request.GET['tribe'].strip()
    if tribe:
        tribe = Tribe.objects.get(tribe=tribe)
    if 'subtribe' in request.GET:
        subtribe = request.GET['subtribe'].strip()
    if subtribe:
        subtribe = Subtribe.objects.get(subtribe=subtribe)

    role = 'pub'
    if 'role' in request.GET:
        role = request.GET['role']

    if 'spc_string' in request.GET:
        spc_string = request.GET['spc_string'].strip()
    else:
        spc_string = ''
    if ' ' not in spc_string:
        genus_string = spc_string
        CaGenus = apps.get_model('cactaceae', 'Genus')
        OrGenus = apps.get_model('orchidaceae', 'Genus')
        OtGenus = apps.get_model('other', 'Genus')
        BrGenus = apps.get_model('bromeliaceae', 'Genus')
        genus_list = []
        cagenus_list = CaGenus.objects.all()
        cagenus_list = cagenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type',
                                           'description', 'num_species', 'num_hybrid')
        orgenus_list = OrGenus.objects.all()
        orgenus_list = orgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type',
                                           'description', 'num_species', 'num_hybrid')
        brgenus_list = BrGenus.objects.all()
        brgenus_list = brgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type',
                                           'description', 'num_species', 'num_hybrid')
        otgenus_list = OtGenus.objects.all()
        otgenus_list = otgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type',
                                           'description', 'num_species', 'num_hybrid')
        genus_list = cagenus_list.union(orgenus_list).union(otgenus_list).union(brgenus_list)
        search_list = []
        for x in genus_list:
            if x['genus']:
                score = fuzz.ratio(x['genus'], genus_string)
                if score >= min_score:
                    search_list.append([x, score])

        search_list.sort(key=lambda k: (-k[1], k[0]['genus']))
        del search_list[5:]
        genus_list = search_list

    keyword = spc_string
    if keyword:
        rest = keyword.split(' ', 1)
        if len(rest) > 1:
            tail = rest[1]
        keys = keyword.split()
        if len(keys[0]) < 3 or keys[0].endswith('.'):
            keys = keys[1:]
            x = keys
        else:
            keyword = ' '.join(keys)
            x = keys[0]            # This could be genus or species (or hybrid)

        if len(x) > 7:
            x = x[: -2]  # Allow for some ending variation
        elif len(x) > 5:
            x = x[: -1]

        if len(keys) > 1:
            y = keys[1]            # This could be genus or species (or hybrid)

        if len(y) > 7:
            y = y[: -2]  # Allow for some ending variation
        elif len(y) > 5:
            y = y[: -1]

        try:
            GenusRel = apps.get_model('orchidaceae', 'GenusRelation')
            genus = Genus.objects.filter(genus__iexact=keys[0])

        except Genus.DoesNotExist:
            try:
                genus = Genus.objects.filter(abrev__iexact=words[0])
            except Genus.DoesNotExist:
                qgenus = ''
        if genus:
            genus = genus[0]
            qgenlist = GenusRel.objects.filter(formula__icontains=genus.genus).values_list('genus', flat=True).distinct()
        else:
            qgenlist = []

        temp_list = Species.objects.exclude(status__iexact='pending')

        search_list = temp_list.filter(genus__in=qgenlist).filter(species__istartswith=tail)
        if len(search_list) > 0:
            mylist = search_list.values('pid')

        elif len(keys) == 1:
            search_list = temp_list.filter(species__icontains=keys[0])
            mylist = search_list.values('pid')
            partial_spc = temp_list.filter(species__icontains=x).exclude(pid__in=mylist)

        elif len(keys) == 2:
            search_list = temp_list.filter(species__iexact=keys[1])
            mylist = search_list.values('pid')
            partial_spc = temp_list.filter(Q(species__icontains=x) | Q(infraspe__icontains=y)
                                           | Q(species__icontains=y)).exclude(pid__in=mylist)

        elif len(keys) == 3:
            search_list = temp_list.filter((Q(species__iexact=keys[0]) & Q(infraspe__iexact=keys[2])) |
                                           (Q(genus__iexact=keys[0]) & Q(species__iexact=keys[1]) &
                                            Q(infraspe__iexact=keys[2])))
            mylist = search_list.values('pid')
            partial_spc = temp_list.filter(Q(species__icontains=x) | Q(species__icontains=keys[1])).exclude(
                pid__in=mylist)

        elif len(keys) >= 4:
            search_list = temp_list.filter((Q(species__iexact=keys[0]) & Q(infraspe__iexact=keys[2]))
                                           | (Q(genus__iexact=keys[0]) & Q(species__iexact=keys[1])
                                              & Q(infraspe__iexact=keys[2])))
            mylist = search_list.values('pid')
            partial_spc = temp_list.filter(Q(species__icontains=keys[1]) | Q(infraspe__icontains=keys[3])).exclude(
                pid__in=mylist)

        all_list = list(chain(search_list, partial_hyb, partial_spc))
        for x in all_list:
            short_grex = x.short_grex().lower()
            score = fuzz.ratio(short_grex, keyword)     # compare against entire keyword
            if score < 60:
                score = fuzz.ratio(short_grex, keys[0])  # match against the first term after genus

            # if score < 100:
            grex = x.grex()
            score1 = fuzz.ratio(grex.lower(), keyword.lower())
            if score1 == 100:
                score1 = 200
            if score1 > score:
                score = score1
            if score >= 60:
                match_list.append([x, score])
            # match_list.append([x, 0])

    match_list.sort(key=lambda k: (-k[1], k[0].name()))
    family_list, alpha = get_family_list(request)
    family = Family.objects.get(pk='Orchidaceae')
    write_output(request, spc_string)

    context = {'spc_string': spc_string, 'genus_list': genus_list,
               'perfect_list': perfect_list, 'match_list': match_list,
               'genus_total': len(genus_list), 'match_total': len(match_list), 'perfect_total': len(perfect_list),
               'family_list': family_list, 'alpha_list': alpha_list, 'alpha': alpha, 'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
               'app': 'orchidaceae', 'title': 'search', 'role': role, 'path': 'information'}
    return django.shortcuts.render(request, "common/search_match.html", context)


def search_fuzzy(request):
    min_score = 60
    spc_string = ''
    result_list = []
    result_score = []
    Family = apps.get_model('core', 'Family')
    Genus = apps.get_model('orchidaceae', 'Genus')
    Alliance = apps.get_model('orchidaceae', 'Alliance')
    Species = apps.get_model('orchidaceae', 'Species')

    family = 'Orchidaceae'
    if 'family' in request.GET:
        family = request.GET['family']
    elif 'newfamily' in request.GET:
        family = request.GET['newfamily']

    role = 'pub'
    if 'role' in request.GET:
        role = request.GET['role']

    if request.GET.get('spc_string'):
        spc_string = request.GET['spc_string'].strip()
    send_url = '/common/search_orchid/?spc_string=' + spc_string + "&role=" + role

    if family != 'Orchidaceae':
        url = "%s?role=%s&family=%s&spc_string=%s" % (
        reverse('common:search_species'), role, family, spc_string)
        return HttpResponseRedirect(url)

    grexlist = Species.objects.exclude(status='pending')
    # Filter for partner specific list.

    perfect_list = grexlist
    keyword = spc_string.lower()
    rest = keyword.split(' ', 1)

    if len(rest) > 1:
        # First get genus by name (could be abbrev.)
        genus = rest[0]
        abrev = genus
        if not genus.endswith('.'):
            abrev = genus + '.'
        # Then find genus in Genus class, start with accepted if exists.
        matched_gen = Genus.objects.filter(Q(genus=rest[0]) | Q(abrev=abrev)).order_by('status')

        if not matched_gen:
            return HttpResponseRedirect(send_url)

        # Genus found, get genus object
        genus_obj = matched_gen[0]
        keyword = rest[1]
        # If genus is a synonym, get accepted name
        if genus_obj.status == 'synonym':
            matched_gen = Genus.objects.filter(Q(genus=genus_obj.gensyn.acc_id) | Q(abrev=genus_obj.gensyn.acc.abrev))
            if matched_gen:
                genus_obj = matched_gen[0]
            else:
                # For synonym genus, use conventional search
                return HttpResponseRedirect(send_url)

        # Get alliance associated to the genus_obj
        alliance_obj = Alliance.objects.filter(gen=genus_obj.pid)
        if alliance_obj:
            # Then create genus_list of all genus associated to the alliance.
            genus_list = list(Alliance.objects.filter(alid=alliance_obj[0].alid.pid).values_list('gen'))

            # Then create the search space of species/hybrids in all genera associated to each alliances.
            grexlist = grexlist.filter(gen__in=genus_list)
        else:
            # If alliance does not exist, just search on the genus alone
            grexlist = grexlist.filter(gen=genus_obj.pid)
    else:
        return HttpResponseRedirect(send_url)

    # Compute fuzzy score for all species in grexlist
    for x in grexlist:
        # If the first word is genus hint, compare species and the tail
        score = fuzz.ratio(x.short_grex().lower(), keyword)
        if score >= min_score:
            result_list.append(x)
            result_score.append([x, score])

    # Add the perfect match and set score 100%.
    # At this point, the first word is related to a genus
    perfect_list = perfect_list.filter(species__iexact=rest[1])
    perfect_pid = perfect_list.values_list('pid', flat=True)

    for x in perfect_list:
        if x in result_list:
            result_list.remove(x)

    for i in range(len(result_score)):
        if genus_obj != '':
            if result_score[i][0].gen.pid == genus_obj.pid:
                if result_score[i][1] == 100:
                    result_score[i][1] = 200
    family_list, alpha = get_family_list(request)
    family = Family.objects.get(pk='Orchidaceae')

    result_score.sort(key=lambda k: (-k[1], k[0].name()))
    context = {'result_list': result_list,'result_score': result_score, 'len': len(result_list), 'spc_string':  spc_string, 'genus': genus,
               'alliance_obj': alliance_obj, 'genus_obj': genus_obj,
               'min_score': min_score, 'keyword': keyword,
               'family': family, 'family_list': family_list, 'alpha_list': alpha_list, 'alpha': alpha,
               'level': 'search', 'title': 'fuzzy', 'role': role, 'namespace': 'search',

               }
    return django.shortcuts.render(request, "common/search_orchid.html", context)


def search_species(request):
    min_score = 70
    genus_string = ''
    single_word = ''
    family = ''
    subfamily = ''
    tribe = ''
    subtribe = ''
    genus_list = []
    match_spc_list = []
    match_list = []
    perfect_list = []
    fuzzy_list = []
    fuzzy = ''
    if 'fuzzy' in request.GET:
        fuzzy = request.GET['fuzzy'].strip()
    # If no match found, perform fuzzy match

    if 'spc_string' in request.GET:
        spc_string = request.GET['spc_string'].strip()
        if ' ' not in spc_string:
            single_word = True
            genus_string = spc_string
        elif spc_string.split()[0]:
            genus_string = spc_string.split()[0]
    else:
        send_url = '/'
        return HttpResponseRedirect(send_url)

    role = getRole(request)
    if 'family' in request.GET:
        family = request.GET['family']
    elif 'newfamily' in request.GET:
        family = request.GET['newfamily']

    if family == 'Orchidaceae':
        url = "%s?role=%s&family=Orchidaceae&spc_string=%s" % (
        reverse('common:search_orchid'), role, spc_string)
        return HttpResponseRedirect(url)

    if family and family != 'other':
        family = Family.objects.get(pk=family)
        app = family.application
    else:
        family = ''
        app = 'other'
    # For other family search across all other families
    if app == 'other':
        family = ''

    # if suprageneric rank requested
    if 'subfamily' in request.GET:
        subfamily = request.GET['subfamily'].strip()
    if subfamily:
        subfamily = Subfamily.objects.get(subfamily=subfamily)
    if 'tribe' in request.GET:
        tribe = request.GET['tribe'].strip()
    if tribe:
        tribe = Tribe.objects.get(tribe=tribe)
    if 'subtribe' in request.GET:
        subtribe = request.GET['subtribe'].strip()
    if subtribe:
        subtribe = Subtribe.objects.get(subtribe=subtribe)

    spc = spc_string
    if family:
        if family.family == 'Cactaceae':
            species_list = get_species_list('cactaceae', family, subfamily, tribe, subtribe)
        elif family.family == 'Orchidaceae':
            species_list = get_species_list('orchidaceae', family, subfamily, tribe, subtribe)
        elif family.family == 'Bromeliaceae':
            species_list = get_species_list('bromeliaceae', family, subfamily, tribe, subtribe)
        else:
            species_list = get_species_list('other')
            species_list = species_list.filter(gen__family=family.family)
    else:
        # In case of app = other, search will scan through every family in the app.
        species_list = get_species_list('other')

    # Perform conventional match
    if not fuzzy:
        # exact match genus, and species from beginning of word
        if genus_string:  # Seach genus table
            min_score = 80
            # Try to match genus
            CaGenus = apps.get_model('cactaceae', 'Genus')
            OrGenus = apps.get_model('orchidaceae', 'Genus')
            OtGenus = apps.get_model('other', 'Genus')
            BrGenus = apps.get_model('bromeliaceae', 'Genus')
            cagenus_list = CaGenus.objects.all()
            cagenus_list = cagenus_list.values('pid', 'genus', 'family', 'author', 'description', 'num_species', 'num_hybrid', 'status', 'year')
            orgenus_list = OrGenus.objects.all()
            orgenus_list = orgenus_list.values('pid', 'genus', 'family', 'author', 'description', 'num_species', 'num_hybrid', 'status', 'year')
            brgenus_list = BrGenus.objects.all()
            brgenus_list = brgenus_list.values('pid', 'genus', 'family', 'author', 'description', 'num_species', 'num_hybrid', 'status', 'year')
            otgenus_list = OtGenus.objects.all()
            otgenus_list = otgenus_list.values('pid', 'genus', 'family', 'author', 'description', 'num_species', 'num_hybrid', 'status', 'year')
            genus_list = cagenus_list.union(orgenus_list).union(otgenus_list).union(brgenus_list)
            search_list = []
            for x in genus_list:
                if x['genus']:
                    score = fuzz.ratio(x['genus'].lower(), genus_string.lower())
                    if score >= min_score:
                        search_list.append([x, score])

            search_list.sort(key=lambda k: (-k[1], k[0]['genus']))
            del search_list[5:]
            genus_list = search_list
        if single_word:
            #Try to 0match species from all families
            CaSpecies = apps.get_model('cactaceae', 'Species')
            OrSpecies = apps.get_model('orchidaceae', 'Species')
            OtSpecies = apps.get_model('other', 'Species')
            BrSpecies = apps.get_model('bromeliaceae', 'Species')
            caspecies_list = CaSpecies.objects.filter(species__istartswith=spc_string)
            caspecies_list = caspecies_list.values('pid', 'species', 'family', 'genus', 'author', 'status', 'year')
            orspecies_list = OrSpecies.objects.filter(species__istartswith=spc_string)
            orspecies_list = orspecies_list.values('pid', 'species', 'family', 'genus', 'author', 'status', 'year')
            brspecies_list = BrSpecies.objects.filter(species__istartswith=spc_string)
            brspecies_list = brspecies_list.values('pid', 'species', 'family', 'genus', 'author', 'status', 'year')
            otspecies_list = OtSpecies.objects.filter(species__istartswith=spc_string)
            otspecies_list = otspecies_list.values('pid', 'species', 'family', 'genus', 'author', 'status', 'year')
            matched_species_list = caspecies_list.union(orspecies_list).union(otspecies_list).union(brspecies_list)
            for x in matched_species_list:
                if x['species']:
                    score = fuzz.ratio(x['species'].lower(), spc_string.lower())
                    if score >= min_score:
                        match_spc_list.append([x, score])
            match_spc_list.sort(key=lambda k: (-k[1], k[0]['species']))
            # del match_spc_list[5:]

        if not match_spc_list:
            # if no species found (single word) search binomial in other families
            spc_string = spc_string.replace('.', '')
            spc_string = spc_string.replace(' mem ', ' Memoria ')
            spc_string = spc_string.replace(' Mem ', ' Memoria ')
            spc_string = spc_string.replace(' mem. ', ' Memoria ')
            spc_string = spc_string.replace(' Mem. ', ' Memoria ')
            words = spc_string.split()
            grex = spc_string.split(' ', 1)
            if len(grex) > 1:
                grex = grex[1]
            else:
                grex = grex[0]
            # print("spc_string = " + spc_string)
            # print("grex = " + grex)
            if len(words) > 1:
                perfect_list = species_list.filter(binomial__istartswith=spc_string)
            # print("words = " + str(len(words)))
            # print("species_list = " + str(len(species_list)))
            # print("perfect_list = " + str(len(perfect_list)))
            if len(perfect_list) == 0:
                if len(words) == 1:
                    # Single word could be a genus or an epithet
                    match_list = species_list.filter(species__istartswith=grex)
                    # match_list = species_list.filter(species__icontains=grex)
                else:
                    match_list = species_list.filter(Q(binomial__icontains=grex) | Q(binomial__icontains=grex))
                    # match_list = species_list.exclude(binomial=spc_string).filter(Q(binomial__icontains=spc_string) | Q(species__icontains=spc_string) | Q(species__icontains=grex) | Q(infraspe__icontains=words[-1]) | Q(binomial__icontains=grex) | Q(species__icontains=subgrex)  | Q(binomial__icontains=subgrex))
                if len(match_list) == 0:
                    if not genus_list:
                        fuzzy = 1
                        url = "%s?role=%s&app=%s&family=%s&spc_string=%s&fuzzy=1" % (reverse('common:search_species'), role, app, family, spc_string)
                        return HttpResponseRedirect(url)

    # Perform Fuzzy search if requested (fuzzy = 1) or if no species match found:
    else:
        first_try = species_list.filter(species=spc)
        min_score = 60
        for x in species_list:
            if x.binomial:
                score = fuzz.ratio(x.binomial, spc)
                if score >= min_score:
                    fuzzy_list.append([x, score])
        fuzzy_list.sort(key=lambda k: (-k[1], k[0].binomial))
        del fuzzy_list[20:]
    path = 'information'
    if role == 'cur':
        path = 'photos'
    family_list, alpha = get_family_list(request)

    write_output(request, spc_string)
    context = {'spc_string': spc_string, 'genus_list': genus_list, 'match_spc_list': match_spc_list,
               'perfect_list': perfect_list, 'match_list': match_list, 'fuzzy_list': fuzzy_list,
               'genus_total': len(genus_list), 'match_total': len(match_list), 'fuzzy_total': len(fuzzy_list), 'perfect_total': len(perfect_list),
               'family_list': family_list, 'alpha_list': alpha_list, 'alpha': alpha, 'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
               'app': app, 'fuzzy': fuzzy, 'single_word': single_word,
               'title': 'search', 'role': role, 'path': path}
    return django.shortcuts.render(request, "common/search_species.html", context)



def xsearch_species(request):
    min_score = 70
    genus_string = ''
    single_word = ''
    family = ''
    subfamily = ''
    tribe = ''
    subtribe = ''
    genus_list = []
    match_spc_list = []
    match_list = []
    perfect_list = []
    fuzzy_list = []
    fuzzy = ''
    if 'fuzzy' in request.GET:
        fuzzy = request.GET['fuzzy'].strip()
    # If no match found, perform fuzzy match

    if 'spc_string' in request.GET:
        spc_string = request.GET['spc_string'].strip()
        if ' ' not in spc_string:
            single_word = True
            genus_string = spc_string
        elif spc_string.split()[0]:
            genus_string = spc_string.split()[0]
    else:
        send_url = '/'
        return HttpResponseRedirect(send_url)

    role = getRole(request)
    if 'family' in request.GET:
        family = request.GET['family']
    elif 'newfamily' in request.GET:
        family = request.GET['newfamily']

    if family == 'Orchidaceae':
        url = "%s?role=%s&family=Orchidaceae&spc_string=%s" % (
        reverse('common:search_orchid'), role, spc_string)
        return HttpResponseRedirect(url)

    if family and family != 'other':
        family = Family.objects.get(pk=family)
        app = family.application
    else:
        family = ''
        app = 'other'
    # For other family search across all other families
    if app == 'other':
        family = ''

    # if suprageneric rank requested
    if 'subfamily' in request.GET:
        subfamily = request.GET['subfamily'].strip()
    if subfamily:
        subfamily = Subfamily.objects.get(subfamily=subfamily)
    if 'tribe' in request.GET:
        tribe = request.GET['tribe'].strip()
    if tribe:
        tribe = Tribe.objects.get(tribe=tribe)
    if 'subtribe' in request.GET:
        subtribe = request.GET['subtribe'].strip()
    if subtribe:
        subtribe = Subtribe.objects.get(subtribe=subtribe)

    spc = spc_string
    if family:
        if family.family == 'Cactaceae':
            species_list = get_species_list('cactaceae', family, subfamily, tribe, subtribe)
        elif family.family == 'Orchidaceae':
            species_list = get_species_list('orchidaceae', family, subfamily, tribe, subtribe)
        elif family.family == 'Bromeliaceae':
            species_list = get_species_list('bromeliaceae', family, subfamily, tribe, subtribe)
        else:
            species_list = get_species_list('other')
            species_list = species_list.filter(gen__family=family.family)
    else:
        # In case of app = other, search will scan through every family in the app.
        species_list = get_species_list('other')

    # Perform conventional match
    if not fuzzy:
        # exact match genus, and species from beginning of word
        if genus_string:  # Seach genus table
            min_score = 80
            # Try to match genus
            CaGenus = apps.get_model('cactaceae', 'Genus')
            OrGenus = apps.get_model('orchidaceae', 'Genus')
            OtGenus = apps.get_model('other', 'Genus')
            BrGenus = apps.get_model('bromeliaceae', 'Genus')
            cagenus_list = CaGenus.objects.all()
            cagenus_list = cagenus_list.values('pid', 'genus', 'family', 'author', 'description', 'num_species', 'num_hybrid', 'status', 'year')
            orgenus_list = OrGenus.objects.all()
            orgenus_list = orgenus_list.values('pid', 'genus', 'family', 'author', 'description', 'num_species', 'num_hybrid', 'status', 'year')
            brgenus_list = BrGenus.objects.all()
            brgenus_list = brgenus_list.values('pid', 'genus', 'family', 'author', 'description', 'num_species', 'num_hybrid', 'status', 'year')
            otgenus_list = OtGenus.objects.all()
            otgenus_list = otgenus_list.values('pid', 'genus', 'family', 'author', 'description', 'num_species', 'num_hybrid', 'status', 'year')
            genus_list = cagenus_list.union(orgenus_list).union(otgenus_list).union(brgenus_list)
            search_list = []
            for x in genus_list:
                if x['genus']:
                    score = fuzz.ratio(x['genus'].lower(), genus_string.lower())
                    if score >= min_score:
                        search_list.append([x, score])

            search_list.sort(key=lambda k: (-k[1], k[0]['genus']))
            del search_list[5:]
            genus_list = search_list
            print(">> 1 genus_list = " + str(len(genus_list)))
        CaSpecies = apps.get_model('cactaceae', 'Species')
        OrSpecies = apps.get_model('orchidaceae', 'Species')
        OtSpecies = apps.get_model('other', 'Species')
        BrSpecies = apps.get_model('bromeliaceae', 'Species')
        caspecies_list = CaSpecies.objects.filter(species__istartswith=spc_string)
        caspecies_list = caspecies_list.values('pid', 'species', 'family', 'genus', 'author', 'status', 'year')
        orspecies_list = OrSpecies.objects.filter(species__istartswith=spc_string)
        orspecies_list = orspecies_list.values('pid', 'species', 'family', 'genus', 'author', 'status', 'year')
        brspecies_list = BrSpecies.objects.filter(species__istartswith=spc_string)
        brspecies_list = brspecies_list.values('pid', 'species', 'family', 'genus', 'author', 'status', 'year')
        otspecies_list = OtSpecies.objects.filter(species__istartswith=spc_string)
        otspecies_list = otspecies_list.values('pid', 'species', 'family', 'genus', 'author', 'status', 'year')
        species_list = caspecies_list.union(orspecies_list).union(otspecies_list).union(brspecies_list)
        if single_word:
            match_spc_list = species_list
            #If search string is one word, then get species from all families
            for x in matched_species_list:
                if x['species']:
                    score = fuzz.ratio(x['species'].lower(), spc_string.lower())
                    if score >= min_score:
                        match_spc_list.append([x, score])
            match_spc_list.sort(key=lambda k: (-k[1], k[0]['species']))
            print(">> 2 match_spc_list = " + str(len(matched_species_list)))
            # del match_spc_list[5:]
        else:
            spc_string = spc_string.replace(' mem ', ' Memoria ')
            spc_string = spc_string.replace(' Mem ', ' Memoria ')
            spc_string = spc_string.replace(' mem. ', ' Memoria ')
            spc_string = spc_string.replace(' Mem. ', ' Memoria ')
            words = spc_string.split()
            grex = spc_string.split(' ', 1)
            if len(grex) > 1:
                grex = grex[1]
            else:
                 grex = grex[0]
            subgrex = grex.rsplit(' ', 1)[0]
            if len(words) > 1:
                caperfect_list = caspecies_list.filter(binomial__istartswith=spc_string)
                orperfect_list = orspecies_list.filter(binomial__istartswith=spc_string)
                brperfect_list = brspecies_list.filter(binomial__istartswith=spc_string)
                caperfect_list = caspecies_list.filter(binomial__istartswith=spc_string)


                print(">> 3 perfect_list = " + str(len(perfect_list)))
            if len(perfect_list) == 0:
                if len(words) == 1:
                    # Single word could be a genus or an epithet
                    match_list = species_list.filter(species__istartswith=grex)
                    # match_list = species_list.filter(species__icontains=grex)
                else:
                    match_list = species_list.filter(Q(binomial__icontains=grex) | Q(binomial__icontains=grex))
                    # match_list = species_list.exclude(binomial=spc_string).filter(Q(binomial__icontains=spc_string) | Q(species__icontains=spc_string) | Q(species__icontains=grex) | Q(infraspe__icontains=words[-1]) | Q(binomial__icontains=grex) | Q(species__icontains=subgrex)  | Q(binomial__icontains=subgrex))
                print(">> 4 match_list = " + str(len(match_list)))
                if len(match_list) == 0:
                    if not genus_list:
                        fuzzy = 1
                        url = "%s?role=%s&app=%s&family=%s&spc_string=%s&fuzzy=1" % (reverse('common:search_species'), role, app, family, spc_string)
                        return HttpResponseRedirect(url)

    # Perform Fuzzy search if requested (fuzzy = 1) or if no species match found:
    else:
        first_try = species_list.filter(species=spc)
        min_score = 60
        for x in species_list:
            if x.binomial:
                score = fuzz.ratio(x.binomial, spc)
                if score >= min_score:
                    fuzzy_list.append([x, score])
        fuzzy_list.sort(key=lambda k: (-k[1], k[0].binomial))
        del fuzzy_list[20:]
    path = 'information'
    if role == 'cur':
        path = 'photos'
    family_list, alpha = get_family_list(request)

    write_output(request, spc_string)
    context = {'spc_string': spc_string, 'genus_list': genus_list, 'match_spc_list': match_spc_list,
               'perfect_list': perfect_list, 'match_list': match_list, 'fuzzy_list': fuzzy_list,
               'genus_total': len(genus_list), 'match_total': len(match_list), 'fuzzy_total': len(fuzzy_list), 'perfect_total': len(perfect_list),
               'family_list': family_list, 'alpha_list': alpha_list, 'alpha': alpha, 'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
               'app': app, 'fuzzy': fuzzy, 'single_word': single_word,
               'title': 'search', 'role': role, 'path': path}
    return django.shortcuts.render(request, "common/search_species.html", context)


def search(request):
    CaGenus = apps.get_model('cactaceae', 'Genus')
    OrGenus = apps.get_model('orchidaceae', 'Genus')
    OtGenus = apps.get_model('other', 'Genus')
    BrGenus = apps.get_model('bromeliaceae', 'Genus')
    min_score = 60
    genus_string = ''
    qgenlist = []
    qgenus = ''
    family = ''
    subfamily = ''
    tribe = ''
    subtribe = ''
    genus_list = []
    species_list = []
    match_list = []
    perfect_list = []
    fuzzy_list = []
    fuzzy = ''
    if 'fuzzy' in request.GET:
        fuzzy = request.GET['fuzzy'].strip()
    # If no match found, perform fuzzy match

    role = getRole(request)
    if 'family' in request.GET:
        family = request.GET['family']
    elif 'newfamily' in request.GET:
        family = request.GET['newfamily']
    if 'spc_string' in request.GET:
        spc_string = request.GET['spc_string'].strip()
        if ' ' not in spc_string:
            genus_string = spc_string
    else:
        send_url = '/'
        return HttpResponseRedirect(send_url)

    # if family == 'Orchidaceae':
    #     send_url = "%s?role=%s&app=orchidaceae&family=%s&spc_string=%s" % (reverse('common:search_match'), role, family, spc_string)
    #     return HttpResponseRedirect(send_url)


    if family and family != 'other':
        family = Family.objects.get(pk=family)
        app = family.application
    else:
        family = ''
        app = 'other'
    # For other family search across all other families
    # if app == 'other':
    #     family = ''


    # if suprageneric rank requested
    if 'subfamily' in request.GET:
        subfamily = request.GET['subfamily'].strip()
    if subfamily:
        subfamily = Subfamily.objects.get(subfamily=subfamily)

    if 'tribe' in request.GET:
        tribe = request.GET['tribe'].strip()
    if tribe:
        tribe = Tribe.objects.get(tribe=tribe)

    if 'subtribe' in request.GET:
        subtribe = request.GET['subtribe'].strip()
    if subtribe:
        subtribe = Subtribe.objects.get(subtribe=subtribe)
    # genus_list = OrGenus.objects.filter(subfamily=subfamily).filter(tribe=tribe).filter(subtribe=subtribe)
    spc_string = spc_string.replace(' mem ', ' Memoria ')
    words = spc_string.split()
    grex = spc_string.split(' ', 1)

    try:
        GenusRel = apps.get_model('orchidaceae', 'GenusRelation')
        qgenus = OrGenus.objects.filter(genus__iexact=words[0])

    except OrGenus.DoesNotExist:
        try:
            qgenus = OrGenus.objects.filter(abrev__iexact=words[0])
        except OrGenus.DoesNotExist:
            qgenus = ''

    if qgenus:
        qgenus = qgenus[0]
        qgenlist = GenusRel.objects.filter(formula__icontains=qgenus.genus).values_list('genus', flat=True).distinct()
    else:
        qgenlist = []

    spc = spc_string
    if family:
        if family.family == 'Cactaceae':
            species_list = get_species_list('cactaceae', family, subfamily, tribe, subtribe)
        elif family.family == 'Orchidaceae':
            species_list = get_species_list('orchidaceae', family, subfamily, tribe, subtribe)
            if qgenlist:
                species_list = species_list.filter(genus__in=qgenlist)
        elif family.family == 'Bromeliaceae':
            species_list = get_species_list('bromeliaceae', family, subfamily, tribe, subtribe)
        else:
            species_list = get_species_list('other')
            species_list = species_list.filter(gen__family=family.family)
    else:
        # In case of app = other, search will scan through every family in the app.
        species_list = get_species_list('other')

    # Perform conventional match
    if not fuzzy:
        if genus_string:  # Seach genus table
            genus_list = []
            cagenus_list = CaGenus.objects.all()
            cagenus_list = cagenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type',
                                               'description', 'num_species', 'num_hybrid')
            orgenus_list = OrGenus.objects.all()
            orgenus_list = orgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type',
                                               'description', 'num_species', 'num_hybrid')
            brgenus_list = BrGenus.objects.all()
            brgenus_list = brgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type',
                                               'description', 'num_species', 'num_hybrid')
            otgenus_list = OtGenus.objects.all()
            otgenus_list = otgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type',
                                               'description', 'num_species', 'num_hybrid')
            genus_list = cagenus_list.union(orgenus_list).union(otgenus_list).union(brgenus_list)
            search_list = []
            for x in genus_list:
                if x['genus']:
                    score = fuzz.ratio(x['genus'], genus_string)
                    if score >= min_score:
                        search_list.append([x, score])

            search_list.sort(key=lambda k: (-k[1], k[0]['genus']))
            del search_list[5:]
            genus_list = search_list

        # spc_string = spc_string.replace('.', '')
        if qgenus:
            perfect_list = species_list.filter(binomial__iexact=spc_string)
            if not perfect_list:
                perfect_list = species_list.filter(genus__iexact=qgenus).filter(species__istartswith=grex)

        else:
            if len(grex) > 1:
                grex = grex[1]
            else:
                 grex = grex[0]
            subgrex = grex.rsplit(' ', 1)[0]
            perfect_list = species_list.filter(binomial__iexact=spc_string)
            pid_list = perfect_list.values_list('pid', flat=True)

            perfect_list1 = species_list.filter(binomial__istartswith=spc_string).exclude(pid__in=pid_list)
            perfect_list = perfect_list.union(perfect_list1)
            pid_list = perfect_list.values_list('pid', flat=True)

            perfect_list2 = species_list.filter(species__iexact=spc_string).exclude(pid__in=pid_list)
            perfect_list = perfect_list.union(perfect_list2)
            pid_list = perfect_list.values_list('pid', flat=True)

            perfect_list2 = species_list.filter(species__istartswith=spc_string).exclude(pid__in=pid_list)
            perfect_list = perfect_list.union(perfect_list2)
            pid_list = perfect_list.values_list('pid', flat=True)

            if len(spc_string) > 5:
                perfect_list2 = species_list.filter(species__istartswith=spc_string[: -2]).exclude(pid__in=pid_list)
                perfect_list = perfect_list.union(perfect_list2)

        if len(perfect_list) == 0:
            if len(words) == 1:
                match_list = species_list.filter(Q(species__icontains=spc_string) | Q(infraspe__icontains=spc_string))
            else:
                match_list = species_list.filter(Q(binomial__icontains=spc_string) | Q(binomial__icontains=grex))
                # match_list = species_list.exclude(binomial=spc_string).filter(Q(binomial__icontains=spc_string) | Q(species__icontains=spc_string) | Q(species__icontains=grex) | Q(infraspe__icontains=words[-1]) | Q(binomial__icontains=grex) | Q(species__icontains=subgrex)  | Q(binomial__icontains=subgrex))
            if len(match_list) == 0:
                if not genus_list:
                    fuzzy = 1
                    url = "%s?role=%s&app=%s&family=%s&spc_string=%s&fuzzy=1" % (reverse('common:search_species'), role, app, family, spc_string)
                    return HttpResponseRedirect(url)

    # Perform Fuzzy search if requested (fuzzy = 1) or if no species match found:
    else:
        first_try = species_list.filter(species__iexact=spc)
        min_score = 60
        for x in species_list:
            if x.binomial:
                score = fuzz.ratio(x.binomial, spc)
                if score >= min_score:
                    fuzzy_list.append([x, score])
        fuzzy_list.sort(key=lambda k: (-k[1], k[0].binomial))
        del fuzzy_list[20:]
    path = 'information'
    if request.user == 'chariya':
        path = 'photos'
    family_list, alpha = get_family_list(request)

    write_output(request, spc_string)
    context = {'spc_string': spc_string, 'genus_list': genus_list,
               'perfect_list': perfect_list, 'match_list': match_list, 'fuzzy_list': fuzzy_list,
               'genus_total': len(genus_list), 'match_total': len(match_list), 'fuzzy_total': len(fuzzy_list), 'perfect_total': len(perfect_list),
               'family_list': family_list, 'alpha_list': alpha_list, 'alpha': alpha, 'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
               'app': app, 'fuzzy': fuzzy,
               'title': 'search', 'role': role, 'path': path}
    return django.shortcuts.render(request, "common/search.html", context)


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

    ortype = 'hybrid'
    if 'type' in request.GET:
        ortype = request.GET['type']
    if 'page' in request.GET:
        page = request.GET['page']
    else:
        page = "1"

    upl = UploadFile.objects.get(id=orid)
    filename = os.path.join(settings.MEDIA_ROOT, str(upl.image_file_path))
    upl.delete()
    area = ''
    if 'area' in request.GET:
        area = request.GET['area']
    if 'next' in request.GET:
        next = request.GET['next']
    role = getRole(request)

    if area == 'allpending':
        # bulk delete by curators from all_pending tab
        url = "%s&page=%s&type=%s&days=%d&family=" % (reverse('common:curate_pending'), page, ortype, days, family)
    elif area == 'curate_newupload':  # from curate_newupload (all rank 0)
        # Requested from all upload photos
        url = "%s?page=%s" % (reverse('common:curate_newupload'), page)
    if next == 'photos':
        url = "%s?role=%s&family=%s" % (reverse('display:photos'), role, family)
    else:
        url = "%s?role=%s&family=%s" % (reverse('common:curate_newupload'), role, family)
    # url = "%s?role=%s&family=%s" % (reverse('display:photos', args=(species.pid,)), role, family)

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
            # hist = SpcImgHistory(pid=Accepted.objects.get(pk=pid), user_id=request.user, img_id=spc.id, action='approve file')
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
                # upl.delete()
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
        # hist.save()
        upl.approved = True
        upl.delete(0)
    write_output(request, str(family))
    url = "%s?role=%s&family=%s" % (reverse('display:photos', args=(species.pid,)), role, family)
    return HttpResponseRedirect(url)


@login_required
def myphoto(request, pid):
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    role = getRole(request)
    if 'newfamily' in request.GET:
        url = "%s?role=%s&family=%s" % (reverse('common:genera'), role, family)
        return HttpResponseRedirect(url)

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
               'title': 'myphoto', 'app': family.application,
               }
    write_output(request, str(family))
    return render(request, 'common/myphoto.html', context)


def myphoto_list(request):
    author, author_list = get_author(request)
    role = getRole(request)
    if 'family' in request.GET:
        family = request.GET['family']

    # If change family
    if 'newfamily' in request.GET:
        family = request.GET['newfamily']

    app_list = ['Orchidaceae', 'Bromeliaceae', 'Cactaceae', 'other']
    my_hyb_list = []
    my_list = []
    if role == 'pub':
        send_url = "%s?family=%s" % (reverse('common:browse'), family)
        return HttpResponseRedirect(send_url)
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
               'title': 'myphoto_list',
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
        send_url = "%s?family=%s" % (reverse('common:browse'), family)
        return HttpResponseRedirect(send_url)
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

    family_list, alpha = get_family_list(request)

    context = {'my_list': my_list, 'type': 'species', 'family': family, 'app': app,
               'myspecies_list': myspecies_list, 'myhybrid_list': myhybrid_list,
               'role': role, 'brwspc': 'active', 'author': author,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page, 'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'author_list': author_list,  'myspc': 'active',
               'title': 'myphoto_browse',
               'family_list': family_list, 'alpha_list': alpha_list, 'alpha': alpha,
               }
    write_output(request, str(family))
    return render(request, 'common/myphoto_browse_spc.html', context)


@login_required
def myphoto_browse_hyb(request):
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    role = getRole(request)
    if role == 'pub':
        send_url = "%s?tab=%s" % (reverse('common:browse'), 'sum')
        return HttpResponseRedirect(send_url)
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
    if family.family == 'Orchidaceae':
        pid_list = HybImages.objects.filter(author=author).values_list('pid', flat=True).distinct()
    else:
        if family and family != 'other':
            pid_list = SpcImages.objects.filter(author=author).filter(gen__family=family.family).values_list('pid', flat=True).distinct()
        else:
            pid_list = SpcImages.objects.filter(author=author).filter(gen__family__application='other').values_list('pid', flat=True).distinct()

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

    family_list, alpha = get_family_list(request)

    context = {'my_list': my_list, 'type': 'hybrid', 'family': family, 'app': app,
               'myspecies_list': myspecies_list, 'myhybrid_list': myhybrid_list,
               'role': role, 'brwhyb': 'active', 'author': author,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page, 'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'author_list': author_list, 'family_list': family_list, 'alpha_list': alpha_list, 'alpha': alpha, 'myhyb': 'active',
               'title': 'myphoto_browse',
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
               'app': app, 'title': 'curate_newupload', 'section': 'Curator Corner',
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

    file_list = SpcImages.objects.filter(rank=0)

    if days:
        file_list = file_list.filter(modified_date__gte=timezone.now() - timedelta(days=days))
    file_list = file_list.order_by('-created_date')

    num_show = 5
    page_length = 100
    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item = mypaginator(
        request, file_list, page_length, num_show)

    role = getRole(request)
    write_output(request, str(family))
    title = 'curate_pending'
    context = {'file_list': page_list, 'type': ortype, 'family': family,
               'tab': 'pen', 'role': role, 'pen': 'active', 'days': days,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page,
               'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'app': app, 'title': title,
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
               'app': app, 'title': 'curate_newapproved',
               }
    return render(request, 'common/curate_newapproved.html', context)


# NOT USED
def home(request):
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    randgenus = Genus.objects.exclude(status='synonym').extra(where=["num_spc_with_image + num_hyb_with_image > 0"]
                                                              ).values_list('pid', flat=True).order_by('?')
    # Number of visits to this view, as counted in the session variable.
    # num_visits = request.session.get('num_visits', 0)
    # request.session['num_visits'] = num_visits + 1
    randimages = []
    for e in randgenus:
        if len(randimages) >= num_img:
            break
        if SpcImages.objects.filter(gen=e):
            img = SpcImages.objects.filter(gen=e).filter(rank__gt=0).filter(rank__lt=7).order_by('-rank', 'quality', '?'
                                                                                                 )[0:1]
            if img and len(img):
                randimages.append(img[0])

    random.shuffle(randimages)
    role = getRole(request)
    context = {'title': 'orchid_home', 'role': role, 'randimages': randimages, 'tab': 'sum', }
    return render(request, 'home.html', context)

def subfamily(request):
    # -- List Genuses
    f = ''
    if 'f' in request.GET:
        f = request.GET['f']
    subfamily_list = Subfamily.objects.filter(family=f).order_by('subfamily')
    context = {'subfamily_list': subfamily_list, 'alpha_list': alpha_list, 'title': 'subfamilies', 'f': f}
    return render(request, 'core/subfamily.html', context)

def tribe(request):
    f, sf = '', ''
    if 'f' in request.GET:
        f = request.GET['f']
    subfamily_list = Subfamily.objects.filter(family=f)
    tribe_list = Tribe.objects.order_by('tribe').filter(family=f)
    if 'sf' in request.GET:
        sf = request.GET['sf']
        if sf:
            sf_obj = Subfamily.objects.get(pk=sf)
            if sf_obj:
                tribe_list = tribe_list.filter(subfamily=sf)
    context = {'tribe_list': tribe_list, 'title': 'tribes', 'f': f, 'sf': sf, 'subfamily_list': subfamily_list, }
    return render(request, 'core/tribe.html', context)

def subtribe(request):
    f, sf, t = '', '', ''
    if 'f' in request.GET:
        f = request.GET['f']
    subfamily_list = Subfamily.objects.filter(family=f)
    tribe_list = Tribe.objects.order_by('tribe').filter(family=f)
    subtribe_list = Subtribe.objects.filter(family=f).order_by('subtribe')
    if 'sf' in request.GET:
        sf = request.GET['sf']
        if sf:
            sf_obj = Subfamily.objects.get(pk=sf)
            if sf_obj:
                subtribe_list = subtribe_list.filter(subfamily=sf)
    if 't' in request.GET:
        t = request.GET['t']
        if t:
            t_obj = Tribe.objects.get(pk=t)
            if t_obj:
                subtribe_list = subtribe_list.filter(tribe=t)

    context = {'subtribe_list': subtribe_list, 'title': 'subtribes', 'f': f, 't': t, 'sf': sf,
               'subfamily_list': subfamily_list, 'tribe_list': tribe_list, }
    return render(request, 'core/subtribe.html', context)

