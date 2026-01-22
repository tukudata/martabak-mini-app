from django.contrib import admin

# Register your models here.
from .models import AturanPerusahaan, TierBonusMitra, TierBonusCabang

class TierBonusMitraInline(admin.TabularInline):
    model = TierBonusMitra
    extra = 1

class TierBonusCabangInline(admin.TabularInline):
    model = TierBonusCabang
    extra = 1

@admin.register(AturanPerusahaan)
class AturanPerusahaanAdmin(admin.ModelAdmin):
    inlines = [TierBonusMitraInline, TierBonusCabangInline]
    
    fieldsets = (
        ('Info Dasar', {'fields': ('nama_aturan',)}),
        ('Parameter Produksi', {'fields': ('konstanta_adonan_jadi', 'harga_per_gram_target')}),
        ('Skema Gaji', {'fields': ('gaji_pokok_training', 'gaji_pokok_tetap', 'insentif_kehadiran')}),
    )

    def has_add_permission(self, request):
        return False if AturanPerusahaan.objects.exists() else True