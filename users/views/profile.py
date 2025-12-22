from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from unithub.views import UnitHubBaseView
from users.models import CustomUser


class UserListView(UnitHubBaseView):
    template_name = 'users_list.html'

class ProfileBaseView(UnitHubBaseView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        profile_id = self.kwargs.get("user_id") or user.id
        context['user_profile'] = CustomUser.objects.filter(id=profile_id).first()

        if user.is_authenticated:
            context["show_management"] = user.is_staff

        context["title"] = "Profile"

        context["sidebar"] = [
            {"name": "Overview", "path": f"/profile/{profile_id}/"},
            {"name": "Training", "path": f"/profile/{profile_id}/training/"},
            {"name": "Attendance", "path": f"/profile/{profile_id}/attendance/"},
            {"name": "Timeline", "path": f"/profile/{profile_id}/timeline/"},
        ]

        if context["show_management"]:
            context["sidebar"].append({"name": "Management", "path": "/profile/{profile_id}/management/"})

        return context

@login_required
def toggle_theme(request):
    user = request.user
    user.theme = 'theme-dark' if user.theme == 'theme-light' else 'theme-light'
    user.save()
    return redirect(request.META.get("HTTP_REFERER", "dashboard-home"))

@method_decorator(login_required, name="dispatch")
class MyProfileView(ProfileBaseView):
    template_name = 'user_profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_own_profile'] = True
        context['has_edit_perms'] = True
        return context

class UserProfileView(ProfileBaseView):
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
class MyProfileEditView(ProfileBaseView):
    template_name = 'user_profile_edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['user_profile'] = self.request.user
        context['is_own_profile'] = True
        context['has_edit_perms'] = True
        return context

@method_decorator(login_required, name="dispatch")
class UserProfileEditView(ProfileBaseView):
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

class ORBATTimelineView(ProfileBaseView):
    template_name = 'user_timeline.html'