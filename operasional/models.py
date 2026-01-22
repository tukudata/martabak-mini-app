from django.db import models
from django.db.models import Q
from django.dispatch import receiver
from django.core.exceptions import ValidationError # edit pesan error
from django.utils import timezone
import io
from PIL import Image
from perusahaan.models import Karyawan, Cabang
from sistem.models import AturanPerusahaan

class LHCabang(models.Model):
    cabang = models.ForeignKey(Cabang, on_delete=models.CASCADE)
    tanggal = models.DateField(default=timezone.now)

    dibuat_oleh = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        editable=False # Supaya tidak muncul di form input (otomatis)
    )
    
    class Meta:
        verbose_name_plural = "Laporan Harian"
        unique_together = ('cabang', 'tanggal')

    def __str__(self):
        return f"{self.cabang} - {self.tanggal}"

class DetailLH(models.Model):
    laporan_induk = models.ForeignKey(LHCabang, related_name='detail_lh', on_delete=models.CASCADE)
    mitra = models.ForeignKey(Karyawan, on_delete=models.PROTECT, limit_choices_to={'jabatan__icontains': 'mitra'})

    STATUS_KEHADIRAN = [
        ('H', 'Hadir'),
        ('S', 'Sakit'),
        ('I', 'Izin'),
        ('A', 'Alfa'),
    ]

    # --- PAGI ---
    status_kehadiran = models.CharField(max_length=1, choices=STATUS_KEHADIRAN, default='H')
    jam_berangkat = models.TimeField(null=True, blank=True)
    adonan_bawa_gr = models.PositiveIntegerField(default=0, help_text="Dalam Gram")
    
    # --- SORE ---
    jam_pulang = models.TimeField(null=True, blank=True)
    adonan_sisa_gr = models.PositiveIntegerField(default=0, help_text="Dalam Gram")
    nilai_sisa_rp = models.PositiveIntegerField(default=0, editable=False)
    cash_diterima = models.PositiveIntegerField(default=0)
    potongan_es = models.PositiveIntegerField(default=0)
    potongan_gas = models.PositiveIntegerField(default=0)
    potongan_parkir = models.PositiveIntegerField(default=0)
    potongan_qris = models.PositiveIntegerField(default=0)

    # --- KOLOM DATABASE (HASIL HITUNG PERMANEN) ---
    target_minimal_rp = models.PositiveIntegerField(default=0, editable=False)
    omzet_bruto_rp = models.PositiveIntegerField(default=0, editable=False)
    selisih_rp = models.IntegerField(default=0, editable=False)
    durasi_kerja = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        verbose_name_plural = "Detail LH"

    ##### ISTIRAHATKAN MATA DULU DI SINI ####

    def get_aturan(self):
        aturan = AturanPerusahaan.objects.first()
        if not aturan:
            return {'harga': 92}  # Langsung angka saja
        return {'harga': aturan.harga_per_gram_target}

    # Validasi: Cek apakah mitra sudah diinput di tanggal yang sama
    def clean(self):
        # Guard clause: pastikan data yang dibutuhkan ada
        if not (self.mitra and self.laporan_induk):
            return
        # Ambil data duplikat dalam 1 query (select_related)
        duplikat = DetailLH.objects.filter(
            mitra=self.mitra, 
            laporan_induk__tanggal=self.laporan_induk.tanggal
        ).exclude(pk=self.pk).select_related('laporan_induk__cabang').first()
        # Jika ditemukan duplikat, susun pesan erornya
        if duplikat:
            induk_lama = duplikat.laporan_induk
            induk_baru = self.laporan_induk
            # Logika pesan simpel: Jika di cabang sama vs cabang berbeda
            if induk_lama.cabang == induk_baru.cabang:
                msg = f"sudah terdaftar di laporan ini."
            else:
                msg = f"sedang bertugas di {induk_lama.cabang.nama_cabang}."
            raise ValidationError(f"Maaf, {self.mitra.nama_lengkap} {msg} Mohon periksa kembali.")
            
    def save(self, *args, **kwargs):
        self.full_clean() # cek semua data sebelum masukkan data baru

        # --- JIKA MITRA TIDAK HADIR ---
        if self.status_kehadiran != 'H':
            # Nol kan semua field angka
            for field in ['adonan_bawa_gr', 'adonan_sisa_gr', 'cash_diterima', 'potongan_es', 
                          'potongan_gas', 'potongan_parkir', 'potongan_qris']: setattr(self, field, 0)
            # Set durasi kerja langsung ke "-"
            self.durasi_kerja = 0

        # ambil harga per gr
        aturan = self.get_aturan()
        harga = aturan['harga']

        self.target_minimal_rp = (self.adonan_bawa_gr or 0) * harga       

        potongan = [
            self.cash_diterima, self.potongan_es, self.potongan_gas, 
            self.potongan_parkir, self.potongan_qris
        ]
        self.omzet_bruto_rp = sum(p or 0 for p in potongan)
        
        self.nilai_sisa_rp = (self.adonan_sisa_gr or 0) * harga
        self.selisih_rp = (self.omzet_bruto_rp + self.nilai_sisa_rp) - self.target_minimal_rp

        # Hitung Durasi Kerja
        if self.jam_berangkat and self.jam_pulang:
            mulai = self.jam_berangkat.hour * 60 + self.jam_berangkat.minute
            selesai = self.jam_pulang.hour * 60 + self.jam_pulang.minute
            selisih_menit = selesai - mulai
            self.durasi_kerja = selisih_menit if selisih_menit > 0 else 0
        else:
            self.durasi_kerja = 0

        super().save(*args, **kwargs) #masukkan ke database

