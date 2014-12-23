from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'smartfields/', include('smartfields.urls', namespace='smartfields')),
)