from django.urls import include, path

urlpatterns = [path('api/center-pro/', include('center_pro.urls'))]
