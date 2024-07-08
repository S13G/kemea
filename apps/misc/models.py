from ckeditor.fields import RichTextField
from django.db import models
from django.db.models import UniqueConstraint

from apps.common.models import BaseModel


# Create your models here.


class Policy(BaseModel):
    title = models.CharField(max_length=255)
    language = models.CharField(max_length=3)
    content = RichTextField()

    class Meta:
        constraints = [
            UniqueConstraint(fields=['title', 'language'], name='unique_policy')
        ]
        verbose_name = 'Policy'
        verbose_name_plural = 'Policies'

    def __str__(self):
        return self.title
