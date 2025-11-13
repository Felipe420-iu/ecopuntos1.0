from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import Notificacion

@login_required
@require_POST
def clear_notifications(request):
    Notificacion.objects.filter(usuario=request.user).delete()
    return JsonResponse({'success': True})