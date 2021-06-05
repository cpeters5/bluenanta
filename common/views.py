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
from accounts.models import User, Photographer
from .forms import UploadFileForm, UploadSpcWebForm, UploadHybWebForm, AcceptedInfoForm, HybridInfoForm, \
    SpeciesForm, RenameSpeciesForm

epoch = 1740
alpha_list = string.ascii_uppercase
logger = logging.getLogger(__name__)
GenusRelation = []
Accepted = []
Synonym = []
alpha_list = config.alpha_list
f, sf, t, st = '', '', '', ''
redirect_message = 'species does not exist'
# num_show = 5
# page_length = 500


def getForms(request):
    family, app = '', ''
    if 'family' in request.GET:
        family = request.GET['family']
    elif 'family' in request.POST:
        family = request.POST['family']
    if family:
        family = Family.objects.get(pk=family)
    try:
        app = Family.objects.get(pk=family)
        app = app.application
    except Family.DoesNotExist:
        app = ''
        family = ''
    if app == 'orchidaceae':
        from orchidaceae.forms import UploadFileForm, UploadSpcWebForm, UploadHybWebForm, AcceptedInfoForm, HybridInfoForm, SpeciesForm, RenameSpeciesForm
    elif app == 'bromeliaceae':
        from bromeliaceae.forms import UploadFileForm, UploadSpcWebForm, UploadHybWebForm, AcceptedInfoForm, \
            HybridInfoForm, SpeciesForm, RenameSpeciesForm
    elif app == 'cactaceae':
        from cactaceae.forms import UploadFileForm, UploadSpcWebForm, UploadHybWebForm, AcceptedInfoForm, \
            HybridInfoForm, SpeciesForm, RenameSpeciesForm
    elif app == 'other':
        from other.forms import UploadFileForm, UploadSpcWebForm, UploadHybWebForm, AcceptedInfoForm, \
            HybridInfoForm, SpeciesForm, RenameSpeciesForm
    if app:
        return UploadFileForm, UploadSpcWebForm, UploadHybWebForm, AcceptedInfoForm, HybridInfoForm, SpeciesForm, RenameSpeciesForm
    else:
        return None,None,None,None,None,None,None,

def getAllGenera():
    # Call this when Family is not provided
    OrGenus = apps.get_model('orchidaceae', 'Genus')
    BrGenus = apps.get_model('bromeliaceae', 'Genus')
    CaGenus = apps.get_model('cactaceae', 'Genus')
    OtGenus = apps.get_model('other', 'Genus')
    return OrGenus, BrGenus, CaGenus, OtGenus


def getAllSpecies():
    # Call this when Genus or Family is not provided
    OrSpecies = apps.get_model('orchidaceae', 'Species')
    BrSpecies = apps.get_model('bromeliaceae', 'Species')
    CaSpecies = apps.get_model('cactaceae', 'Species')
    OtSpecies = apps.get_model('other', 'Species')
    OrSpcImages = apps.get_model('orchidaceae', 'SpcImages')
    OrHybImages = apps.get_model('orchidaceae', 'HybImages')
    BrSpcImages = apps.get_model('bromeliaceae', 'SpcImages')
    CaSpcImages = apps.get_model('cactaceae', 'SpcImages')
    OtSpcImages = apps.get_model('other', 'SpcImages')

    return OrSpecies, BrSpecies, CaSpecies, OtSpecies, OrSpcImages, OrHybImages, BrSpcImages, CaSpcImages, OtSpcImages

def getFamilyImage(family):
    SpcImages = apps.get_model(family.application, 'SpcImages')
    return SpcImages.objects.filter(rank__lt=7).filter(status='approved').order_by('-rank','quality', '?')[0:1][0]

