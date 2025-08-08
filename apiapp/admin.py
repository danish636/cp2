from django.contrib import admin
from .models import *

class CustomUserAdmin(admin.ModelAdmin):
    ordering = ["email"]
    list_display = ['email','firstName', 'lastName',"is_active"]

    def save_model(self, request, obj, form, change):
        # Hash the password before saving the user
        if obj.pk is None:  # Only hash the password when creating a new user
            obj.set_password(form.cleaned_data['password'])
        super().save_model(request, obj, form, change)


admin.site.register(User, CustomUserAdmin)
admin.site.register(UserPortfolio)
admin.site.register(UserScreenerFilter)
admin.site.register(TempTokenModel)