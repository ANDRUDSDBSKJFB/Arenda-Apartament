from django.contrib import admin
from .models import Category, Post, Comment

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created')
    search_fields = ('name',)
    # Убрано prepopulated_fields так как нет поля slug

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'price', 'rooms', 'created','views','status')
    list_filter = ('category', 'created',)
    search_fields = ('title', 'description', 'address', 'owner__username')
    readonly_fields = ('created', 'updated')
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'owner', 'category','status')
        }),
        ('Детали недвижимости', {
            'fields': ('price', 'area', 'rooms')
        }),
        ('Адрес', {
            'fields': ('address', 'contact_phone')
        }),
        ('Системная информация', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'owner', 'created', 'active')
    list_filter = ('created', 'active')
    search_fields = ('content', 'post__title', 'owner__username')
    readonly_fields = ('created', 'updated')