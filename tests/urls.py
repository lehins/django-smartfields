from django.conf.urls import include, url

urlpatterns = [
    url(r'smartfields/', include('smartfields.urls', namespace='smartfields')),
]
