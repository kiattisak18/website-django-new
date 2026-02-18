from django.db import models

# Create your models here.
class Genus(models.Model):
    genus_id = models.AutoField(primary_key=True)
    genus_name = models.CharField(max_length=100)
    remarks = models.CharField(max_length=200, blank=True, null=True)
    def __str__(self):
        return self.genus_name

class Species(models.Model):
    species_id = models.AutoField(primary_key=True)
    sci_name = models.CharField(max_length=200)
    thai_name = models.CharField(max_length=200, null=True)
    description = models.TextField(null=True)
    genus = models.ForeignKey(Genus,on_delete=models.SET_NULL,null=True,blank=True)
    def __str__(self):
        return self.sci_name
    
class KnowledgeInfo(models.Model):
    info_id = models.AutoField(primary_key=True)
    info_headline = models.CharField(max_length=200)
    info_content = models.TextField(null=True)
    info_creator = models.CharField(max_length=100)
    info_date = models.DateField()
    info_image = models.ImageField(
        upload_to='knowledge_images/',
        blank=True,
        null=True
    )
    def __str__(self):
        return self.info_content

class Image(models.Model):
    species = models.ForeignKey(Species,on_delete=models.SET_NULL,null=True,blank=True,
        related_name="images"
    )
    
    speciesimage = models.ImageField(upload_to="species_images/")
    def __str__(self):
        return self.speciesimage.name

class AdminUser(models.Model):
    admin_id = models.AutoField(primary_key=True)
    user_name = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=255)  # สำหรับเก็บรหัสที่ผ่านการ Hashing
    full_name = models.CharField(max_length=200)
    last_login = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        return self.user_name



