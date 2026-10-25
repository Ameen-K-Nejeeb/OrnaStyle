from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def staff_or_vendor_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_custom_admin() or request.user.is_vendor():
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("Access restricted to Vendors and Admin personnel.")
    return wrapper