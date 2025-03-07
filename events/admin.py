from django.contrib import admin
from .models import Category

class AdminCategory(admin.ModelAdmin):
    list_display = ('name',)

    
    def has_add_permission(self, request):
        return True
    
    def has_change_permission(self, request,obj=None):
        return True
    def has_delete_permission(self, request,obj = None):
        return True

admin.site.register(Category,AdminCategory)
