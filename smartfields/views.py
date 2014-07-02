import json, types

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.http import Http404, HttpResponse
from django.forms import ModelForm
from django.forms.models import modelform_factory
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.generic import View

__all__ = (
    "FileUploadView",
)


class FileUploadView(View):
    _model = None
    _field_name = None
    parent_field_name = None

    @property
    def model(self):
        if self._model is not None:
            return self._model
        raise ImproperlyConfigured("'model' is a required property")

    @model.setter
    def model(self, value):
        self._model = value

    @property
    def field_name(self):
        if self._field_name is not None:
            return self._field_name
        raise ImproperlyConfigured("'field_name' is a required property")

    @field_name.setter
    def field_name(self, value):
        self._field_name = value

    def has_permission(self, obj, user):
        raise ImproperlyConfigured("'has_permission' is a required method")


    def get_form(self):
        return modelform_factory(self.model, fields=(self.field_name,))


    def get_object(self, pk=None, parent_pk=None):
        kwargs = {}
        manager = self.model.objects
        if parent_pk is not None and self.parent_field_name is not None:
            parent_field = self.model._meta.get_field_by_name(self.parent_field_name)[0]
            parent_model = parent_field.rel.to
            parent_pk_field_name = "%s_%s" % (
                self.parent_field_name, parent_model._meta.pk.name)
            kwargs = {parent_pk_field_name: parent_pk}
            manager = manager.select_related(self.parent_field_name)
        if pk is None:
            obj = self.model(**kwargs)
        else:
            try:
                obj = manager.get(pk=pk, **kwargs)
            except self.model.DoesNotExist: 
                raise Http404
        return obj


    def json_response(self, context, status_code=200):
        return HttpResponse(json.dumps(context), mimetype="application/json",
                            status=status_code)


    @method_decorator(csrf_protect)
    @method_decorator(login_required)
    def dispatch(self, request, pk=None, parent_pk=None, *args, **kwargs):
        obj = self.get_object(pk=pk, parent_pk=parent_pk)
        if not self.has_permission(obj, request.user):
            raise PermissionDenied
        return super(FileUploadView, self).dispatch(
            request, obj, pk=pk, parent_pk=parent_pk, *args, **kwargs)


    def complete(self, obj, status):
        field_file = getattr(obj, self.field_name)
        if field_file:
            status.update({
                'file_name': field_file.name_base,
                'file_url': field_file.url,
                'html_tag': field_file.html_tag
            })
            if field_file.field.manager and field_file.field.manager.dependencies:
                dependencies = {}
                for dep in field_file.field.manager.dependencies:
                    name = dep.get_name(field_file.field)
                    dependencies[name] = getattr(obj, name).url
                status['dependencies'] = dependencies
        return self.json_response(status)


    def get(self, request, obj, *args, **kwargs):
        status = obj.smartfield_status(self.field_name)
        if status['state'] == 'complete':
            return self.complete(obj, status)
        return self.json_response(status)


    def post(self, request, obj, *args, **kwargs):
        status = obj.smartfield_status(self.field_name)
        if status['state'] != 'ready':
            return self.json_response(status)

        # TODO: figure out field key for new objects, so progress reporting would work
        # since urls are preconfigured, when pk is None, maybe use uuid in request.GET
        created = False # necessary hack for status
        if not obj.pk:
            created = True
            obj.save()

        form_class = self.get_form()
        form = form_class(
            instance=obj, data=request.POST, files=request.FILES)
        if form.is_valid():
            obj = form.save()
            return self.get(request, obj, *args, **kwargs)

        if created:
            obj.delete()

        status.update({
            'task': 'uploading',
            'task_name': "Uploading",
            'state': 'error',
            'messages': form.errors.get(self.field_name)
        })
        return self.json_response(status)


    def delete(self, request, obj, *args, **kwargs):
        obj.delete()
        return self.json_response({'task': 'delete', 'result': 'success'})
