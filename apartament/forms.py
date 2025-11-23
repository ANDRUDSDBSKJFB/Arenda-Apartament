from .models import Post, Comment, Profile, PostImage
from django import forms
from django.contrib.auth.models import User
from django.forms import ModelForm, TextInput, Textarea
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django import forms



class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone', 'bio', 'birth_date', 'avatar']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


class PostImageForm(forms.ModelForm):
    class Meta:
        model = PostImage
        fields = ['image', 'is_main']
        widgets = {
            'is_main': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

# Основная форма для поста
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'description', 'category', 'price', 'area', 'rooms', 'address', 'contact_phone']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'area': forms.NumberInput(attrs={'class': 'form-control'}),
            'rooms': forms.NumberInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        post = super().save(commit=False)
        if self.request:
            post.owner = self.request.user
        if commit:
            post.save()
        return post

# Форма для загрузки нескольких изображений
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class PostImageUploadForm(forms.Form):
    images = MultipleFileField(
        required=False,
        label='Изображения',
        help_text='Можно выбрать несколько файлов'
    )
class AdminPostForm(PostForm):
    """Форма для администраторов с возможностью изменения статуса"""
    class Meta(PostForm.Meta):
        fields = PostForm.Meta.fields + ['status']
        widgets = PostForm.Meta.widgets.copy()
        widgets.update({
            'status': forms.Select(attrs={'class': 'form-select'})
        })

class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['content']  # Убрано поле 'rating'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


class AuthUserForm(AuthenticationForm, ModelForm):
    class Meta:
        model = User
        fields = ('username', 'password')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


class RegUserForm(UserCreationForm, ModelForm):
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')  # Исправлено: добавлены password1 и password2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])  # Исправлено: password1 вместо password
        if commit:
            user.save()
        return user
    
