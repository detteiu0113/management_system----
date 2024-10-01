from accounts.models import CustomUser
from django.db import models
import os

def get_upload_path(instance, filename):
    return os.path.join("uploads", str(instance.user.id), filename)

class Room(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    # ownerは全ての部屋にアクセス可能
    users = models.ManyToManyField(CustomUser)

    def __str__(self):
        return self.name

class Message(models.Model):
    room = models.ForeignKey(Room, related_name='messages', on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, related_name='messages', on_delete=models.CASCADE)
    content = models.TextField()
    file = models.FileField(upload_to=get_upload_path, blank=True, null=True)
    image = models.ImageField(upload_to=get_upload_path, blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ('date_added',)