def orchid_home(request):
    role = getRole(request)
    if 'newfamily' in request.GET:
        family = request.GET['newfamily']

        url = "%s?role=%s&family=%s" % (reverse('common:genera'), role, family)
        return HttpResponseRedirect(url)

    num_samples = 5
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

    # get random carnivorous
    sample_genus = Genus.objects.filter(is_carnivorous=True).filter(num_spcimage__gt=0).order_by('?')[0:1][0]
    carnivorous_obj = SpcImages.objects.filter(genus=sample_genus).order_by('?')[0:1][0]


    context = {'orcimage': orcimage, 'broimage': broimage, 'cacimage': cacimage, 'family': orcfamily,
               'other_list': other_list, 'succulent_obj': succulent_obj, 'carnivorous_obj': carnivorous_obj,
        'title': 'orchid_home', 'role': role }
    return render(request, 'orchid_home.html', context)


def require_get(view_func):
    def wrap(request, *args, **kwargs):
        if request.method != "GET":
            return HttpResponseBadRequest("Expecting GET request")
        return view_func(request, *args, **kwargs)
    wrap.__doc__ = view_func.__doc__
    wrap.__dict__ = view_func.__dict__
    wrap.__name__ = view_func.__name__
    return wrap


# @login_required
def genera(request):
    path = resolve(request.path).url_name
    role = getRole(request)
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)

    alpha = ''
    if 'alpha' in request.GET:
        alpha = request.GET['alpha']

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
        otgenus_list = OtGenus.objects.all().order_by('family','genus')
        # orgenus_list = OrGenus.objects.all().order_by('genus')
        # genus_list = list(chain(otgenus_list, brgenus_list, cagenus_list)) #, orgenus_list))
        # genus_list = sorted(allgenus_list, key=operator.attrgetter('genus'))
        genus_list = otgenus_list
    # Complete building genus list
    # Define sort
    if alpha and len(alpha) == 1:
        genus_list = genus_list.filter(genus__istartswith=alpha)
    if request.GET.get('sort'):
        sort = request.GET['sort']
        sort.lower()

    family_list = get_family_list()
    total = len(genus_list)
    write_output(request, str(family))
    context = {
        'genus_list': genus_list,  'app': app, 'total':total,
        'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe, 'role': role,
        'family_list': family_list, 'title': 'taxonomy', 'alpha_list': alpha_list, 'alpha': alpha,
        'path': path
    }
    return render(request, "common/genera.html", context)


def species(request):
    # path = resolve(request.path).url_name
    genus = ''
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
    alpha = ''
    max_items = 3000

    syn = ''
    if 'syn' in request.GET:
        syn = request.GET['syn']

    if genus:
        species_list = Species.objects.filter(type='species').filter(
            cit_status__isnull=True).exclude(cit_status__exact='')
        # new genus has been selected. Now select new species/hybrid
        species_list = species_list.filter(genus=genus)
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

    if 'alpha' in request.GET:
        alpha = request.GET['alpha']
        if alpha == 'ALL':
            alpha = ''
    if alpha != '':
        species_list = species_list.filter(species__istartswith=alpha)
    total = len(species_list)
    msg = ''

    if total > max_items:
        species_list = species_list[0:max_items]
        msg = "List too long, truncated to " + str(max_items) + ". Please refine your search criteria."
        total = max_items
    family_list = get_family_list()

    write_output(request, str(family))
    context = {
        'genus': genus, 'species_list': species_list, 'app': app, 'total':total, 'syn': syn, 'max_items': max_items,
        'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe, 'role': role,
        'family_list': family_list, 'title': 'taxonomy', 'alpha_list': alpha_list, 'alpha': alpha,
        'msg': msg, 'path': path
    }
    return render(request, "common/species.html", context)


def hybrid(request):
    path = resolve(request.path).url_name
    path = 'genera'
    genus = ''
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
    genus = ''
    syn = ''
    primary = ''
    msg = ''
    max_items = 3000
    alpha = ''
    if 'alpha' in request.GET:
        alpha = request.GET['alpha']
        if alpha == 'ALL':
            alpha = ''

    genus = ''
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

    if alpha != '':
        hybrid_list = hybrid_list.filter(species__istartswith=alpha)
    total = len(hybrid_list)
    # hybrid_list = hybrid_list.order_by('genus', 'species')
    if total > max_items:
        hybrid_list = hybrid_list[0:max_items]
        msg = "List too long. Only show first " + str(max_items) + " items"
        total = max_items
    family_list = get_family_list()
    write_output(request, str(family))
    context = {
        'genus': genus, 'hybrid_list': hybrid_list, 'app': app, 'total':total, 'syn': syn, 'max_items': max_items,
        'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe, 'role': role,
        'family_list': family_list, 'title': 'taxonomy', 'alpha_list': alpha_list, 'alpha': alpha,
        'msg': msg, 'path': path, 'primary': primary,
    }
    return render(request, "common/hybrid.html", context)


