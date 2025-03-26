from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser,AbstractBaseUser
from django.utils.translation import gettext_lazy as _
from safedelete.models import SafeDeleteModel
import uuid

from .manager import UserManager

# Create your models here.
class BaseFields(SafeDeleteModel):
    object_id = models.UUIDField(primary_key=True,default=uuid.uuid4)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_created",
        null=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_updated",
        null=True,
    )
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        abstract = True

class Entity(BaseFields):
    # Defining status choices
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('in_active', 'In Active'),
    )
    name = models.CharField(_("entity name"),max_length=255,blank=True,null=True)
    address = models.TextField(_("address"),blank=True,null=True)
    description = models.TextField(_("entity description"),blank=True,null=True)
    status = models.CharField(_("entity status"), max_length=80,choices=STATUS_CHOICES,default='pending')

class Role(BaseFields):
    name = models.CharField(_("role name"),max_length=255,blank=True,null=True)

class User(AbstractBaseUser,BaseFields):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('active', 'Active'),
        ('in_active', 'In Active'),
    )
    first_name = models.CharField(_("first name"),max_length=255)
    last_name = models.CharField(_("last name"),max_length=255,blank=True,null=True)
    email = models.EmailField(_("email address"), unique=True,)
    phone_number = models.CharField(_("phone number"),max_length=15, blank=True, null=True)
    address = models.TextField(_("address"),blank=True,null=True)
    is_superuser = models.BooleanField(default=False)
    entity = models.ForeignKey(Entity,on_delete=models.CASCADE,blank=True,null=True,related_name="%(app_label)s_%(class)s_entity",)
    status = models.CharField(_("user status"), max_length=80,choices=STATUS_CHOICES,default='pending')
    
    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"
    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")


class Dataset(BaseFields):
    DATASET_STATUS_CHOICES = [
        ('READ_PENDING','Read Pending'),
        ('READ_COMMENCE','Read Commence'),
        ('READ_COMPLETE','Read Complete'),
        ('WRITE_COMMENCE', 'Write Commence'),
        ('WRITE_COMPLETE', 'Write Complete')
    ]
    name = models.CharField(_("dataset name"),max_length=255)
    description = models.TextField(_("dataset description"),blank=True)
    status = models.CharField(_("dataset status"),max_length=255,default='READ_PENDING')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='datasets')
    metadata = models.JSONField(default=dict)
    # file = models.FileField(upload_to='datasets/', blank=True, null=True)  # Add this field for file uploads
