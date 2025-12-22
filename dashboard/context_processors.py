from .models import NavShortcut

def navigation_links(request):
    return {
        "nav_shortcuts": NavShortcut.objects.all()
    }