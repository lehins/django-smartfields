from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.template.response import TemplateResponse
from django.forms import ModelForm

import json, new

def json_response(context):
    return HttpResponse(json.dumps(context), mimetype="application/json")

__all__ = (
    "FileUploadView",
)

class FileUploadView(View):
    model_form = None
    field_name = None
    prefix=None
    has_permission = None

    @method_decorator(login_required)
    @method_decorator(csrf_protect)
    def dispatch(self, request, pk=None, *args, **kwargs):
        if not pk:
            raise Http404
        if not (self.has_permission and callable(self.has_permission) and
                self.model_form and self.field_name):
            return HttpResponse("Missing required implementation", code=501)
        obj = get_object_or_404(self.model_form._meta.model, pk=pk)
        if not self.has_permission(obj, request.user):
            return HttpResponseForbidden()
        return super(FileUploadView, self).dispatch(
            request, obj=obj, *args, **kwargs)

    def complete(self, request, obj=None):
        form = self.model_form(instance=obj, prefix=self.prefix)
        field = form.fields.get(self.field_name, None)
        value = obj.__dict__[self.field_name]
        if not field:
            raise Http404
        return json_response({
                'task': 'uploading',
                'result': 'complete',
                'rendered_result': field.widget.render_initial(
                    form.add_prefix(self.field_name), value)
                })

    def post(self, request, obj=None):
        UploadMeta = new.classobj("UploadMeta", (), { 
                'model': self.model_form._meta.model, 
                'fields': (self.field_name,) 
                }) 
        UploadForm = new.classobj("UploadForm", (ModelForm,), { 
                "Meta": UploadMeta 
                }) 
        form = UploadForm(
            instance=obj, data=request.POST, files=request.FILES, prefix=self.prefix)
        if form.is_valid():
            obj = form.save()
            return self.complete(request, obj=obj)
        errors = form.errors.get(form.add_prefix(self.field_name))
        return json_response({
                'task': 'uploading',
                'result': 'failed',
                'errors': errors})

    def get(self, request, obj=None):
        form = self.model_form(instance=obj, prefix=self.prefix)
        field = form.fields.get(self.field_name, None)
        value = obj.__dict__[self.field_name]
        if not field:
            raise Http404
        return json_response({
                'task': 'uploading',
                'result': 'complete',
                'rendered_result': field.widget.render_initial(
                    form.add_prefix(self.field_name), value)
                })
