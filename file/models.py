from django.db import models
from django.utils import timezone
from accounts.models import CustomUser

# Create your models here.
class File(models.Model):
    accessible_users = models.ManyToManyField(CustomUser)
    file = models.FileField(upload_to='', blank=True, null=True)
    date = models.DateField()
    created_at = models.DateField(default=timezone.now)

    def __str__(self):
        return f'{self.file.name}' if self.file else None

    def delete(self, *args, **kwargs):
        # ファイルが存在する場合は削除する
        if self.file:
            storage, path = self.file.storage, self.file.path
            # ファイルを削除
            storage.delete(path)
        super().delete(*args, **kwargs)