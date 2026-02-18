from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse
from dataapp.models import Genus
from dataapp.models import Species,KnowledgeInfo,Image,AdminUser
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.hashers import check_password,make_password
import zipfile
import io

import os
import numpy as np
from django.conf import settings
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.vgg16 import preprocess_input
from PIL import Image as PILImage
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
import tensorflow as tf

def admin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if 'admin_id' not in request.session:
            return redirect('formlogin')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def index(request):
    # แก้ไขเป็น /
    return render(request,"dataapp/homepage.html")

def home(request):
    knowledge_info = KnowledgeInfo.objects.all().order_by("info_creator")
    # แก้ไขเป็น /
    return render(request,"dataapp/homepage.html",
        {
            "knowledge": knowledge_info
        }
    )

def managedata(request):
    # แก้ไขเป็น /
    return render(request,"dataapp/manage_data.html")

def managegenus(request):
    gn =Genus.objects.all()
    # แก้ไขเป็น /
    return render(request,"dataapp/manage_genus.html",{"genus":gn})

def managespeci(request):
    sp =Species.objects.all()
    # แก้ไขเป็น /
    return render(request,"dataapp/manage_species.html",{"spi":sp})

def manageinfo(request):
    kn =KnowledgeInfo.objects.all()
    # แก้ไขเป็น /
    return render(request,"dataapp/manage_info.html",{"kno":kn})

def addgenus(request):
    if request.method == "POST":
        gn = request.POST["genus"]
        rm = request.POST["remark"]
        gunusdata = Genus.objects.create(
            genus_name=gn,
            remarks=rm,
        )
        gunusdata.save()
        messages.success(request,"บันทึกข้อมูลเรียบร้อย")
        return redirect("genusdata")
    else :
        # แก้ไขเป็น /
        return render(request,"dataapp/genus_add.html")
    
def genusdelete(request,genu_id):
    gn = Genus.objects.get(genus_id=genu_id)
    gn.delete()
    messages.success(request,"ลบข้อมูลเรียบร้อย")
    return redirect("genusdata")

def genusupdate(request,gn_id):
    if request.method == "POST":
        gn = Genus.objects.get(genus_id=gn_id)
        gn.genus_name = request.POST["genusname"]
        gn.remarks = request.POST["remark"]
        gn.save()
        messages.success(request,"อัพเดตข้อมูลเรียบร้อย")
        return redirect("genusdata")
    else:
        gn = Genus.objects.get(genus_id=gn_id)
        # แก้ไขเป็น /
        return render(request, "dataapp/genus_update.html",{"gen":gn})
    
def genussearch(request):
        q = request.GET.get("name", "")
        genus = Genus.objects.filter(genus_name__icontains=q)
        # แก้ไขเป็น /
        return render(request,"dataapp/genus_search.html",{
            "genus": genus,
            "name": q,
        }
    )

def addspecies(request):
    gn = Genus.objects.all()
    if request.method == "POST":
        sn = request.POST["sciname"]
        tn = request.POST["thainame"]
        at = request.POST["attri"]
        genu = request.POST["typegenus"]
        sp = Species.objects.create(
            sci_name=sn,
            thai_name=tn,
            description=at,
            genus_id=genu
        )
        sp.save()
        messages.success(request,"บันทึกข้อมูลเรียบร้อย")
        return redirect("specidata")
    else :
        # แก้ไขเป็น /
        return render(request,"dataapp/species_add.html",{"genus":gn})
    
def deletespecies(request,spec_id):
    sp = Species.objects.get(species_id=spec_id)
    sp.delete()
    messages.success(request,"ลบข้อมูลเรียบร้อย")
    return redirect("specidata")

def updatespecies(request,spec_id):
    if request.method == "POST":
        genus=Genus.objects.all()
        spec = Species.objects.get(species_id=spec_id)
        spec.sci_name = request.POST["sciname"]
        spec.thai_name = request.POST["thainame"]
        spec.description = request.POST["descri"]
        spec.genus_id = request.POST["typegenus"]
        spec.save()
        messages.success(request,"อัพเดตข้อมูลเรียบร้อย")
        return redirect("specidata")
    else:
        speci = Species.objects.get(species_id=spec_id)
        genus=Genus.objects.all()
        # แก้ไขเป็น /
        return render(request, "dataapp/species_update.html",{"sp":speci, "gn":genus})