def information(request, pid):
    role = getRole(request)
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    ps_list = pp_list = ss_list = sp_list = seedimg_list = pollimg_list = ()
    if 'newfamily' in request.GET:
        family = request.GET['newfamily']
        url = "%s?role=%s&family=%s" % (reverse('common:genera'), role, family)
        return HttpResponseRedirect(url)
    offspring_list = []
    offspring_count = 0
    offspring_test = ''
    max_items = 3000
    ancspc_list = []
    seedimg_list = []
    pollimg_list = []
    distribution_list = []
    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        return HttpResponseRedirect('/')

    # If pid is a synonym, convert to accept
    if species.status == 'synonym':
        synonym = Synonym.objects.get(pk=pid)
        pid = synonym.acc_id
        species = Species.objects.get(pk=pid)

    genus = species.gen

    display_items = []
    synonym_list = Synonym.objects.filter(acc=pid)
    if species.gen.family == 'Orchidaceae':
        if species.type == 'species':
            accepted = species.accepted
            images_list = SpcImages.objects.filter(pid=species.pid).order_by('-rank', 'quality', '?')
            distribution_list = Distribution.objects.filter(pid=species.pid)
        else:
            accepted = species.hybrid
            images_list = HybImages.objects.filter(pid=species.pid).order_by('-rank', 'quality', '?')

    else:
        images_list = SpcImages.objects.filter(pid=species.pid).order_by('-rank', 'quality', '?')
        if species.type == 'species':
            accepted = species.accepted
        else:
            accepted = species.hybrid

    # Build display in main table
    if images_list:
        i_1, i_2, i_3, i_4, i_5, i_7, i_8 = 0, 0, 0, 0, 0, 0, 0
        for x in images_list:
            if x.rank == 1 and i_1 <= 0:
                i_1 += 1
                display_items.append(x)
            elif x.rank == 2 and i_2 <= 0:
                i_2 += 1
                display_items.append(x)
            elif x.rank == 3 and i_3 <= 1:
                i_3 += 1
                display_items.append(x)
            elif x.rank == 4 and i_4 <= 3:
                i_4 += 1
                display_items.append(x)
            elif x.rank == 5 and i_5 <= 3:
                i_5 += 1
                display_items.append(x)
            elif x.rank == 7 and i_7 <= 2:
                i_7 += 1
                display_items.append(x)
            elif x.rank == 8 and i_8 < 2:
                i_8 += 1
                display_items.append(x)
    # Build parents display for Orchidaceae hybrid  only
    from orchidaceae.models import AncestorDescendant
    seed_list = Hybrid.objects.filter(seed_id=species.pid).order_by('pollen_genus', 'pollen_species')
    pollen_list = Hybrid.objects.filter(pollen_id=species.pid)
    # Remove duplicates. i.e. if both parents are synonym.
    temp_list = pollen_list
    for x in temp_list:
        if x.seed_status() == 'syn' and x.pollen_status() == 'syn':
            pollen_list = pollen_list.exclude(pid=x.pid_id)
    pollen_list = pollen_list.order_by('seed_genus', 'seed_species')
    offspring_list = chain(list(seed_list), list(pollen_list))
    offspring_count = len(seed_list) + len(pollen_list)
    if offspring_count > max_items:
        offspring_list = offspring_list[0:max_items]

    if species.type == 'hybrid':
        if accepted.seed_id and accepted.seed_id.type == 'species':
            seed_obj = Species.objects.get(pk=accepted.seed_id.pid)
            seedimg_list = SpcImages.objects.filter(pid=seed_obj.pid).filter(rank__lt=7). \
                               order_by('-rank', 'quality', '?')[0: 3]
        elif accepted.seed_id and accepted.seed_id.type == 'hybrid':
            seed_obj = Hybrid.objects.get(pk=accepted.seed_id)
            if seed_obj:
                seedimg_list = HybImages.objects.filter(pid=seed_obj.pid.pid).filter(rank__lt=7).order_by('-rank',
                                                                                                          'quality',
                                                                                                          '?')[0: 3]
                assert isinstance(seed_obj, object)
                if seed_obj.seed_id:
                    ss_type = seed_obj.seed_id.type
                    if ss_type == 'species':
                        ss_list = SpcImages.objects.filter(pid=seed_obj.seed_id.pid).filter(rank__lt=7).order_by(
                            '-rank', 'quality', '?')[: 1]
                    elif ss_type == 'hybrid':
                        ss_list = HybImages.objects.filter(pid=seed_obj.seed_id.pid).filter(rank__lt=7).order_by(
                            '-rank', 'quality', '?')[: 1]
                if seed_obj.pollen_id:
                    sp_type = seed_obj.pollen_id.type
                    if sp_type == 'species':
                        sp_list = SpcImages.objects.filter(pid=seed_obj.pollen_id.pid).filter(rank__lt=7).filter(
                            rank__lt=7).order_by('-rank', 'quality', '?')[: 1]
                    elif sp_type == 'hybrid':
                        sp_list = HybImages.objects.filter(pid=seed_obj.pollen_id.pid).filter(rank__lt=7).filter(
                            rank__lt=7).order_by('-rank', 'quality', '?')[: 1]
        # Pollen
        if accepted.pollen_id and accepted.pollen_id.type == 'species':
            pollen_obj = Species.objects.get(pk=accepted.pollen_id.pid)
            pollimg_list = SpcImages.objects.filter(pid=pollen_obj.pid).filter(rank__lt=7).order_by('-rank', 'quality',
                                                                                                    '?')[0: 3]
        elif accepted.pollen_id and accepted.pollen_id.type == 'hybrid':
            pollen_obj = Hybrid.objects.get(pk=accepted.pollen_id)
            pollimg_list = HybImages.objects.filter(pid=pollen_obj.pid.pid).filter(rank__lt=7). \
                               order_by('-rank', 'quality', '?')[0: 3]
            if pollen_obj.seed_id:
                ps_type = pollen_obj.seed_id.type
                if ps_type == 'species':
                    ps_list = SpcImages.objects.filter(pid=pollen_obj.seed_id.pid).filter(rank__lt=7). \
                                  order_by('-rank', 'quality', '?')[: 1]
                elif ps_type == 'hybrid':
                    ps_list = HybImages.objects.filter(pid=pollen_obj.seed_id.pid).filter(rank__lt=7). \
                                  order_by('-rank', 'quality', '?')[: 1]
            if pollen_obj.pollen_id:
                pp_type = pollen_obj.pollen_id.type
                if pp_type == 'species':
                    pp_list = SpcImages.objects.filter(pid=pollen_obj.pollen_id.pid).filter(rank__lt=7). \
                                  order_by('-rank', 'quality', '?')[: 1]
                elif pp_type == 'hybrid':
                    pp_list = HybImages.objects.filter(pid=pollen_obj.pollen_id.pid).filter(rank__lt=7). \
                                  order_by('-rank', 'quality', '?')[: 1]

        ancspc_list = AncestorDescendant.objects.filter(did=species.pid).filter(anctype='species').order_by('-pct')
        if ancspc_list:
            for x in ancspc_list:
                img = x.aid.get_best_img()
                if img:
                    x.img = img.image_file
    write_output(request, str(family))
    family_list = get_family_list()
    context = {'pid': species.pid, 'species': species, 'synonym_list': synonym_list, 'accepted': accepted,
               'title': 'information', 'tax': 'active', 'q': species.name, 'type': 'species', 'genus': genus,
               'display_items': display_items, 'distribution_list': distribution_list, 'family': family,
               'offspring_list': offspring_list, 'offspring_count': offspring_count, 'max_items': max_items,
               'seedimg_list': seedimg_list, 'pollimg_list': pollimg_list, 'family_list': family_list,
               'ss_list': ss_list, 'sp_list': sp_list, 'ps_list': ps_list, 'pp_list': pp_list,
               'app': app, 'role': role, 'ancspc_list': ancspc_list,
               }
    return render(request, "common/information.html", context)


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


