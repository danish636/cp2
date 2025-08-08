from django.contrib import admin

# Register your models here.

from .models import *    

from django.contrib.auth.models import Group, User
try:
    admin.site.unregister(Group)
    admin.site.unregister(User)
except:
    pass


class Industry_report_report(admin.ModelAdmin):
    search_fields = ['Sector_name','industry_name','heading_name']
    list_display = ['heading_name','Sector_name','industry_name','find']
    
    
class General_topic_report(admin.ModelAdmin):
    search_fields = ['Blog_heading', "heading_name"]
    list_display = ['heading_name', 'find']

class Blog_admin(admin.ModelAdmin):
    search_fields = ['Blog_heading', "heading_name"]
    list_display = ['heading_name', 'find']
    
class macroeconimcs_admin(admin.ModelAdmin):
    search_fields = ['Macroeconomic_field', "heading_name"]
    list_display = ['heading_name', 'find']

admin.site.register(Industry_report,Industry_report_report)
admin.site.register(General_topic,General_topic_report)
admin.site.register(Blog,Blog_admin)
admin.site.register(Macroeconomics,macroeconimcs_admin)


admin.site.site_header = "Invex Dashboard"
admin.site.site_title = "Invex Dashboard"