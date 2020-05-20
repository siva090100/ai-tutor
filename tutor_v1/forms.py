from django import forms
from django.forms import ModelForm
from .models import Problem

class UploadQuestions(forms.Form):
	title = forms.CharField(max_length = 50)
	question_file = forms.FileField()
	mapping_file = forms.FileField()