def photos(request, pid=None):
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    role = getRole(request)
    if 'newfamily' in request.GET:
        family = request.GET['newfamily']
        url = "%s?role=%s&family=%s" % (reverse('common:genera'), role, family)
        return HttpResponseRedirect(url)

    author, author_list = get_author(request)
    if not pid and 'pid' in request.GET:
        pid = request.GET['pid']
        if pid:
            pid = int(pid)
        else:
            pid = 0

    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        return HttpResponseRedirect('/')


    if role == 'pri':
        url = "%s?role=%s&family=%s" % (reverse('common:myphoto', args=(species.pid,)), role, family)
        return HttpResponseRedirect(url)

    if species.status == 'synonym':
        synonym = Synonym.objects.get(pk=pid)
        pid = synonym.acc_id
        species = Species.objects.get(pk=pid)

    variety = ''
    tail = ''

    if family.family == 'Orchidaceae' and species.type == 'hybrid':
        all_list = HybImages.objects.filter(pid=species.pid)
    else:
        all_list = SpcImages.objects.filter(pid=species.pid)

    # Get private photos

    private_list, public_list, upload_list, myspecies_list, myhybrid_list = getmyphotos(author, app, species, Species, UploadFile, SpcImages, HybImages, role)
    # Happened when a curator request an author photos
    # if role == 'cur':
    #     if author:
    #         public_list = all_list.filter(rank__gt=0).filter(author=author)
    #         private_list = all_list.filter(rank=0).filter(author=author)
    # else:  # anonymous
    #     public_list = all_list.filter(rank__gt=0)

    # upload_list = UploadFile.objects.filter(pid=species.pid)
    # if role != 'cur':
    #     if author:
    #         upload_list = upload_list.filter(author=author)
    if app == 'orchidaceae' and species.type == 'hybrid':
        rank_update(request, HybImages)
        quality_update(request, HybImages)
    else:
        rank_update(request, SpcImages)
        quality_update(request, SpcImages)
    # Handle Variety filter
    if 'variety' in request.GET:
        variety = request.GET['variety']
    if variety == 'semi alba':
        variety = 'semialba'

    # Extract first term, possibly an infraspecific
    parts = variety.split(' ', 1)
    if len(parts) > 1:
        tail = parts[1]
    var = variety
    if variety and tail:
        public_list = public_list.filter(Q(variation__icontains=var) | Q(form__icontains=var) | Q(name__icontains=var)
                                         | Q(source_file_name__icontains=var) | Q(description__icontains=var)
                                         | Q(variation__icontains=tail) | Q(form__icontains=tail)
                                         | Q(name__icontains=tail) | Q(source_file_name__icontains=tail)
                                         | Q(description__icontains=tail))
    elif variety:
        public_list = public_list.filter(Q(variation__icontains=var) | Q(form__icontains=var) | Q(name__icontains=var)
                                         | Q(source_file_name__icontains=var) | Q(description__icontains=var))

    if public_list:
        if var == "alba":
            public_list = public_list.exclude(variation__icontains="semi")
        public_list = public_list.order_by('-rank', 'quality', '?')
        if private_list:
            private_list = private_list.order_by('created_date')

    write_output(request, str(family))
    family_list = get_family_list()
    context = {'species': species, 'author': author, 'author_list': author_list, 'family': family,
               'variety': variety, 'pho': 'active', 'tab': 'pho', 'app':app, 'family_list': family_list,
               'public_list': public_list, 'private_list': private_list, 'upload_list': upload_list,
               'myspecies_list': myspecies_list, 'myhybrid_list': myhybrid_list,
               'role': role, 'title': 'photos', 'namespace': 'common',
               }
    return render(request, 'common/photos.html', context)


