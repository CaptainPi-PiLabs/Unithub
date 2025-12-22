from django.http import JsonResponse
from django.views import View

from users.models import CustomUser


class BulkUserActionView(View):
    def post(self, request, *args, **kwargs):
        user_ids = request.POST.getlist('user_ids[]')
        action = request.POST.get('action')

        users = CustomUser.objects.filter(id__in=user_ids)

        return JsonResponse({"status": "ok", "updated": users.count()})
