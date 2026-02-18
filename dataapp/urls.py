from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name ='home'),
    path('homepage/', views.home, name ='homedata'),
    
    path('manage_data/', views.managedata, name ='mndata'),
    path('manage_genus/', views.managegenus, name ='genusdata'),
    path('manage_species/', views.managespeci, name ='specidata'),
    path('manage_info/', views.manageinfo, name ='infodata'),

    path('genus_add/', views.addgenus, name ='addgenu'),
    path('genus_delete/<genu_id>/',views.genusdelete, name='genusde'),
    path('genus_update/<int:gn_id>/',views.genusupdate, name='updatege'),
    path('genus_search/',views.genussearch, name='genusearch'),

    path('species_add/', views.addspecies, name ='addspec'),
    path('species_delete/<spec_id>/',views.deletespecies, name='speciesdelete'),
    path('species_update/<int:spec_id>/',views.updatespecies, name='speciesupdate'),
    path('species_search/',views.searchspecies, name='speciessearch'),
    path('species_image/',views.imagespeciesupload, name='speciesimage'),
    path('species_show_image/<int:image_id>/',views.speciesgallery, name='showspeciesgallery'),
    path('species_page/',views.speciesdata, name='pagespecies'),
    path('testadd/', views.testaddspecies, name ='addtest'),
    path('download-images/', views.downloadselectedimages, name='download_selected_images'),
    path('testload_image/<int:image_id>', views.testloadgallery, name ='testload'),
    path('species_detail_page/<int:pk>/', views.speciesfulldetail, name='species_full_detail'),

    path('info_add/', views.addinfomation, name ='addinf'),
    path('info_delete/<k_id>/',views.deleteinfomation, name='knowdelete'),
    path('info_update/<int:k_id>/',views.updateinfomation, name='knowupdate'),
    path('info_search/',views.searchinfo, name='infosearch'),
    path('knowledge_detail/<int:pk>/', views.knowledgedetail, name='knowledge_detail'),

    #path('classify_page',views.plantclassify, name='classify'),
    path('classify_page',views.predictplant, name='classify'),
    path('add_model',views.addmodel, name='addmodel'),
    path('delete_model/<str:filename>/', views.delete_model, name='lostmodel'),
    path('species_show_search/',views.searchspecies2, name='speciessearch2'),
    path('login_form/',views.adminlogincode, name='formlogin'),
    path('add_admin/',views.addadmincode, name='adminadd'),
    path('manage_addmin/',views.manageadmin, name='adminmanage'),
    # เพิ่ม <int:admin_id> เพื่อรับค่า ID จากปุ่มใน HTML
    path('delete_admin/<int:admin_id>/', views.deleteadmin, name='admindelete'),
    path('logout/', views.admin_logout, name='adminlogout'),
]