def browse(request):
    app = ''
    num_show = 5
    page_length = 20
    if 'newfamily' in request.GET:
        family = request.GET['newfamily']
    elif 'family' in request.GET:
        family = request.GET['family']

    if family and family != 'other':
        family = Family.objects.get(family=family)
        app = family.application
    else:
        app = 'other'
    if 'alpha' in request.GET:
        alpha = request.GET['alpha']
        if alpha == 'ALL':
            alpha = ''
        elif len(alpha) > 1:
            alpha = alpha[0].upper()

    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    # reqsubgenus = reqsection = reqsubsection = reqseries = ''
    # subgenus_obj = section_obj = subsection_obj = series_obj = ''
    # subgenus_list = section_list = subsection_list = series_list = []
    page_range = page_list = last_page = next_page = prev_page = page = first_item = last_item = alpha = total = ''
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

    # genus, pid_list, intragen_list = getPartialPid(reqgenus, type, 'accepted', app)

    if app == 'orchidaceae':
        Genus = apps.get_model(app.lower(), 'Genus')
        Species = apps.get_model(app.lower(), 'Species')
    else:
        Genus = apps.get_model(app.lower(), 'Genus')
        Species = apps.get_model(app.lower(), 'Species')

    pid_list = Species.objects.filter(type=type)
    pid_list = pid_list.exclude(status='synonym')

    if reqgenus:
        try:
            genus = Genus.objects.get(genus=reqgenus)
        except Genus.DoesNotExist:
            genus = ''
        if genus:
            pid_list = pid_list.filter(genus=genus)
    else:
        reqgenus = ''

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

        if alpha:
            if reqgenus:
                pid_list = pid_list.filter(species__istartswith=alpha)
            else:
                pid_list = pid_list.filter(genus__istartswith=alpha)

        pid_list = pid_list.order_by('genus', 'species')
        total = len(pid_list)
        page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item \
            = mypaginator(request, pid_list, page_length, num_show)

        my_full_list = []
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


    family_list = get_family_list()

    genus_list = Genus.objects.all()
    if family:
        genus_list = genus_list.filter(family=family.family)
    if display == 'checked':
        if type == 'species':
            genus_list = genus_list.filter(num_spcimage__gt=0)
        else:
            genus_list = genus_list.filter(num_hybimage__gt=0)
    write_output(request, str(family))
    context = {'family':family, 'family_list': family_list,
        'page_list': my_full_list, 'type': type, 'genus': reqgenus, 'display': display, 'genus_list': genus_list,
        'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
        'page': page, 'alpha': alpha, 'alpha_list': alpha_list, 'total': total,
        'seed_genus': seed_genus, 'seed': seed, 'pollen_genus': pollen_genus, 'pollen': pollen,
        'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
        'title': 'browse', 'section': 'list', 'role': role,
    }

    return render(request, 'common/browse.html', context)


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
    elif family:
        species_list = species_list.filter(gen__family=family)
    return species_list
    # return species_list.values('pid', 'binomial', 'author', 'source', 'status', 'type', 'family')


