from django.conf.urls import patterns, url

from smartfields.views import FileUploadView

urlpatterns = patterns('',
    url(r'upload/(?P<app_label>\w+)/(?P<model>\w+)/(?P<field_name>\w+)/(?:(?P<pk>\d+)/)?'
        r'(?:(?P<parent_field_name>\w+)/(?P<parent_pk>\d+)/)?$',
        FileUploadView.as_view(), name='upload'),
)