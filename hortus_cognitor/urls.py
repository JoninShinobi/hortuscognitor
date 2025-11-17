from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from courses.views import home, regenerative_movement_course, contact, about, privacy_policy
from django.http import HttpResponse

def health_check(request):
    return HttpResponse("Django is working! ✅")

def simple_home(request):
    return HttpResponse("<h1>Hortus Cognitor</h1><p>Simple home page working!</p>")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    path('test/', simple_home, name='simple_home'),
    path('', home, name='home'),
    path('about/', about, name='about'),
    path('contact/', contact, name='contact'),
    path('privacy-policy/', privacy_policy, name='privacy_policy'),
    path('regenerative-movement-course/', regenerative_movement_course, name='regenerative_movement_course'),
    path('courses/', include('courses.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)