def search_species(request):
    min_score = 20
    spc_string = ''
    genus_string = ''
    family = ''
    subfamily = ''
    tribe = ''
    subtribe = ''
    app = ''
    species_list = []
    genus_list = []

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
    if app == 'other':
        family = ''

    if 'spc_string' in request.GET:
        spc_string = request.GET['spc_string'].strip()
        if ' ' not in spc_string:
            genus_string = spc_string
    else:
        send_url = '/'
        return HttpResponseRedirect(send_url)

    # if higher rank taxon requested
    if 'subfamily' in request.GET:
        subfamily = request.GET['subfamily'].strip()
    if subfamily:
        subfamily = Subfamily.objects.get(subfamily=subfamily)
    if 'tribe' in request.GET:
        tribe = request.GET['tribe'].strip()
    if tribe:
        tribe = Tribe.objects.get(tribe=tribe)
    if 'subtribe' in request.GET:
        subtribe = request.GET['subtribe'].subtribe()
    if subtribe:
        subtribe = Subtribe.objects.get(subtribe=subtribe)

    fuzzy = ''
    if 'fuzzy' in request.GET:
        fuzzy = request.GET['fuzzy'].strip()
    # If no match found, perform fuzzy match

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

    fuzzy_list = []
    genus_list = []
    match_list = []
    perfect_list = []

    # Perform conventional match
    if not fuzzy:
        if genus_string:  # Seach genus table
            CaGenus = apps.get_model('cactaceae', 'Genus')
            OrGenus = apps.get_model('orchidaceae', 'Genus')
            OtGenus = apps.get_model('other', 'Genus')
            BrGenus = apps.get_model('bromeliaceae', 'Genus')
            genus_list = []
            cagenus_list = CaGenus.objects.all()
            cagenus_list = cagenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type', 'description', 'num_species', 'num_hybrid')
            orgenus_list = OrGenus.objects.all()
            orgenus_list = orgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type', 'description', 'num_species', 'num_hybrid')
            brgenus_list = BrGenus.objects.all()
            brgenus_list = brgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type', 'description', 'num_species', 'num_hybrid')
            otgenus_list = OtGenus.objects.all()
            otgenus_list = otgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type', 'description', 'num_species', 'num_hybrid')
            genus_list = cagenus_list.union(orgenus_list).union(otgenus_list).union(brgenus_list)
            search_list = []
            for x in genus_list:
                if x['genus']:
                    score = fuzz.ratio(x['genus'].lower(), genus_string)
                    if score >= min_score:
                        search_list.append([x, score])

            search_list.sort(key=lambda k: (-k[1], k[0]['genus']))
            del search_list[5:]
            genus_list = search_list

        spc_string = spc_string.replace('.', '')
        spc_string = spc_string.replace(' mem ', ' Memoria ')
        spc_string = spc_string.replace(' Mem ', ' Memoria ')
        words = spc_string.split()
        grex = spc_string.split(' ', 1)
        if len(grex) > 1:
            grex = grex[1]
        else:
             grex = grex[0]
        subgrex = grex.rsplit(' ', 1)[0]

        perfect_list = species_list.filter(binomial=spc_string)

        if len(words) == 1:
            match_list = species_list.exclude(binomial=spc_string).filter(Q(species__icontains=spc_string) | Q(species__icontains=grex) | Q(infraspe__icontains=words[-1]) | Q(species__icontains=subgrex))
        else:
            if words:
                match_list = species_list.exclude(binomial=spc_string).filter(Q(binomial__icontains=spc_string) | Q(species__icontains=spc_string) | Q(species__icontains=grex) | Q(infraspe__icontains=words[-1]) | Q(binomial__icontains=grex) | Q(species__icontains=subgrex)  | Q(binomial__icontains=subgrex))
        if len(match_list) == 0 and len(perfect_list) == 0 and len(genus_list) == 0:
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
    family_list = get_family_list()

    write_output(request, spc_string)
    context = {'spc_string': spc_string, 'genus_list': genus_list,
               'perfect_list': perfect_list, 'match_list': match_list, 'fuzzy_list': fuzzy_list,
               'genus_total': len(genus_list), 'match_total': len(match_list), 'fuzzy_total': len(fuzzy_list), 'perfect_total': len(perfect_list),
               'family_list': family_list, 'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
               'app': app, 'fuzzy': fuzzy,
               'title': 'search', 'role': role, 'path': path}
    return django.shortcuts.render(request, "common/search_species.html", context)


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


