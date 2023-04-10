from django.shortcuts import redirect
from .models import *

#RE-DIRECT TO ERROR PAGE or LOGIN page 
class RequestFromAdminMixin:
    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            profile = Admin.objects.filter(email = request.user.email)
            if profile:
                return super().dispatch(request, *args, **kwargs)
        return redirect('login')

class RequestFromUserMixin:
    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            profile = UserProfile.objects.filter(email = request.user.email)
            if profile:
                return super().dispatch(request, *args, **kwargs)
        return redirect('login')
