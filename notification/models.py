from django.db import models
from accounts.models import CustomUser

class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='receive_notifications')
    message = models.TextField()
    # 重複の可能性
    created_at = models.DateTimeField(auto_now_add=True)
    is_priority = models.BooleanField(default=False) 
    is_read = models.BooleanField(default=False) 
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_notifications', blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.message}'