# @login_required
def deletephoto(request, orid, pid):
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    spcall = Species.objects.all()


    try:
        image = UploadFile.objects.get(pk=orid)
    except UploadFile.DoesNotExist:
        message = 'This hybrid does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)

    try:
        species = Species.objects.get(pk=image.pid_id)
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
    role = getRole(request)

    if area == 'allpending':
        # bulk delete by curators from all_pending tab
        url = "%s&page=%s&type=%s&days=%d&family=" % (reverse('detail:curate_pending'), page, ortype, days, family)
    elif area == 'curate_newupload':  # from curate_newupload (all rank 0)
        # Requested from all upload photos
        url = "%s?page=%s" % (reverse('detail:curate_newupload'), page)
    url = "%s?role=%s&family=%s" % (reverse('common:photos', args=(species.pid,)), role, family)

    # Finally remove file if exist
    if os.path.isfile(filename):
        os.remove(filename)

    write_output(request, str(family))
    return HttpResponseRedirect(url)


# @login_required
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
        url = "%s?role=%s&family=%s" % (reverse('common:photos', args=(species.pid,)), role, family)
    write_output(request, str(family))
    return HttpResponseRedirect(url)


# @login_required
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
        url = "%s?role=%s&msg=%s&family=%s" % (reverse('common:photos', args=(species.pid,)), role, msg, family)
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
                            description=upl.description, location=upl.location, created_date=upl.created_date)
            else:
                spc = SpcImages(pid=species, author=upl.author, user_id=upl.user_id, name=upl.name, awards=upl.awards,
                            source_file_name=upl.source_file_name, variation=upl.variation, form=upl.forma, rank=0,
                            description=upl.description, location=upl.location, created_date=upl.created_date)
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
                            description=upl.description, location=upl.location, created_date=upl.created_date)
            spc.approved_by = request.user
            if family.family == 'Orchidaceae':
                newdir = os.path.join(settings.STATIC_ROOT, "utils/images/hybrid")
            else:
                newdir = os.path.join(settings.STATIC_ROOT, "utils/images/" + str(family))
            image_file = "hyb_"

        image_file = image_file + str(format(upl.pid_id, "09d")) + "_" + str(format(upl.id, "09d"))
        new_name = os.path.join(newdir, image_file)
        if not os.path.exists(new_name + ext):
            try:
                shutil.copy(old_name, tmp_name)
                shutil.move(old_name, new_name + ext)
            except shutil.Error:
                # upl.delete()
                url = "%s?role=%s&family=%s" % (reverse('common:photos', args=(species.pid,)), role, family)
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
                        url = "%s?role=%s&family=%s" % (reverse('common:photos', args=(species.pid,)), role, family)
                        return HttpResponseRedirect(url)
                    spc.image_file = image_file
                    break
                i += 1

        spc.save()
        # hist.save()
        upl.approved = True
        upl.delete(0)
    write_output(request, str(family))
    url = "%s?role=%s&family=%s" % (reverse('common:photos', args=(species.pid,)), role, family)
    return HttpResponseRedirect(url)


