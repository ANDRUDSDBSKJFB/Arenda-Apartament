# models.py
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.validators import FileExtensionValidator

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название категории')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'apartament'
        verbose_name = 'Категория'
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name

class Post(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('moderation', 'На модерации'),
        ('active', 'Активно'),
        ('rejected', 'Отклонено'),
        ('archived', 'Архив'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Описание')
    owner = models.ForeignKey(User, related_name='posts', on_delete=models.CASCADE)
    category = models.ForeignKey(Category, related_name='posts', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Цена')
    area = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name='Площадь')
    rooms = models.PositiveIntegerField(default=1, verbose_name='Комнаты')
    address = models.CharField(max_length=300, default='', verbose_name='Адрес')
    contact_phone = models.CharField(max_length=20, default='', verbose_name='Телефон')
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='moderation',
        verbose_name='Статус'
    )
    views = models.PositiveIntegerField(default=0, verbose_name='Просмотры')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'apartament'
        verbose_name = 'Объявление'
        verbose_name_plural = "Объявления"

    def __str__(self):
        return self.title

    def increment_views(self):
        """Увеличивает счетчик просмотров"""
        self.views += 1
        self.save(update_fields=['views'])

    def get_absolute_url(self):
        return reverse('post-detail', kwargs={'pk': self.pk})

class Comment(models.Model):
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    owner = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE)
    content = models.TextField(default='', verbose_name='Текст комментария')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        app_label = 'apartament'
        verbose_name = 'Комментарий'
        verbose_name_plural = "Комментарии"

    def __str__(self):
        return f'Комментарий от {self.owner}'
    
class Profile(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='profile'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Телефон'
    )
    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name='Аватар',
        # Дополнительные валидаторы (опционально)
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])
        ]
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        verbose_name='О себе'
    )
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата рождения'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        app_label = 'apartament'
        verbose_name = 'Профиль'
        verbose_name_plural = "Профили"

    def __str__(self):
        return f'Профиль {self.user.username}'
    
class PostImage(models.Model):
    post = models.ForeignKey(
        Post, 
        related_name='images', 
        on_delete=models.CASCADE,
        verbose_name='Объявление'
    )
    image = models.ImageField(
        upload_to='posts/%Y/%m/%d/',
        verbose_name='Изображение',
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])
        ]
    )
    is_main = models.BooleanField(default=False, verbose_name='Основное изображение')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'apartament'
        verbose_name = 'Изображение объявления'
        verbose_name_plural = "Изображения объявлений"
        ordering = ['-is_main', 'created']

    def __str__(self):
        return f"Изображение для {self.post.title}"

    def save(self, *args, **kwargs):
        # Если это основное изображение, снимаем флаг с других изображений этого поста
        if self.is_main:
            PostImage.objects.filter(post=self.post, is_main=True).update(is_main=False)
        super().save(*args, **kwargs)

# Сигнал для автоматического создания профиля при создании пользователя
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()