from django.contrib.gis.geos.geometry import GEOSGeometry
from django.core.files.base import File
from django.db.models.fields.files import FieldFile

from smartfields.models.fields.files import FileField

GEO_CONVERTER = from_string_import(
    getattr(settings, 'SMARTFIELDS_GEO_CONVERTER', 
            'smartfields.gis.utils.GeoConverter'))

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
                            " a string name of a non-empty GeometryField.")
        file_name = self.field.generate_filename(
            self.instance, "%s.%s" % (name, self.field.format.lower()))
        file_path = self.storage.path(file_name)
        converter = self.converter_class(geometry)
        file = converter.convert(file_path, format=self.field.format, **kwargs)
        self.file = File(file)
        self._size = file.size
        self._commited = True
        self.instance.save()


class GeoFileField(FileField):
    attr_class = GeoFieldFile
    
    def __init__(self, geometry, format='KML', **kwargs):
        self.geometry = geometry
        self.format = format
        super(GeoFileField, self).__init__(**kwargs)
            
