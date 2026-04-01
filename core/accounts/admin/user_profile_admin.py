from django import forms
from django.contrib import admin
from django.forms import JSONField

from core.accounts.models import UserProfile


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = '__all__'

    membership = JSONField(required=False)
    training_background = JSONField(required=False)
    socials = JSONField(required=False)

    def clean_membership(self):
        membership = self.cleaned_data.get('membership', None)
        if membership is None:
            return []
        return membership

    def clean_training_background(self):
        training_background = self.cleaned_data.get('training_background', None)
        if training_background is None:
            return []
        return training_background

    def clean_socials(self):
        socials = self.cleaned_data.get('socials', None)
        if socials is None:
            return []
        return socials


class UserProfileAdmin(admin.ModelAdmin):
    form = UserProfileForm
    list_display = ('id', 'user', 'user_uuid')
    search_fields = ['user__username']
    autocomplete_fields = ['user']

    def user_uuid(self, obj):
        return obj.user.uuid if obj.user else None
    user_uuid.admin_order_field = 'user__uuid'
    user_uuid.short_description = 'User UUID'
