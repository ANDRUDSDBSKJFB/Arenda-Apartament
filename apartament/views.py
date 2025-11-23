from django.contrib.auth import authenticate, login
from django.db.models import F
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import generics, permissions
from . import serializers
from django.contrib import messages
from django.utils import timezone
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse, reverse_lazy
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.forms import modelformset_factory
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .forms import AuthUserForm, RegUserForm, PostForm, CommentForm
from .models import Post, Comment, Category
from .serializers import PostSerializer, UserSerializer
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from django.views.generic import DeleteView, CreateView, UpdateView, DetailView, ListView
from rest_framework.views import APIView
from django.views.generic.edit import FormMixin
from .permissions import IsOwnerOrReadOnly
from .models import Profile
from .forms import UserUpdateForm, ProfileUpdateForm, AdminPostForm, PostImage, PostImageForm,PostImageUploadForm

class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = 'main/profile.html'
    context_object_name = 'profile'

    def get_object(self):
        return self.request.user.profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Получаем статистику
        user_posts = Post.objects.filter(owner=user)
        total_views = user_posts.aggregate(total_views=Sum('views'))['total_views'] or 0
        recent_posts = user_posts.order_by('-created')[:5]
        
        context.update({
            'user': user,
            'total_views': total_views,
            'recent_posts': recent_posts,
            'post_count': user_posts.count(),
            'comment_count': Comment.objects.filter(owner=user).count(),
        })
        return context

class ProfileUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Profile
    template_name = 'main/profile_edit.html'
    form_class = ProfileUpdateForm
    user_form_class = UserUpdateForm
    success_message = "Профиль успешно обновлен"
    success_url = reverse_lazy('profile')

    def get_object(self):
        return self.request.user.profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['user_form'] = self.user_form_class(self.request.POST, instance=self.request.user)
        else:
            context['user_form'] = self.user_form_class(instance=self.request.user)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        user_form = context['user_form']
        if user_form.is_valid():
            user_form.save()
            return super().form_valid(form)
        else:
            return self.form_invalid(form)


class PostinList(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'main/index.html'

    def get(self, request):
        # Базовый queryset - только активные объявления
        queryset = Post.objects.filter(status='active')
        
        # Поиск по тексту
        search_query = request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(address__icontains=search_query)
            )
        
        # Фильтр по цене
        max_price = request.GET.get('max_price')
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Фильтр по комнатам
        rooms = request.GET.get('rooms')
        if rooms:
            queryset = queryset.filter(rooms=rooms)
        
        # Фильтр по площади
        min_area = request.GET.get('min_area')
        if min_area:
            queryset = queryset.filter(area__gte=min_area)
        
        # Сортировка
        sort = request.GET.get('sort', '-created')
        queryset = queryset.order_by(sort)
        
        # Пагинация
        paginator = Paginator(queryset, 9)  # 9 объявлений на страницу
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Статистика для отображения
        total_views = sum(post.views for post in Post.objects.filter(status='active'))
        active_users = User.objects.filter(posts__status='active').distinct().count()
        new_today = Post.objects.filter(
            status='active',
            created__date=timezone.now().date()
        ).count()
        
        return Response({
            'posts': page_obj,
            'total_views': total_views,
            'active_users': active_users,
            'new_today': new_today,
        })
class PostDetailView(DetailView):
    model = Post
    template_name = 'main/changer.html'
    context_object_name = 'get_article'


class CustomSuccessMessageMixin:
    @property
    def success_msg(self):
        return False

    def form_valid(self, form):
        messages.success(self.request, self.success_msg)
        return super().form_valid(form)

    def get_success_url(self):
        return '%s?id=%s' % (self.success_url, self.object.id)


# views.py
class PostChangeView(LoginRequiredMixin, CreateView):
    model = Post
    template_name = 'main/changer.html'
    success_url = reverse_lazy('change')
    
    def get_form_class(self):
        if self.request.user.is_staff:
            return AdminPostForm
        return PostForm
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        # Показываем все объявления пользователя
        user_posts = Post.objects.filter(owner=self.request.user)
        
        # Статистика - теперь используем реальные данные
        total_views = sum(post.views for post in user_posts)
        active_posts = user_posts.filter(status='active').count()
        moderation_posts = user_posts.filter(status='moderation').count()
        draft_posts = user_posts.filter(status='draft').count()
        
        kwargs['user_posts'] = user_posts
        kwargs['total_views'] = total_views
        kwargs['active_posts'] = active_posts
        kwargs['moderation_posts'] = moderation_posts
        kwargs['draft_posts'] = draft_posts
        kwargs['total_comments'] = Comment.objects.filter(
            post__in=user_posts, 
            active=True
        ).count()
        
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        form.instance.owner = self.request.user
        if not self.request.user.is_staff:
            form.instance.status = 'moderation'
        messages.success(self.request, 'Объявление успешно создано!')
        return super().form_valid(form)

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    template_name = 'main/model.html'
    success_url = reverse_lazy('change')
    
    def get_form_class(self):
        if self.request.user.is_staff:
            return AdminPostForm
        return PostForm
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        # Формсет для изображений
        PostImageFormSet = modelformset_factory(PostImage, form=PostImageForm, extra=5)
        context['image_formset'] = PostImageFormSet(queryset=PostImage.objects.none())
        return context

    def form_valid(self, form):
        form.instance.owner = self.request.user
        if not self.request.user.is_staff:
            form.instance.status = 'moderation'
        
        response = super().form_valid(form)
        
        # Обработка изображений
        PostImageFormSet = modelformset_factory(PostImage, form=PostImageForm, extra=5)
        formset = PostImageFormSet(self.request.POST, self.request.FILES, queryset=PostImage.objects.none())
        
        if formset.is_valid():
            for image_form in formset:
                if image_form.cleaned_data.get('image'):
                    image = image_form.save(commit=False)
                    image.post = self.object
                    image.save()
        
        messages.success(self.request, 'Объявление успешно создано!')
        return response

