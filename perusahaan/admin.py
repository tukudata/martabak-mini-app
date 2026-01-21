from django.contrib import admin
from .models import Departemen, Karyawan, Cabang

@admin.register(Departemen)
class DepartemenAdmin(admin.ModelAdmin):
    list_display = ('kode_departemen', 'nama_departemen')

@admin.register(Karyawan)
class KaryawanAdmin(admin.ModelAdmin):
    list_display = ('id_staff', 'nama_lengkap', 'nomor_hp', 'jabatan', 'cabang_tugas')
    list_filter = ('jabatan', 'cabang_tugas') # filter dropdown
    search_fields = ('id_staff', 'nama_lengkap', 'nomor_hp') # kolom search
    
@admin.register(Cabang)
class CabangAdmin(admin.ModelAdmin):
    list_display = ('kode_cabang', 'nama_cabang', 'kepala_cabang')
    search_fields = ('kode_cabang', 'nama_cabang',
                     'kepala_cabang__id_staff', # foreign key di sf tidak boleh langsung
                     'kepala_cabang__nama_lengkap')     # 'kepala_cabang_

# --- GRAFIK CHART ---
original_index = admin.site.index

def custom_index(request, extra_context=None):
    extra_context = extra_context or {}
    
    # Masukkan data ke Dashboard
    extra_context['total_cabang'] = Cabang.objects.count()
    extra_context['total_karyawan'] = Karyawan.objects.count()
    extra_context['total_departemen'] = Departemen.objects.count()
    
    # Jalankan index yang asli tapi dengan data tambahan kita
    return original_index(request, extra_context)

# Timpa fungsi index milik admin default tanpa merusak registrasi model/sidebar
admin.site.index = custom_index