def searchspecies(request):
    query = request.GET.get("message", "")
    results = Species.objects.select_related('genus').all()
    if query:
        results = results.filter(
            Q(thai_name__icontains=query) |
            Q(sci_name__icontains=query)  |
            Q(description__icontains=query)|
            Q(genus__genus_name__icontains=query)
        )
    # แก้ไขเป็น /
    return render(request,"dataapp/species_search.html",
        {
            "species": results,
            "query": query
        }
    )

def imagespeciesupload(request):
    species_list = Species.objects.all()
    if request.method == "POST":
        sp_id = request.POST["speciesid"]
        images = request.FILES.getlist("imagesid")
        if not sp_id:
            messages.error(request, "กรุณาเลือกสายพันธุ์")
            return redirect(request.path)
        sp = Species.objects.get(pk=sp_id)
        if not images:
            messages.error(request, "กรุณาเลือกรูปภาพ")
            return redirect(request.path)
        if len(images) > 30:
            messages.error(request, "อัปโหลดได้ไม่เกิน 30 รูปต่อครั้ง")
            return redirect(request.path)
        current_count = sp.images.count()
        if current_count + len(images) > 1000:
            messages.error(
                request,
                f"สายพันธุ์นี้มีรูปแล้ว {current_count} รูป (รวมทั้งหมดต้องไม่เกิน 1000)"
            )
            return redirect(request.path)
        for img in images:
            Image.objects.create(
                species=sp,
                speciesimage=img
            )
        messages.success(request, "อัปโหลดรูปภาพเรียบร้อย")
        return redirect("specidata")
    # แก้ไขเป็น /
    return render(
        request,
        "dataapp/species_image.html",
        {"species": species_list}
    )

def speciesgallery(request, image_id):
    spec = get_object_or_404(Species, pk=image_id)
    images = spec.images.all() 
    # แก้ไขเป็น /
    return render(request, 'dataapp/species_show_image.html', {
        'species': spec,
        'images': images
    })

def testloadgallery(request, image_id):
    spec = get_object_or_404(Species, pk=image_id)
    images = spec.images.all() 
    # แก้ไขเป็น /
    return render(request, 'dataapp/testload_image.html', {
        'species': spec,
        'images': images
    })

def speciesfulldetail(request, pk):
    plant = get_object_or_404(Species, pk=pk)
    # แก้ไขเป็น /
    return render(request, 'dataapp/species_detail_page.html', {'plant': plant})

def plantclassify(request):
    # แก้ไขเป็น /
    return render(request,"dataapp/classify_page.html")

def addinfo(request):
    # แก้ไขเป็น /
    return render(request,"dataapp/info_add.html")

def addinfomation(request):
    if request.method == "POST":
        inhea = request.POST["heading"]
        inct = request.POST["infocontent"]
        inb = request.POST["infoby"]
        ind = request.POST["infodate"]
        inim = request.FILES["infoimage"]
        knowdata = KnowledgeInfo.objects.create(
            info_headline=inhea,
            info_content=inct,
            info_creator=inb,
            info_date=ind,
            info_image=inim,
        )
        knowdata.save()
        messages.success(request,"บันทึกข้อมูลเรียบร้อย")
        return redirect("infodata")
    else :
        # แก้ไขเป็น /
        return render(request,"dataapp/info_add.html")
    
def deleteinfomation(request,k_id):
    knl = KnowledgeInfo.objects.get(info_id=k_id)
    knl.delete()
    messages.success(request,"ลบข้อมูลเรียบร้อย")
    return redirect("infodata")

def updateinfomation(request,k_id):
    if request.method == "POST":
        knl = KnowledgeInfo.objects.get(info_id=k_id)
        knl.info_content = request.POST["infocontent"]
        knl.info_creator = request.POST["infoby"]
        knl.info_date = request.POST["infodate"]
        if "infoimage" in request.FILES:
            knl.info_image = request.FILES["infoimage"]
        knl.save()
        messages.success(request,"อัพเดตข้อมูลเรียบร้อย")
        return redirect("infodata")
    else:
        knl = KnowledgeInfo.objects.get(info_id=k_id)
        # แก้ไขเป็น /
        return render(request, "dataapp/info_update.html",{"kn":knl})

