from django.contrib import admin
from .models import Group, GiftIdea, Invitation

# Register your models here.

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name',)
    filter_horizontal = ('members',)

@admin.register(GiftIdea)
class GiftIdeaAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'group', 'purchased', 'purchased_by')
    list_filter = ('purchased', 'group')
    search_fields = ('name', 'description', 'user__username', 'group__name')

@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'group', 'invited_by', 'created_at')
    list_filter = ('group', 'created_at')
    search_fields = ('email', 'group__name', 'invited_by__username')
    readonly_fields = ('token',)
