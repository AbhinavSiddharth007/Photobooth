from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid

class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    guest_code = models.CharField(max_length=12, unique=True, editable=False)
    owner_secret = models.CharField(max_length=32, unique=True, editable=False)
    name = models.CharField(max_length=200)
    owner_email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    uploads_enabled = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=30)
        if not self.guest_code:
            self.guest_code = str(uuid.uuid4())[:12]
        if not self.owner_secret:
            self.owner_secret = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Photo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='photos')
    s3_key = models.CharField(max_length=500)
    s3_url = models.URLField(max_length=1000)
    original_filename = models.CharField(max_length=255)
    file_size = models.IntegerField()
    content_type = models.CharField(max_length=50)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Photo for {self.event.name}"
