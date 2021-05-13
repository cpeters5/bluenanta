from django.urls import path, re_path
from . import views

app_name = 'common'
urlpatterns = [
    # Top level
    # path('', orchid_home, name='orchid_home'),


    # path('taxonomy/', views.taxonomy, name='taxonomy'),
    path('genera/', views.genera, name='genera'),
    path('species/', views.species, name='species'),
    path('hybrid/', views.hybrid, name='hybrid'),
    path('information/<int:pid>/', views.information, name='information'),
    path('photos/<int:pid>/', views.photos, name='photos'),
    path('browse/', views.browse, name='browse'),
    # path('advanced/', views.advanced, name='advanced'),
    # path('search_genus/', views.search_genus, name='search_genus'),
    path('search_species/', views.search_species, name='search_species'),
    # path('search_match/', views.search_match, name='search_match'),
    # path('search_fuzzy/', views.search_fuzzy, name='search_fuzzy'),

    path('deletephoto/<int:orid>/<int:pid>/', views.deletephoto, name='deletephoto'),
    path('deletewebphoto/<int:pid>/', views.deletewebphoto, name='deletewebphoto'),
    path('approvemediaphoto/<int:pid>/', views.approvemediaphoto, name='approvemediaphoto'),

    path('curate_newupload/', views.curate_newupload, name='curate_newupload'),
    path('curate_pending/', views.curate_pending, name='curate_pending'),
    path('curate_newapproved/', views.curate_newapproved, name='curate_newapproved'),

    path('myphoto/<int:pid>/', views.myphoto, name='myphoto'),
    path('myphoto/', views.myphoto, name='myphoto'),
    path('myphoto_browse_spc/', views.myphoto_browse_spc, name='myphoto_browse_spc'),
    path('myphoto_browse_hyb/', views.myphoto_browse_hyb, name='myphoto_browse_hyb'),

]
