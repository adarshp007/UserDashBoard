from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import Dataset, Entity, Role, User

# Register your models here.


class UserAdmin(BaseUserAdmin):
    list_display = ("email", "first_name", "last_name", "status", "is_superuser")
    list_filter = ("status", "is_superuser")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "phone_number", "address")}),
        (_("Entity info"), {"fields": ("entity",)}),
        (_("Status"), {"fields": ("status",)}),
        (_("Permissions"), {"fields": ("is_superuser",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "first_name", "last_name", "status"),
            },
        ),
    )
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)
    filter_horizontal = ()


class EntityAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "created_date", "modified_date")
    list_filter = ("status",)
    search_fields = ("name", "description")
    readonly_fields = ("created_date", "modified_date", "created_by", "updated_by")


class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "created_date", "modified_date")
    search_fields = ("name",)
    readonly_fields = ("created_date", "modified_date", "created_by", "updated_by")


class DatasetAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "owner", "created_date", "modified_date")
    list_filter = ("status",)
    search_fields = ("name", "description")
    readonly_fields = ("created_date", "modified_date", "created_by", "updated_by", "metadata")


# Register the models with their respective admin classes
admin.site.register(User, UserAdmin)
admin.site.register(Entity, EntityAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(Dataset, DatasetAdmin)
