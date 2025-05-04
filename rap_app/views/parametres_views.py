from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages

# Fonction pour vérifier si l'utilisateur est un administrateur
def is_admin(user):
    return user.is_authenticated and user.is_staff

# Appliquer le décorateur à la vue
@user_passes_test(is_admin, login_url='/login/')
def parametres(request):
    # Si l'utilisateur n'est pas administrateur, un message est déjà affiché par @user_passes_test
    # Vous pouvez ajouter un message supplémentaire si nécessaire
    if not request.user.is_staff:
        messages.error(request, "Vous devez être administrateur pour accéder à cette page.")
        return redirect('home')  # Redirigez vers une autre page si nécessaire
    return render(request, 'parametres/parametres.html')