def searchinfo(request):
    query = request.GET.get("message", "")
    results = KnowledgeInfo.objects.all()
    if query:
        results = results.filter(
            Q(info_content__icontains=query) |
            Q(info_creator__icontains=query)  
        )
    # แก้ไขเป็น /
    return render(request,"dataapp/info_search.html",
        {
            "kno": results,
            "query": query
        }
    )

def knowledgedetail(request, pk):
    item = get_object_or_404(KnowledgeInfo, pk=pk)
    # แก้ไขเป็น /
    return render(request, 'dataapp/knowledge_detail.html', {'item': item})

def speciesdata(request):
    species_list = Species.objects.all() 
    # แก้ไขเป็น /
    return render(request, "dataapp/species_page.html", {
        "species_list": species_list
    })

def testaddspecies(request):
    gn = Genus.objects.all()
    if request.method == "POST":
        sn = request.POST["sciname"]
        tn = request.POST["thainame"]
        at = request.POST["attri"]
        genu = request.POST["typegenus"]
        images = request.FILES.getlist("imagesid") 
        if len(images) > 30:
            messages.error(request, "อัปโหลดได้ไม่เกิน 30 รูป")
            return render(request, "dataapp/testadd.html", {"genus": gn})
        sp = Species.objects.create(
            sci_name=sn,
            thai_name=tn,
            description=at,
            genus_id=genu
        )
        if images:
            for img in images:
                Image.objects.create(
                    species=sp,
                    speciesimage=img
                )
        messages.success(request, f"บันทึกข้อมูล '{tn}' และรูปภาพ {len(images)} รูป เรียบร้อยแล้ว")
        return redirect("specidata")
    else:
        # แก้ไขเป็น /
        return render(request, "dataapp/testadd.html", {"genus": gn})

def get_latest_model():
    # ในฟังก์ชันจัดการไฟล์ Linux จะใช้ / หรือแนะนำให้ใช้ os.path.join เพื่อความปลอดภัยสูงสุด
    save_path = os.path.join(settings.BASE_DIR, 'dataapp', 'ml_models')
    for ext in ['.keras', '.h5']:
        path = os.path.join(save_path, f'classify_plant_model{ext}')
        if os.path.exists(path):
            return path
    return None

CLASS_NAMES = ['กระพี้นางนวล', 'พะยูง', 'เกร็ดแดง', 'เครือคางควาย', 'เครือแมด']

def predictplant(request):
    result = None
    confidence = None
    image_url = None 
    if request.method == 'POST' and request.FILES.get('plant_image'):
        try:
            img_file = request.FILES['plant_image']
            fs = FileSystemStorage()
            filename = fs.save(img_file.name, img_file)
            image_url = fs.url(filename) 
            
            model_path = get_latest_model()
            if not model_path:
                result = "ไม่พบไฟล์โมเดลในระบบ (.h5 หรือ .keras)"
            else:
                # ✅ 1. ใช้ tf.keras.models.load_model แทน และเพิ่ม compile=False แก้ Error ที่พีทเจอ
                model = tf.keras.models.load_model(model_path, compile=False)
                
                img = PILImage.open(fs.path(filename)).convert("RGB")
                img = img.resize((224, 224))

                # ✅ 2. เปลี่ยนมาใช้ tf.keras.preprocessing.image แทนการเรียก image เฉยๆ
                img_array = tf.keras.preprocessing.image.img_to_array(img)
                img_array = np.expand_dims(img_array, axis=0)
                
                # ✅ 3. ใช้ preprocess_input ตามที่ import ไว้ (หรือ tf.keras.applications.vgg16.preprocess_input)
                img_array = tf.keras.applications.vgg16.preprocess_input(img_array)

                predictions = model.predict(img_array)
                result_index = np.argmax(predictions[0])

                if result_index < len(CLASS_NAMES):
                    result = CLASS_NAMES[result_index]
                    confidence = f"{np.max(predictions[0]) * 100:.2f}%"
                else:
                    result = "ไม่ทราบชนิด"
                    
        except Exception as e:
            # พิมพ์ Error ออกมาดูใน Log ของ Render ด้วย
            print(f"Prediction Error: {e}")
            result = f"เกิดข้อผิดพลาด: {str(e)}"
            
    return render(request, 'dataapp/classify_page.html', {
            'result': result,
            'confidence': confidence,
            'image_url': image_url,
        })

