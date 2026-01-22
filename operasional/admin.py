from django.contrib import admin
from django.db.models import Q, Sum, Count, FloatField, ExpressionWrapper
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.safestring import mark_safe
from .models import LHCabang, DetailLH, PengeluaranLH, SetorPusat, RekapLaporan
from perusahaan.models import Karyawan

def dashboard_hari_ini(request, extra_context=None):
    hari_ini = timezone.localtime(timezone.now()).date()
    
    laporan_induk = LHCabang.objects.filter(tanggal=hari_ini)
    if not request.user.is_superuser:
        laporan_induk = laporan_induk.filter(cabang__kepala_cabang__user=request.user)
    
    detail_laporan = DetailLH.objects.filter(
        laporan_induk__in=laporan_induk, 
        status_kehadiran='H'
    )
    
    context = {
        **admin.site.each_context(request), # Ambil context asli admin secara manual
        'title': 'Hari Ini',
        'total_cabang': laporan_induk.count(),
        'total_karyawan': detail_laporan.count(),
        'total_omzet': detail_laporan.aggregate(total=Sum('omzet_bruto_rp'))['total'] or 0,
        'total_minus': detail_laporan.filter(selisih_rp__lt=0).count(),
    }
    
    if extra_context:
        context.update(extra_context)
    
    # Gunakan TemplateResponse langsung ke index.html
    return TemplateResponse(request, "admin/index.html", context)

# Tetap gunakan ini untuk menimpa halaman utama
admin.site.index = dashboard_hari_ini

