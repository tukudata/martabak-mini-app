from django.db import models

# Create your models here.
class AturanPerusahaan(models.Model):
    nama_aturan = models.CharField(max_length=100, default="Konfigurasi Utama")
    
    # Produksi
    konstanta_adonan_jadi = models.FloatField(default=2.5)
    harga_per_gram_target = models.FloatField(default=92.0)
    
    # Gaji & Insentif
    gaji_pokok_training = models.FloatField(default=1800000)
    gaji_pokok_tetap = models.FloatField(default=2000000)
    insentif_kehadiran = models.FloatField(default=150000)

    class Meta:
        verbose_name_plural = verbose_name_plural = "Aturan Perusahaan"

    def __str__(self):
        return self.nama_aturan

class TierBonusMitra(models.Model):
    aturan = models.ForeignKey(AturanPerusahaan, on_delete=models.CASCADE, related_name='bonus_mitra')
    min_omset_harian = models.FloatField()
    nominal_bonus_pekanan = models.FloatField()

class TierBonusCabang(models.Model):
    aturan = models.ForeignKey(AturanPerusahaan, on_delete=models.CASCADE, related_name='bonus_cabang')
    min_mitra_berangkat = models.IntegerField()
    nominal_bonus_cabang = models.FloatField()