class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    template_name = 'main/post_update.html'
    success_url = reverse_lazy('change')
    
    def get_form_class(self):
        if self.request.user.is_staff:
            return AdminPostForm
        return PostForm
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['update'] = True
        context['categories'] = Category.objects.all()
        
        # Исправлено: используем post вместо Post
        context['existing_images'] = PostImage.objects.filter(Post=self.object)
        context['image_form'] = PostImageUploadForm()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Обработка новых изображений
        image_form = PostImageUploadForm(self.request.POST, self.request.FILES)
        if image_form.is_valid():
            images = self.request.FILES.getlist('images')
            for image_file in images:
                PostImage.objects.create(
                    Post=self.object,  # Исправлено: post вместо Post
                    image=image_file
                )
        
        # Обработка основного изображения
        main_image_id = self.request.POST.get('main_image')
        if main_image_id:
            PostImage.objects.filter(Post=self.object).update(is_main=False)  # Исправлено
            PostImage.objects.filter(id=main_image_id, Post=self.object).update(is_main=True)  # Исправлено
        
        messages.success(self.request, 'Объявление успешно обновлено!')
        return response

class PostinDetailView(FormMixin, DetailView):
    model = Post
    template_name = 'main/post_detail.html'
    context_object_name = 'post'
    form_class = CommentForm
    success_msg = 'Комментарий успешно создан, ожидайте модерации'

    def get(self, request, *args, **kwargs):
        # Увеличиваем счетчик просмотров
        response = super().get(request, *args, **kwargs)
        if self.object.status == 'active':
            Post.objects.filter(pk=self.object.pk).update(views=F('views')+ 1)
            # Обновляем объект в контексте
            self.object.views += 1
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = Comment.objects.filter(post=self.object, active=True)
        context['form'] = self.form_class()
        
        # Добавляем профиль пользователя, если он аутентифицирован
        if self.request.user.is_authenticated:
            try:
                context['profile'] = self.request.user.profile
            except Profile.DoesNotExist:
                # Если профиля нет, создаем его
                Profile.objects.create(user=self.request.user)
                context['profile'] = self.request.user.profile
        else:
            context['profile'] = None
            
        return context

    def get_success_url(self):
        return reverse_lazy('post-detail', kwargs={'pk': self.get_object().id})

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        comment = form.save(commit=False)
        comment.post = self.get_object()
        comment.owner = self.request.user
        comment.save()
        messages.success(self.request, self.success_msg)
        return super().form_valid(form)


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'main/post_delete.html'
    success_url = reverse_lazy('change')
    success_msg = 'Запись удалена'
    raise_exception = True

    def get_context_data(self, **kwargs):
        kwargs['comments'] = Comment.objects.all()
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        messages.success(self.request, self.success_msg)
        return super().post(request)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.request.user != self.object.owner:
            return self.handle_no_permission()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.user != self.object.owner:
            return self.handle_no_permission()
        return kwargs


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = 'main/post_delete.html'
    success_url = '/'
    success_msg = 'Запись удалена'
    raise_exception = True

    def post(self, request, *args, **kwargs):
        messages.success(self.request, self.success_msg)
        return super().post(request)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.request.user == self.object.owner:
            self.object.delete()
            return self.handle_no_permission()
        success_url = self.get_success_url()
        return HttpResponseRedirect(success_url)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.user != self.object.owner:
            return self.handle_no_permission()
        return kwargs


class ProjectUserLoginView(LoginView):
    template_name = 'main/login.html'
    form_class = AuthUserForm
    success_url = '/login'


class ProjectUserRegistrationView(CreateView):
    template_name = 'main/register.html'
    form_class = RegUserForm
    success_url = '/'
    success_msg = "Record created"

    def form_valid(self, form):
        form_valid = super().form_valid(form)
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password1"]
        aut_user = authenticate(username=username, password=password)
        login(self.request, aut_user)
        return form_valid


class ProjectUserLogOutView(LogoutView):
    next_page = '/'


class UserList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer


class UserDetail(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer


class PostList(generics.ListCreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PostDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly]


class CommentList(generics.ListCreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = serializers.CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class CommentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = serializers.CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly]


class CategoryList(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = serializers.CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class CategoryDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = serializers.PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly]
    
class ModerationListView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'main/moderation_list.html'
    context_object_name = 'posts'
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Post.objects.filter(status='moderation')
        return Post.objects.none()
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect('post-list')
        return super().dispatch(request, *args, **kwargs)

class ImageDeleteView(LoginRequiredMixin, DeleteView):
    model = PostImage
    template_name = 'main/image_delete.html'
    
    def get_success_url(self):
        return reverse_lazy('post-update', kwargs={'pk': self.object.post.pk})
    
    def get_queryset(self):
        return PostImage.objects.filter(post__owner=self.request.user)