class DetailLHInline(admin.TabularInline):     
    model = DetailLH
    extra = 7
    max_num = 8

    readonly_fields = ('display_target', 'display_sisa_rp', 'display_omzet', 'display_selisih', 'display_durasi_kerja')
    
    fields = (
        'mitra', 'status_kehadiran', 'jam_berangkat', 'adonan_bawa_gr', 'display_target',
        'jam_pulang', 'display_durasi_kerja', 'adonan_sisa_gr', 'display_sisa_rp', 'cash_diterima', 
        'potongan_es', 'potongan_gas', 'potongan_obat', 'potongan_qris',
        'display_omzet', 'display_selisih')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "mitra" and not request.user.is_superuser:
            # SUPER KETAT:
            # 1. Harus Mitra
            # 2. Harus Aktif
            # 3. Harus yang bertugas di cabang yang dipimpin oleh user login
            kwargs["queryset"] = Karyawan.objects.filter(
                jabatan__icontains='mitra',
                status='AKTIF',
                cabang_tugas__kepala_cabang__user=request.user
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # semua display di bawah ini, datanya kita ambil langsung dari field database
    def display_target(self, obj):
        if obj.pk:
            return f"Rp {obj.target_minimal_rp:,}"
        return "-"
    display_target.short_description = "Target Minimal"

    def display_durasi_kerja(self, obj):
        if obj.durasi_kerja:
            jam, menit = divmod(obj.durasi_kerja, 60)
            return f"{jam:02d}:{menit:02d} Jam"
        return "-"
    display_durasi_kerja.short_description = "Durasi Kerja"

    def display_sisa_rp(self, obj):
        if obj.pk:
            return f"Rp {obj.nilai_sisa_rp:,}"
        return "-"
    display_sisa_rp.short_description = "Nilai Sisa (Rp)"

    def display_omzet(self, obj):
        if obj.pk:
            return f"Rp {obj.omzet_bruto_rp:,}"
        return "-"
    display_omzet.short_description = "Omzet Ril"

    def display_selisih(self, obj):
        if obj.pk and obj.selisih_rp is not None:
            warna = "orange" if obj.selisih_rp > 0 else "red"
            return mark_safe(f'<b style="color: {warna}">Rp {obj.selisih_rp:,}</b>')
        return "-"
    display_selisih.short_description = "Minus/Lebih"
    
class PengeluaranInline(admin.TabularInline):
    model = PengeluaranLH
    extra = 1
    fields = ('kategori', 'mitra', 'item', 'nominal', 'bukti_nota')

    # Bonus dan Kasbon hanya boleh dari mitra dan kacab yang bertugas
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "mitra":
            resolved = request.resolver_match
            if resolved and 'object_id' in resolved.kwargs:
                laporan_id = resolved.kwargs['object_id']
                laporan = LHCabang.objects.get(pk=laporan_id)

                # Kita ambil Kacab yang terdaftar di tabel Cabang perusahaan
                kacab_cabang = laporan.cabang.kepala_cabang 
                
                # Ambil semua Mitra yang bertugas di tabel atas
                id_mitra_bertugas = DetailLH.objects.filter(
                    laporan_induk=laporan
                ).values_list('mitra_id', flat=True)
                
                # Filter: Hanya Mitra hari itu DAN Kacab pemilik cabang tersebut
                kwargs["queryset"] = Karyawan.objects.filter(
                    Q(id_staff__in=id_mitra_bertugas) | 
                    Q(id_staff=kacab_cabang.id_staff if kacab_cabang else None)
                ).distinct()
            else:
                kwargs["queryset"] = Karyawan.objects.none()                
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
class SetorPusatInline(admin.StackedInline):
    model = SetorPusat
    extra = 1
    max_num = 1
    
    # Kita tampilkan sebagai field baca saja (readonly)
    readonly_fields = ('display_cash', 'display_pengeluaran', 'display_wajib_setor')
    fields = ('display_cash', 'display_pengeluaran', 'display_wajib_setor', 'bukti_transfer')

    def display_cash(self, obj):
        if obj.pk:
            return f"Rp {obj.total_cash_mitra:,}"
        return "-"
    display_cash.short_description = "Total Cash Mitra"

    def display_pengeluaran(self, obj):
        if obj.pk:
            return f"Rp {obj.total_pengeluaran:,}"
        return "-"
    display_pengeluaran.short_description = "Total Pengeluaran"

    def display_wajib_setor(self, obj):
        if obj.pk and obj.nominal_setor is not None:
            nilai = obj.nominal_setor
            html_string = f"""
                <strong id="nominal_copy" style="color: orange; font-size: 16px; margin-right: 10px;">Rp {nilai:,}</strong>
                <button type="button" onclick="navigator.clipboard.writeText('{nilai}')" 
                    style="cursor: pointer; padding: 2px 8px; border-radius: 4px; border: 1px solid #ccc; background: #f8f9fa; font-size: 11px;">
                    📋 Copy
                </button>
            """
            return mark_safe(html_string)
        return "-"
    display_wajib_setor.short_description = "JUMLAH YANG HARUS DITRANSFER"

@admin.register(LHCabang)
class LHCabangAdmin(admin.ModelAdmin):
    list_display = ('tanggal', 'cabang', 'dibuat_oleh')
    inlines = [DetailLHInline, PengeluaranInline, SetorPusatInline]

    # 1. KETAT: Hanya lihat laporan cabang miliknya
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser: 
            return qs
        return qs.filter(cabang__kepala_cabang__user=request.user)

    # 2. KETAT: Saat klik "Add", hanya muncul cabang miliknya di pilihan
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "cabang" and not request.user.is_superuser:
            from perusahaan.models import Cabang
            kwargs["queryset"] = Cabang.objects.filter(kepala_cabang__user=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # 3. OTOMATIS: Catat siapa yang login (ID Staff)
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.dibuat_oleh = request.user
        super().save_model(request, obj, form, change)    

@admin.register(RekapLaporan)
class RekapLaporanAdmin(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        # Ambil input tanggal dari form
        tgl_mulai = request.GET.get('dari')
        tgl_selesai = request.GET.get('sampai')
        hasil = None # jika tgl belum dipilih, maka data kosong

        if tgl_mulai and tgl_selesai:
            data_lh = DetailLH.objects.filter(laporan_induk__tanggal__range=[tgl_mulai, tgl_selesai])
    
            if not request.user.is_superuser:
                data_lh = data_lh.filter(laporan_induk__cabang__kepala_cabang__user=request.user)

            # Menghitung Rekap per Mitra
            rekap_mitra = data_lh.values('mitra__nama_lengkap').annotate(
                total_jam=ExpressionWrapper(
                    Sum('durasi_kerja') / 60.0, 
                    output_field=FloatField()
                ),
                total_minus=Sum('selisih_rp', filter=Q(selisih_rp__lt=0)),
                total_omset=Sum('omzet_bruto_rp'),
                kehadiran=Count('id')
            ).order_by('-total_jam')

            rekap_cabang = data_lh.values('laporan_induk__cabang__nama_cabang').annotate(
                jumlah_berangkat=Count('id')
            ).order_by('-jumlah_berangkat')

            hasil = {
                'rekap_mitra': rekap_mitra,
                'rekap_cabang': rekap_cabang,
            }

        context = {
            **self.admin_site.each_context(request), 
            'title': "Evaluasi Kinerja Mitra",
            'hasil': hasil, # Langsung kirim dictionary hasil yang sudah lengkap
            'tgl_mulai': tgl_mulai,
            'tgl_selesai': tgl_selesai,
        }

        return render(request, 'admin/rekap_dashboard.html', context)