from django.db import models
from django.contrib.auth.models import User

class Departemen(models.Model):
    kode_departemen = models.CharField(max_length=10, primary_key=True) # pk
    nama_departemen = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.kode_departemen} - {self.nama_departemen}"
    
    class Meta:
        verbose_name_plural = "Departemen"

class Karyawan(models.Model):
    STATUS_PILIHAN = [
        ('AKTIF', 'Aktif'),
        ('RESIGN', 'Resign'),
        ('CUTI', 'Cuti'),
    ]
    
    # user adalah logika login
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    id_staff = models.CharField(max_length=10, primary_key=True,
                                blank=True, # Di Form Admin boleh kosong
                                help_text="ID Staff otomatis dibuatkan oleh sistem.")
    nama_lengkap = models.CharField(max_length=255)
    nomor_hp = models.CharField(max_length=15, unique=True)
    departemen = models.ForeignKey(Departemen, on_delete=models.SET_NULL, null=True) # on delete penting banget
    jabatan = models.CharField(max_length=100)
    tanggal_masuk = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_PILIHAN, default='AKTIF')
    cabang_tugas = models.ForeignKey('Cabang', on_delete=models.SET_NULL, null=True, blank=True, related_name='staff_cabang')

    def save(self, *args, **kwargs):
        if not self.id_staff:
            # Menggunakan count() sebagai basis nomor urut
            nomor_baru = Karyawan.objects.count() + 1
            while Karyawan.objects.filter(id_staff=f'DS{nomor_baru:04d}').exists():
                nomor_baru += 1
            self.id_staff = f'DS{nomor_baru:04d}'
        super(Karyawan, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.id_staff} - {self.nama_lengkap}"
    
    class Meta:
        verbose_name_plural = "Karyawan"

class Cabang(models.Model):
    kode_cabang = models.CharField(max_length=10, primary_key=True) # pk
    nama_cabang = models.CharField(max_length=100, unique=True)

    kepala_cabang = models.ForeignKey(
        'Karyawan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'jabatan__icontains': 'kepala cabang'},
        related_name='cabang_dipimpin'
    )

    def __str__(self):
        return f"{self.kode_cabang} - {self.nama_cabang}"

    class Meta:
        verbose_name_plural = "Cabang"