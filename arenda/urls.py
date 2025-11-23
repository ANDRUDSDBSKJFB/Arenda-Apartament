from django.urls import path
from django.contrib import admin
from rest_framework.urlpatterns import format_suffix_patterns
from apartament import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.PostinList.as_view(), name='post-list'),
    path('login', views.ProjectUserLoginView.as_view(), name='auth'),
    path('reg', views.ProjectUserRegistrationView.as_view(), name='registration'),
    path('logout', views.ProjectUserLogOutView.as_view(), name='logout'),
    path('edit', views.PostChangeView.as_view(), name='change'),
    path('create/',views.PostCreateView.as_view(),name='post-create'),
    path('<int:pk>/', views.PostinDetailView.as_view(), name='post-detail'),
    path('<int:pk>/comment', views.CommentDeleteView.as_view(), name='comment-delete'),
    path('<int:pk>/update', views.PostUpdateView.as_view(), name='post-update'),
    path('<int:pk>/delete', views.PostDeleteView.as_view(), name='post-delete'),
    path('image/<int:pk>/delete/', views.ImageDeleteView.as_view(), name='delete-image'),
    path('accounts/profile/', views.ProfileDetailView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile-edit'),
    path('users', views.UserList.as_view()),
    path('users/<int:pk>/', views.UserDetail.as_view()),
    path('posts/', views.PostList.as_view()),
    path('posts/<int:pk>/', views.PostDetail.as_view()),
    path('comments/', views.CommentList.as_view()),
    path('comments/<int:pk>/', views.CommentDetail.as_view()),
    path('categories/', views.CategoryList.as_view()),
    path('categories/<int:pk>/', views.CategoryDetail.as_view()),
    path('moderation/', views.ModerationListView.as_view(), name='moderation-list'),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)