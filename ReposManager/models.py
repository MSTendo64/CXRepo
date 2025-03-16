from django.db import models
import os
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

def validate_zip_file(value):
    if not value.name.endswith('.zip'):
        raise ValidationError('Только ZIP файлы разрешены')

def package_upload_path(instance, filename):
    """Динамический путь для загрузки пакета"""
    return os.path.join("pkgs", instance.pkg_name, instance.pkg_version, filename)

class Package(models.Model):
    VERIFICATION_STATUS = (
        ('pending', 'На проверке'),
        ('verified', 'Проверен'),
        ('rejected', 'Отклонен'),
    )

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='packages')
    pkg_name = models.CharField(max_length=50)
    pkg_version = models.CharField(max_length=30)
    pkg_description = models.CharField(max_length=1000)
    pkg_publish_date = models.DateField()
    pkg_file = models.FileField(
        upload_to=package_upload_path,
        validators=[validate_zip_file]
    )
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS,
        default='pending'
    )
    admin_comment = models.TextField(blank=True, null=True)
    
    class Meta:
        # Гарантируем уникальность комбинации имени и версии
        unique_together = [('pkg_name', 'pkg_version')]
        ordering = ['-pkg_publish_date', '-pkg_version']
    
    def __str__(self):
        return f"{self.pkg_name} {self.pkg_version}"

    @property
    def pkg_filepath(self):
        """Свойство для получения полного пути к файлу (опционально)"""
        return self.pkg_file.path if self.pkg_file else None

    def clean(self):
        if self.pk:  # Если это обновление существующего пакета
            existing = Package.objects.get(pk=self.pk)
            if existing.pkg_version == self.pkg_version and existing.pkg_name != self.pkg_name:
                raise ValidationError('Нельзя изменить имя пакета для существующей версии')
            if existing.verification_status == 'rejected' and self.pkg_version != existing.pkg_version:
                raise ValidationError('Нельзя изменить версию отклоненного пакета')

