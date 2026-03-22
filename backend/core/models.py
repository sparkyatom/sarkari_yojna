"""core/models.py — Upload history tracking"""
from django.db import models
from django.conf import settings


class UploadHistory(models.Model):
    FILE_TYPE_CHOICES = [('excel','Excel'),('csv','CSV'),('json','JSON')]

    filename        = models.CharField(max_length=255)
    file_type       = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES)
    schemes_created = models.PositiveIntegerField(default=0)
    schemes_skipped = models.PositiveIntegerField(default=0)
    uploaded_by     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at     = models.DateTimeField(auto_now_add=True)
    success         = models.BooleanField(default=True)
    error_log       = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'upload_history'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.filename} — {self.schemes_created} schemes"
