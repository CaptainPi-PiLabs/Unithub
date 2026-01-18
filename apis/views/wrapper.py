from django.contrib import messages


def call_api_view(api_class, request, *args, success_message=None, **kwargs):
    """
        Calls an API view and returns a tuple: (response, success)
        - response: DRF Response or JsonResponse
        - success: True if status < 400 and 'success' in data
        """
    api_view = api_class.as_view()
    response = api_view(request, *args, **kwargs)

    status = getattr(response, "status_code", 200)
    data = getattr(response, "data", None)

    success = False
    if status < 400 and isinstance(data, dict) and data.get("success"):
        success = True
        if success_message:
            messages.success(request, success_message)
    elif status >= 400:
        error = None
        if isinstance(data, dict):
            error = data.get("error")
        messages.error(request, error or f"Request failed: {status}")

    return response, success