from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View

from orbat.models import UnitApplication, SectionApplication, Section
from orbat.views import ORBATBaseView
from unithub.views import UnitHubBaseView


class ORBATApplicationLOA(View):
    template_name = 'orbat_section_detail.html'

class ORBATApplicationJoin(View):
    template_name = 'orbat_section_detail.html'

class ORBATApplicationOverview(ORBATBaseView):
    template_name = 'orbat_applications.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_staff: #TODO Add J1 Department
            context['unit_application_perms'] = True
            context['unit_applications'] = UnitApplication.objects.filter(processed_date=None).order_by('date')

        managed_section = Section.objects.filter(leader=self.request.user).first()

        if self.request.user.is_staff or managed_section:
            if not managed_section:
                section_applications = SectionApplication.objects.filter(processed_date=None).order_by('date')
            else:
                section_applications = SectionApplication.objects.filter(processed_date=None, section_slot__section=managed_section).order_by('date')
            context['section_application_perms'] = True
            context['section_applications'] = section_applications

        return context

class UnitApplicationOnboarding(ORBATBaseView):
    template_name = 'orbat_applications_onboarding.html'

    def _get_application(self):
        pk = self.kwargs.get("pk")
        if not pk:
            self.add_message("No application found.", level=messages.ERROR)
            return None
        try:
            return UnitApplication.objects.get(pk=pk, processed_date__isnull=True)
        except UnitApplication.DoesNotExist:
            self.add_message("Application does not exist.", level=messages.ERROR)
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        app = self._get_application()
        if app:
            context["focused_application"] = app
            other_qs = (
                UnitApplication.objects.filter(processed_date=None)
                .order_by("date")[:10]
            )

            context["slide_json"] = {
                "id": app.pk,
                "user_id": str(app.user.id) if app.user else None,
                "username": app.user.username if app.user else "",
                "teamspeak_id": app.teamspeak_id,
                "over_18": app.over_18,
            }
        else:
            other_qs = UnitApplication.objects.filter(processed_date=None).order_by("date")[:10]
        context["other_applications"] = other_qs
        return context


class UnitApplicationUserManager(UnitApplicationOnboarding):

    def _redirect(self, app=None):
        """Redirect back to the same page (or base page if no app)."""
        if app:
            return redirect("orbat_applications_onboarding", pk=app.pk)
        return redirect(reverse("orbat_applications_onboarding_list"))

    def post(self, request, *args, **kwargs):
        app = self._get_application()
        if not app:
            return self._redirect()

        # Determine action
        method = request.POST.get('_method', 'create').lower()

        if method == 'delete':
            if not app.user:
                self.add_message("No user found to delete.", level=messages.ERROR)
                return self._redirect(app)
            user = app.user
            name = user.display_name
            user.delete()
            app.user = None
            app.save()
            self.add_message(f"User {name} deleted.", level=messages.INFO)
            return self._redirect(app)

        # For create / update
        name = request.POST.get('name', '').strip()
        teamspeak_id = request.POST.get('teamspeak_id') or None
        over_18 = request.POST.get('over18') == 'true'

        User = get_user_model()

        if method == 'create':
            if not name:
                self.add_message("Name is required to create a user.", level=messages.ERROR)
                return self._redirect(app)
            if User.objects.filter(display_name=name).exists():
                self.add_message(f"A user with the name '{name}' already exists.", level=messages.ERROR)
                return self._redirect(app)
            user = User.objects.create(username=name, display_name=name)
            app.user = user
            app.teamspeak_id = teamspeak_id
            app.over_18 = over_18
            app.save()
            self.add_message(f"User '{user.display_name}' created.", level=messages.INFO)
            return self._redirect(app)

        elif method == 'update':
            if app.user:
                user = app.user
                if name:
                    user.display_name = name
                    user.username = name
                    user.save()
            app.teamspeak_id = teamspeak_id
            app.over_18 = over_18
            app.save()
            if app.user:
                self.add_message(f"Application for '{app.user.display_name}' updated.", level=messages.INFO)
            else:
                self.add_message(f"Application for {app.external_account.username} updated.", level=messages.INFO)
            return self._redirect(app)

        # Fallback
        return self._redirect(app)