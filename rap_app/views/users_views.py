from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm, PasswordResetForm, UserChangeForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

### 📌 Inscription d'un utilisateur
def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Connexion automatique après l'inscription
            messages.success(request, "Inscription réussie !")
            return redirect("user-profile")
    else:
        form = UserCreationForm()
    return render(request, "users/register.html", {"form": form})

### 📌 Connexion
def user_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Connexion réussie !")
            return redirect("user-profile")
    else:
        form = AuthenticationForm()
    return render(request, "users/login.html", {"form": form})

### 📌 Déconnexion
def user_logout(request):
    logout(request)
    messages.success(request, "Vous êtes déconnecté.")
    return redirect("login")

### 📌 Profil utilisateur (Protégé par login_required)
@login_required
def user_profile(request):
    return render(request, "users/profile.html", {"user": request.user})

### 📌 Changement de mot de passe
@login_required
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Mot de passe mis à jour !")
            return redirect("user-profile")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "users/change_password.html", {"form": form})

### 📌 Réinitialisation du mot de passe
def reset_password(request):
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(request=request)
            messages.success(request, "Email de réinitialisation envoyé !")
            return redirect("login")
    else:
        form = PasswordResetForm()
    return render(request, "users/reset_password.html", {"form": form})

### 📌 Liste des utilisateurs (Protégé)
class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = "users/user_list.html"
    context_object_name = "users"
    ordering = ["username"]

### 📌 Détail d'un utilisateur
class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "users/user_detail.html"
    context_object_name = "user"

### 📌 Mise à jour du profil utilisateur
class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = UserChangeForm
    template_name = "users/user_update.html"

    def get_success_url(self):
        return reverse_lazy("user-profile")

    def test_func(self):
        return self.get_object() == self.request.user

### 📌 Suppression d'un utilisateur
class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = User
    template_name = "users/user_delete.html"
    success_url = reverse_lazy("user-list")

    def test_func(self):
        return self.get_object() == self.request.user
