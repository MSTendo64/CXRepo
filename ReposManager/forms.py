from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from captcha.fields import CaptchaField
from .models import Package
from django.core.exceptions import ValidationError

class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'name@example.com'
        })
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Имя пользователя'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Пароль'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Подтвердите пароль'
        })
    )
    captcha = CaptchaField(
        error_messages={'invalid': 'Неправильный код капчи'}
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if self.fields[field].widget.attrs.get('class'):
                self.fields[field].widget.attrs['class'] += ' is-invalid' if field in self.errors else ''

class PackageUpdateForm(forms.ModelForm):
    class Meta:
        model = Package
        fields = ['pkg_version', 'pkg_description', 'pkg_file']
        widgets = {
            'pkg_version': forms.TextInput(attrs={'class': 'form-control'}),
            'pkg_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'pkg_file': forms.FileInput(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if self.fields[field].widget.attrs.get('class'):
                self.fields[field].widget.attrs['class'] += ' is-invalid' if field in self.errors else ''

    def clean_pkg_version(self):
        version = self.cleaned_data.get('pkg_version')
        name = self.instance.pkg_name
        if Package.objects.filter(pkg_name=name, pkg_version=version).exists():
            raise ValidationError('Пакет с такой версией уже существует')
        return version 