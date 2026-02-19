from django.contrib import admin
from dataapp.models import Genus
from dataapp.models import Species,KnowledgeInfo,Image,AdminUser
# Register your models here.

admin.site.register(Genus)
admin.site.register(Species)
admin.site.register(AdminUser)
admin.site.register(KnowledgeInfo)
admin.site.register(Image)