from django.db import models


class DepartmentUser(models.Model):
    email = models.EmailField(unique=True)
    username = models.CharField(
        max_length=128, blank=True, null=True, help_text='Pre-Windows 2000 login username.')

    def __str__(self):
        return self.email
