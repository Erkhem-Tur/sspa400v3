from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import Department


class RegisterForm(forms.ModelForm):
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        label="Хэлтэс / Тасаг",
        empty_label="-- Хэлтэсээ сонгоно уу --"
    )
    password = forms.CharField(widget=forms.PasswordInput, label="Нууц үг")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Нууц үг давтах")

    class Meta:
        model = User
        fields = ['username', 'email']
        labels = {'username': 'Хэрэглэгчийн нэр', 'email': 'Имэйл'}

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('password2'):
            raise forms.ValidationError("Нууц үг таарахгүй байна.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Хэрэглэгчийн нэр")
    password = forms.CharField(widget=forms.PasswordInput, label="Нууц үг")
