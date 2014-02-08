from django.contrib.gis.geos.geometry import GEOSGeometry
from django.conf import settings
from django.core.files.base import File, ContentFile
from django.db.models.fields.files import FieldFile

from smartfields.models import FileField
from smartfields.utils import from_string_import

GEO_CONVERTER = from_string_import(
    getattr(settings, 'SMARTFIELDS_GEO_CONVERTER', 
            'smartfields.gis.utils.GeoConverter'))

if 'south' in settings.INSTALLED_APPS:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules(
        [], ["^smartfields\.gis\.models\.fields\.GeoFileField"])


class GeoFieldFile(FieldFile):
    converter_class = GEO_CONVERTER

    def update_file(self, **kwargs):
        if self:
            self.delete(save=False)
        if isinstance(self.field.geometry, basestring):
            name = self.field.geometry
            geometry = getattr(self.instance, self.field.geometry)
        else:
            name = 'geometry'
            geometry = self.field.geometry
        if not isinstance(geometry, GEOSGeometry):
            raise TypeError("'geometry' has to be either a GEOSGeometry type or"
                            " a string name of a non-empty GeometryField. %s" % 
                            type(geometry))
        self.name = self.field.generate_filename(
            self.instance, "%s.%s" % (name, self.field.format.lower()))
        file_path = self.storage.path(self.name)
        converter = self.converter_class(geometry, encoder=self.field.encoder)
        content = converter.convert(
            file_path, format=self.field.format, instance=self.instance, **kwargs)
        if content is not None:
            self.save(self.name, ContentFile(content), save=False)
        self._commited = True
        setattr(self.instance, self.field.name, self.name)



class GeoFileField(FileField):
    attr_class = GeoFieldFile
    
    def __init__(self, geometry=None, format='KML', encoder=None, **kwargs):
        self.geometry = geometry
        self.format = format
        self.encoder = encoder
        super(GeoFileField, self).__init__(**kwargs)
            
