from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from .forms import CustomLoginForm, CustomPasswordChangeForm


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = CustomLoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, f"Welcome back, {form.get_user().display_name}!")
        return super().form_valid(form)


@login_required
def role_redirect_view(request):
    """Redirects authenticated users to their respective role dashboard."""
    user = request.user
    if user.must_change_password:
        messages.info(request, "Please update your password before proceeding.")
        return redirect('accounts:change_password')

    if user.is_branch_head:
        return redirect('branch_head:dashboard')
    elif user.is_trainer:
        return redirect('trainer:dashboard')
    elif user.is_student:
        return redirect('student:dashboard')
    else:
        messages.warning(request, "Unrecognized user role.")
        return redirect('public_home')


def custom_logout_view(request):
    """Logs out user and redirects to login page."""
    logout(request)
    messages.info(request, "You have been successfully logged out.")
    return redirect('accounts:login')


class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/change_password.html'
    form_class = CustomPasswordChangeForm
    success_url = reverse_lazy('accounts:role_redirect')

    def form_valid(self, form):
        # Clear must_change_password flag
        user = form.save()
        if user.must_change_password:
            user.must_change_password = False
            user.save(update_fields=['must_change_password'])
        messages.success(self.request, "Your password has been updated successfully!")
        return super().form_valid(form)


def permission_denied_view(request, exception=None):
    """Custom 403 Forbidden handler."""
    return render(request, '403.html', {'message': str(exception) if exception else None}, status=403)
