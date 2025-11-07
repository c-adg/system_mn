from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from django import forms
from .forms import ProfileUpdateForm, SignUpForm
from django.contrib.auth.models import Group
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from .forms import ProfileUpdateForm


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'registration/sign_up.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Cuenta creada exitosamente. Por favor, inicia sesión.')
            return response
        except Exception as e:
            messages.error(self.request, 'Error al crear la cuenta. Por favor, intenta nuevamente.')
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return super().form_invalid(form)

class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileUpdateForm
    template_name = 'registration/profile.html'
    success_url = reverse_lazy('eventHome')

    def get_object(self):
        return self.request.user
