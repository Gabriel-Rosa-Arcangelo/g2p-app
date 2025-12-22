from allauth.account.forms import LoginForm
from captcha.fields import CaptchaField 
from django import forms
from .models import UserSettings

class CustomLoginForm(LoginForm):
    captcha = CaptchaField()
    
class UserSettingsForm(forms.ModelForm):
    
    class Meta:
        model = UserSettings
        fields = ['firstname','lastname','address','zipcode','city','country','department','jobtitle']

    
 