# @login_required
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
        url = "%s?role=%s&family=%s" % (reverse('common:information', args=(pid,)), role, species.gen.family)
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
               'title': 'myphoto',
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

    family_list = get_family_list()

    context = {'my_list': my_list, 'family': family, 'app': app,
               'my_list': my_list,
               'role': role, 'brwspc': 'active', 'author': author,
               'author_list': author_list,
               'title': 'myphoto_list',
               'family_list': family_list,
               }
    write_output(request, str(family))
    return render(request, 'common/myphoto_list.html', context)

# @login_required
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

    family_list = get_family_list()

    context = {'my_list': my_list, 'type': 'species', 'family': family, 'app': app,
               'myspecies_list': myspecies_list, 'myhybrid_list': myhybrid_list,
               'role': role, 'brwspc': 'active', 'author': author,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page, 'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'author_list': author_list,
               'title': 'myphoto_browse',
               'family_list': family_list,
               }
    write_output(request, str(family))
    return render(request, 'common/myphoto_browse_spc.html', context)


# @login_required
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

    family_list = get_family_list()

    context = {'my_list': my_list, 'type': 'hybrid', 'family': family, 'app': app,
               'myspecies_list': myspecies_list, 'myhybrid_list': myhybrid_list,
               'role': role, 'brwhyb': 'active', 'author': author,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page, 'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'author_list': author_list, 'family_list': family_list,
               'title': 'myphoto_browse',
               }
    write_output(request, str(family))
    return render(request, 'common/myphoto_browse_hyb.html', context)


# @login_required
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


# @login_required
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


# @login_required
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