class PengeluaranLH(models.Model):
    # Pilihan kategori agar admin tidak typo saat input
    KATEGORI_PILIHAN = [
        ('OPERASIONAL', 'Operasional'),
        ('MAINTENANCE', 'Perbaikan Gerobak'),
        ('KASBON', 'Kasbon'),
        ('BONUS', 'Bonus Pekanan'),
        ('TRAINING', 'Uang Training'),
        ('KONSUMSI', 'Makan Bulanan'),
        ('LAINNYA', 'Lain-lain'),
    ]

    laporan_induk = models.ForeignKey(LHCabang, related_name='pengeluaran_op', on_delete=models.CASCADE)
    kategori = models.CharField(max_length=20, choices=KATEGORI_PILIHAN, default='OPERASIONAL')
    mitra = models.ForeignKey('perusahaan.Karyawan', on_delete=models.SET_NULL, null=True, blank=True,
        limit_choices_to=Q(jabatan__icontains='mitra') | Q(jabatan__icontains='kepala cabang'),
        help_text="Klik 'Save and Continue Editing' agar daftar mitra yang bertugas hari ini muncul."
    )
    item = models.CharField(max_length=100, null=True, blank=True, help_text="Contoh: Air Galon / Kasbon Agus")
    nominal = models.PositiveIntegerField(default=0)
    bukti_nota = models.ImageField(upload_to='nota_cabang/%Y/%m/', null=True, blank=True)

    # kompres foto
    def save(self, *args, **kwargs):
        if self.bukti_nota:
            img = Image.open(self.bukti_nota)

            if img.mode in ("RGBA", "P"): #jika file PNG, ubah ke RGB
                img = img.convert("RGB")
            output = io.BytesIO() #kompres foto

            # Resize jika lebih lebar dari 1200px
            max_width = 1200
            if img.width > max_width:
                ratio = max_width / float(img.width)
                new_height = int(float(img.height) * float(ratio))
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

            # Masukkan kembali ke field bukti_transfer
            img.save(output, format='JPEG', quality=70, optimize=True)
            output.seek(0)

            # Masukkan kembali ke field bukti_transfer
            self.bukti_nota = ContentFile(output.read(), name=self.bukti_nota.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Pengeluaran"

class SetorPusat(models.Model):
    laporan_induk = models.OneToOneField(LHCabang, on_delete=models.CASCADE, related_name='setoran_pusat')
    total_cash_mitra = models.PositiveIntegerField(default=0)
    total_pengeluaran = models.PositiveIntegerField(default=0)
    nominal_setor = models.PositiveIntegerField(default=0)
    bukti_transfer = models.ImageField(upload_to='setoran_pusat/%Y/%m/')

    def save(self, *args, **kwargs):
        # PROTEKSI: Jika tidak ada bukti transfer, jangan simpan apapun ke tabel ini
        if not self.bukti_transfer:
            return # Batalkan proses simpan
            
        # Jika ada foto, baru jalankan hitungan untuk "mengunci" angka ke database
        from django.db.models import Sum
        cash = self.laporan_induk.detail_lh.aggregate(total=Sum('cash_diterima'))['total'] or 0
        keluar = self.laporan_induk.pengeluaran_op.aggregate(total=Sum('nominal'))['total'] or 0
        
        self.total_cash_mitra = cash
        self.total_pengeluaran = keluar
        self.nominal_setor = cash - keluar
        
        ## -- KOMPRES FOTO --
        if self.bukti_transfer:
            img = Image.open(self.bukti_transfer)

            if img.mode in ("RGBA", "P"): #jika file PNG, ubah ke RGB
                img = img.convert("RGB")
            output = io.BytesIO() #kompres foto

            # Resize jika lebih lebar dari 1200px
            max_width = 1200
            if img.width > max_width:
                ratio = max_width / float(img.width)
                new_height = int(float(img.height) * float(ratio))
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

            # Simpan dengan kompresi JPEG
            img.save(output, format='JPEG', quality=70, optimize=True)
            output.seek(0)

            # Masukkan kembali ke field bukti_transfer
            self.bukti_transfer = ContentFile(output.read(), name=self.bukti_transfer.name)

        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Setor Harian"

class RekapLaporan(models.Model):
    class Meta:
        verbose_name_plural = "Rekap Laporan"
        managed = False  # Penting: Django tidak akan buat tabel di database