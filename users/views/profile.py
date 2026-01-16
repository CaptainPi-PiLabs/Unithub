from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.decorators import method_decorator

from core.views import UnitHubTemplateView
from users.models import CustomUser
from users.views import ProfileContextMixin


class UserListView(UnitHubTemplateView):
    template_name = 'users_list.html'

@login_required
def toggle_theme(request):
    user = request.user
    user.theme = 'theme-dark' if user.theme == 'theme-light' else 'theme-light'
    user.save()
    return redirect(request.META.get("HTTP_REFERER", "dashboard-home"))

@method_decorator(login_required, name="dispatch")
class MyProfileView(ProfileContextMixin, UnitHubTemplateView):
    template_name = 'user_profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_own_profile'] = True
        context['has_edit_perms'] = True
        return context

class UserProfileView(ProfileContextMixin, UnitHubTemplateView):
    template_name = 'user_profile.html'

    user_obj = None
    is_own_profile = False
    has_edit_perms = False

    def dispatch(self, request, *args, **kwargs):
        user_id = self.kwargs.get('user_id')
        self.user_obj = CustomUser.objects.filter(id=user_id).first()
        if not self.user_obj:
            messages.error(request, f"User could not be found.")
            return redirect("/")
        self.is_own_profile = request.user.id == self.user_obj.id
        self.has_edit_perms = self.is_own_profile or request.user.is_staff

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['user_profile'] = self.user_obj
        context['is_own_profile'] = self.is_own_profile
        context['has_edit_perms'] = self.has_edit_perms
        return context

@method_decorator(login_required, name="dispatch")
class MyProfileEditView(ProfileContextMixin, UnitHubTemplateView):
    template_name = 'user_profile_edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['user_profile'] = self.request.user
        context['is_own_profile'] = True
        context['has_edit_perms'] = True
        return context

@method_decorator(login_required, name="dispatch")
class UserProfileEditView(ProfileContextMixin, UnitHubTemplateView):
    template_name = 'user_profile_edit.html'

    user_obj = None
    is_own_profile = False
    has_edit_perms = False

    def dispatch(self, request, *args, **kwargs):
        user_id = self.kwargs.get('user_id')
        self.user_obj = CustomUser.objects.filter(id=user_id).first()
        if not self.user_obj:
            messages.error(request, f"Access Denied.")
            return redirect("/")

        self.is_own_profile = self.request.user.id == self.user_obj.id
        self.has_edit_perms = self.is_own_profile or request.user.is_staff

        if not self.has_edit_perms:
            messages.error(request, f"Access Denied.")
            return redirect("/")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['user_profile'] = self.request.user
        context['is_own_profile'] = self.is_own_profile
        context['has_edit_perms'] = self.has_edit_perms

class ORBATTimelineView(ProfileContextMixin, UnitHubTemplateView):
    template_name = 'user_timeline.html'