def testaddmodel(request):
    # แก้ไขเป็น /
    return render(request,"dataapp/add_model.html")

def addmodel(request):
    save_path = os.path.join(settings.BASE_DIR, 'dataapp', 'ml_models')
    model_files = []
    if os.path.exists(save_path):
        model_files = [f for f in os.listdir(save_path) 
                       if f.startswith('classify_plant_model') and f.lower().endswith(('.h5', '.keras'))]
    if request.method == 'POST' and request.FILES.get('new_model'):
        new_model_file = request.FILES['new_model']
        extension = os.path.splitext(new_model_file.name)[1].lower()
        if extension not in ['.h5', '.keras']:
            return redirect('addmodel')
        for old_file in os.listdir(save_path):
            if old_file.startswith('classify_plant_model'):
                os.remove(os.path.join(save_path, old_file))
        filename = f'classify_plant_model{extension}'
        fs = FileSystemStorage(location=save_path)
        fs.save(filename, new_model_file)
        return redirect('addmodel')
    # แก้ไขเป็น /
    return render(request, 'dataapp/add_model.html', {
        'model_files': model_files
    })

def searchspecies2(request):
    query = request.GET.get("alltext", "")
    results = Species.objects.select_related('genus').all()
    if query:
        results = results.filter(
            Q(thai_name__icontains=query) |
            Q(sci_name__icontains=query)  |
            Q(description__icontains=query)|
            Q(genus__genus_name__icontains=query)
        )
    # แก้ไขเป็น /
    return render(request,"dataapp/species_show_search.html",
        {
            "species": results,
            "query": query
        }
    )

def login(request):
    # แก้ไขเป็น /
    return render(request,"dataapp/login_form.html")

def adminlogin(request):
    if request.method == "POST":
        user_in = request.POST.get('username')
        pass_in = request.POST.get('password')
        try:
            admin = AdminUser.objects.get(user_name=user_in)
            if pass_in == admin.password: 
                request.session['admin_id'] = admin.admin_id
                request.session['admin_name'] = admin.full_name
                admin.last_login = timezone.now()
                admin.save()
                return redirect('mndata')
            else:
                messages.error(request, "รหัสผ่านไม่ถูกต้อง")
        except AdminUser.DoesNotExist:
            messages.error(request, "ไม่พบชื่อผู้ใช้งาน")
    # แก้ไขเป็น /
    return render(request, 'dataapp/login_form.html')

@admin_required
def managedata2(request):
    # แก้ไขเป็น /
    return render(request, 'dataapp/manage_data.html')

def addadmin(request):
    if request.method == "POST":
        u_name = request.POST.get('user_name')
        p_word = request.POST.get('password')
        f_name = request.POST.get('full_name')
        if AdminUser.objects.filter(user_name=u_name).exists():
            messages.error(request, "ชื่อผู้ใช้งานนี้มีอยู่ในระบบแล้ว")
        else:
            new_admin = AdminUser(
                user_name=u_name,
                password=p_word,
                full_name=f_name
            )
            new_admin.save()
            messages.success(request, f"เพิ่มคุณ {f_name} เป็นผู้ดูแลระบบเรียบร้อยแล้ว")
            return redirect('mndata')
    # แก้ไขเป็น /
    return render(request, 'dataapp/add_admin.html')

@admin_required
def manageadmin(request):
    admins = AdminUser.objects.all() 
    # แก้ไขเป็น /
    return render(request, 'dataapp/manage_admin.html', {'admins': admins})

