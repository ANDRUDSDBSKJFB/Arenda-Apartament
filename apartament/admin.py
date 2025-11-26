from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Post, Comment,PostImage, Profile,User
from django.contrib.admin import DateFieldListFilter


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created')
    search_fields = ('name',)
    # Убрано prepopulated_fields так как нет поля slug

class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 1
    fields = ('image_preview', 'image', 'is_main', 'created')
    readonly_fields = ('image_preview', 'created', 'updated')
    
    def image_preview(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />', 
                obj.image.url
            )
        return "Нет изображения"
    image_preview.short_description = 'Предпросмотр'

@admin.register(PostImage)
class PostImageAdmin(admin.ModelAdmin):
    list_display = (
        'post', 
        'image_preview', 
        'is_main', 
        'created'
    )
    list_filter = (
        'is_main', 
        'created', 
        'updated'
    )
    search_fields = (
        'post__title',
    )
    list_editable = ('is_main',)
    readonly_fields = (
        'created', 
        'updated', 
        'image_preview_admin'
    )
    fieldsets = (
        (None, {
            'fields': (
                'post', 
                'image'
            )
        }),
        ('Настройки', {
            'fields': ('is_main',)
        }),
        ('Предпросмотр', {
            'fields': ('image_preview_admin',),
            'classes': ('collapse',)
        }),
        ('Даты', {
            'fields': (
                'created', 
                'updated'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def image_preview(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px;" />', 
                obj.image.url
            )
        return "Нет изображения"
    image_preview.short_description = 'Изображение'
    
    def image_preview_admin(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            return format_html(
                '<img src="{}" style="max-height: 300px; max-width: 300px;" />', 
                obj.image.url
            )
        return "Нет изображения"
    image_preview_admin.short_description = 'Большой предпросмотр'

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title', 
        'owner', 
        'category', 
        'price', 
        'status', 
        'views', 
        'created', 
        'comments_count',
        'images_count',
        'main_image_preview'  # Добавляем превью главного изображения
    )
    list_filter = (
        'status', 
        'category', 
        'created', 
        'updated',
        'rooms'
    )
    search_fields = (
        'title', 
        'description', 
        'address', 
        'owner__username'
    )
    readonly_fields = (
        'views', 
        'created', 
        'updated',
        'main_image_display'
    )
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'title', 
                'description', 
                'owner', 
                'category',
                'status'
            )
        }),
        ('Характеристики', {
            'fields': (
                'price',
                'area', 
                'rooms', 
                'address'
            )
        }),
        ('Контакты', {
            'fields': ('contact_phone',)
        }),
        ('Главное изображение', {
            'fields': ('main_image_display',),
            'classes': ('collapse',)
        }),
        ('Статистика', {
            'fields': (
                'views', 
                'created', 
                'updated'
            ),
            'classes': ('collapse',)
        }),
    )
    inlines = [PostImageInline]
    actions = ['approve_posts', 'reject_posts']
    
    def approve_posts(self, request, queryset):
        queryset.update(status='active')
    approve_posts.short_description = "✅ Одобрить выбранные объявления"
    
    def reject_posts(self, request, queryset):
        queryset.update(status='rejected') 
    reject_posts.short_description = "❌ Отклонить выбранные объявления"
    
    def comments_count(self, obj):
        return obj.comments.count()
    comments_count.short_description = 'Комментарии'
    
    def images_count(self, obj):
        return obj.images.count()
    images_count.short_description = 'Изображения'
    
    def main_image_preview(self, obj):
        main_image = obj.images.filter(is_main=True).first()
        if main_image and main_image.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px;" />', 
                main_image.image.url
            )
        # Если нет главного, показываем первое изображение
        first_image = obj.images.first()
        if first_image and first_image.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px;" />', 
                first_image.image.url
            )
        return "Нет изображения"
    main_image_preview.short_description = 'Главное фото'
    
    def main_image_display(self, obj):
        main_image = obj.images.filter(is_main=True).first()
        if main_image and main_image.image:
            return format_html(
                '<img src="{}" style="max-height: 300px; max-width: 300px;" />', 
                main_image.image.url
            )
        return "Главное изображение не установлено"
    main_image_display.short_description = 'Главное изображение'

# Обновленный ProfileAdmin с предпросмотром аватара
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 
        'phone', 
        'avatar_preview',
        'birth_date', 
        'created'
    )
    list_filter = (
        'created', 
        'updated', 
        'birth_date'
    )
    search_fields = (
        'user__username', 
        'user__first_name', 
        'user__last_name', 
        'phone'
    )
    readonly_fields = (
        'created', 
        'updated',
        'avatar_display'
    )
    fieldsets = (
        ('Пользователь', {
            'fields': ('user',)
        }),
        ('Контактная информация', {
            'fields': (
                'phone', 
                'avatar'
            )
        }),
        ('Личная информация', {
            'fields': (
                'bio', 
                'birth_date'
            )
        }),
        ('Предпросмотр аватара', {
            'fields': ('avatar_display',),
            'classes': ('collapse',)
        }),
        ('Даты', {
            'fields': (
                'created', 
                'updated'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def avatar_preview(self, obj):
        if obj.avatar and hasattr(obj.avatar, 'url'):
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px; border-radius: 50%;" />', 
                obj.avatar.url
            )
        return "Нет аватара"
    avatar_preview.short_description = 'Аватар'
    
    def avatar_display(self, obj):
        if obj.avatar and hasattr(obj.avatar, 'url'):
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 200px; border-radius: 10px;" />', 
                obj.avatar.url
            )
        return "Аватар не установлен"
    avatar_display.short_description = 'Предпросмотр аватара'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'owner', 'created', 'active')
    list_filter = ('created', 'active')
    search_fields = ('content', 'post__title', 'owner__username')
    readonly_fields = ('created', 'updated')

    actions = ['activate_comments', 'deactivate_comments']
    
    def activate_comments(self, request, queryset):
        queryset.update(active=True)
    activate_comments.short_description = "Активировать комментарии"
    
    def deactivate_comments(self, request, queryset):
        queryset.update(active=False)
    deactivate_comments.short_description = "Деактивировать комментарии"

