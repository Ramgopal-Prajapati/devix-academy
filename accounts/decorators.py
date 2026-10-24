from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib.auth.mixins import AccessMixin
from .models import User


def branch_head_required(view_func):
    """Decorator ensuring the logged in user is the Branch Head."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_branch_head:
            raise PermissionDenied("Access restricted to Branch Head only.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def trainer_required(view_func):
    """Decorator ensuring the logged in user is a Trainer."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_trainer:
            raise PermissionDenied("Access restricted to Trainers only.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def student_required(view_func):
    """Decorator ensuring the logged in user is a Student."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_student:
            raise PermissionDenied("Access restricted to Students only.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


class BranchHeadRequiredMixin(AccessMixin):
    """Verify that the current user is Branch Head."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_branch_head:
            raise PermissionDenied("Access restricted to Branch Head only.")
        return super().dispatch(request, *args, **kwargs)


class TrainerRequiredMixin(AccessMixin):
    """Verify that the current user is a Trainer."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_trainer:
            raise PermissionDenied("Access restricted to Trainers only.")
        return super().dispatch(request, *args, **kwargs)


class StudentRequiredMixin(AccessMixin):
    """Verify that the current user is a Student."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_student:
            raise PermissionDenied("Access restricted to Students only.")
        return super().dispatch(request, *args, **kwargs)