def downloadselectedimages(request):
    if request.method == "POST":
        selected_ids = request.POST.getlist('selected_images')
        
        # ตรวจสอบว่ามีการเลือกรูปจริงไหม
        if not selected_ids:
            return HttpResponse("กรุณาเลือกรูปภาพอย่างน้อย 1 รูป")

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zip_file:
            # ดึงข้อมูลรูปภาพ (ตรวจสอบชื่อฟิลด์ id ให้ตรงกับ Model ของคุณ)
            images = Image.objects.filter(id__in=selected_ids)
            
            for img in images:
                if img.speciesimage and os.path.exists(img.speciesimage.path):
                    file_path = img.speciesimage.path
                    file_name = os.path.basename(file_path)
                    # เขียนไฟล์ลงใน ZIP
                    zip_file.write(file_path, file_name)
                else:
                    # กรณีหาไฟล์จริงในเครื่องไม่เจอ
                    print(f"File not found: {img.speciesimage.name}")

        # สำคัญ: ต้องอยู่หลังปิด with zip_file
        buffer.seek(0)
        
        # ตรวจสอบขนาดของ buffer ถ้าเป็น 0 แสดงว่าไม่มีไฟล์ถูกเขียนลงไป
        if buffer.getbuffer().nbytes == 0:
            return HttpResponse("ไม่สามารถสร้างไฟล์ ZIP ได้เนื่องจากไม่พบไฟล์ต้นฉบับในระบบ")

        response = HttpResponse(buffer, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="plants_collection.zip"'
        return response
    
# ฟังก์ชันสำหรับลบโมเดล
def delete_model(request, filename):
    if request.method == 'POST':
        file_path = os.path.join(settings.BASE_DIR, 'dataapp', 'ml_models', filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            messages.success(request, f'ลบไฟล์ {filename} เรียบร้อยแล้ว')
        else:
            messages.error(request, 'ไม่พบไฟล์ที่ต้องการลบ')
    return redirect('addmodel')

def adminlogincode(request):
    if request.method == "POST":
        user_in = request.POST.get('username')
        pass_in = request.POST.get('password')

        try:
            admin = AdminUser.objects.get(user_name=user_in)
            # ตรวจสอบโดยการคำนวณเปรียบเทียบ
            if check_password(pass_in, admin.password):
                request.session['admin_id'] = admin.admin_id
                admin.last_login = timezone.now()
                admin.save()
                return redirect('mndata')
            else:
                messages.error(request, "รหัสผ่านไม่ถูกต้อง")
        except AdminUser.DoesNotExist:
            messages.error(request, "ไม่พบชื่อผู้ใช้งานนี้")
            
    return render(request, 'dataapp/login_form.html')

def addadmincode(request):
    if request.method == "POST":
        u_name = request.POST.get('user_name')
        p_word = request.POST.get('password')
        f_name = request.POST.get('full_name')

        if AdminUser.objects.filter(user_name=u_name).exists():
            messages.error(request, "ชื่อผู้ใช้งานนี้มีคนใช้แล้ว")
        else:
            # เข้ารหัสก่อนบันทึกลง MySQL
            hashed_p = make_password(p_word) 
            AdminUser.objects.create(
                user_name=u_name, 
                password=hashed_p, 
                full_name=f_name
            )
            messages.success(request, "เพิ่มแอดมินใหม่สำเร็จ!")
            return redirect('adminadd')
    return render(request, 'dataapp/add_admin.html')

@admin_required
def deleteadmin(request, admin_id):
    # ป้องกันไม่ให้แอดมินลบตัวเอง (ทางเลือก)
    if admin_id == request.session.get('admin_id'):
        messages.error(request, "คุณไม่สามารถลบบัญชีของตัวเองได้ในขณะที่ใช้งานอยู่")
        return redirect('adminmanage')

    try:
        admin = AdminUser.objects.get(admin_id=admin_id)
        admin.delete()
        messages.success(request, "ลบข้อมูลผู้ดูแลระบบเรียบร้อยแล้ว")
    except AdminUser.DoesNotExist:
        messages.error(request, "ไม่พบข้อมูลที่ต้องการลบ")
        
    return redirect('adminmanage')

def admin_logout(request):
    # ล้างข้อมูล Session ทั้งหมด (admin_id, admin_name ฯลฯ)
    request.session.flush()
    # ส่งข้อความแจ้งเตือน (ถ้าต้องการ)
    messages.success(request, "ออกจากระบบเรียบร้อยแล้ว")
    # ดีดกลับไปหน้า Login
    return redirect('formlogin')






