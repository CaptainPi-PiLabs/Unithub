from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View

User = get_user_model()


class UserSearchApi(LoginRequiredMixin, View):
    def get(self,request):
        query = request.GET.get("q", "").strip()
        if len(query) < 2:
            return JsonResponse({"results": []})

        users = (
            User.objects
            .filter(display_name__icontains=query)
            .order_by("display_name")[:10]
        )

        data = [
            {
                "id": str(user.id),
                "name": user.display_name,
            }
            for user in users
        ]

        return JsonResponse({"results": data})