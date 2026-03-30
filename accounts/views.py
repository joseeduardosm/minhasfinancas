"""Views do app de autenticacao (accounts)."""

from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render


class CustomLoginView(LoginView):
    """View de login com template proprio do app accounts."""

    template_name = "accounts/login.html"
    redirect_authenticated_user = True


def signup_view(request):
    """Permite criar um novo usuario local e autentica-lo em seguida."""
    if request.user.is_authenticated:
        return redirect("welcome:home")

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("welcome:home")
    else:
        form = UserCreationForm()

    return render(request, "accounts/signup.html", {"form": form})


def home_redirect(request):
    """Redireciona usuarios para login ou area de boas-vindas."""
    if request.user.is_authenticated:
        return redirect("welcome:home")
    return redirect("accounts:login")


def logout_view(request):
    """Realiza logout via GET para suportar link simples no menu."""
    logout(request)
    return redirect("accounts:login")
