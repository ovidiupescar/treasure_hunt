from django.contrib import admin
from .models import Group, Question, Answer

def set_as_licu(modeladmin, request, queryset):
    queryset.update(licu=True)
set_as_licu.short_description = "Mark selected groups as Licu"

def set_as_explo(modeladmin, request, queryset):
    queryset.update(licu=False)
set_as_explo.short_description = "Mark selected groups as Explo"

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('group_number', 'group_name', 'licu', 'total_points', 'answers_provided', 'completion_order')
    list_filter = ('licu', 'completion_order')
    search_fields = ('group_number', 'group_name')
    actions = [set_as_licu, set_as_explo]

admin.site.register(Question)
admin.site.register(Answer)
