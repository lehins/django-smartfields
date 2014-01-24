import simplekml

from django.contrib.gis.geos import Point, LineString, LinearRing, Polygon, \
    GeometryCollection
from django.utils.six import StringIO


class KMLEncoder(object):
    def __init__(self, geometry, geo_processor=None):
        self.geometry = geometry
        self._kml = simplekml.Kml()
        if callable(geo_processor):
            self._processor = geo_processor
        
    def _processor(self, obj):
        return obj

    def _encode(self, kml, g):
        obj = None
        if isinstance(g, Point):
            obj = kml.newpoint()
            obj.coords = [g.get_coords]
        elif isinstance(g, LineString):
            obj = kml.newlinestring()
            obj.coords = g
        elif isinstance(g, LinearRing):
            obj = kml.newlinearring()
            obj.outerboundaryis.coords = g
        elif isinstance(g, Polygon):
            obj = kml.newpolygon()
            obj.outerboundaryis = g[0]
            obj.innerboundaryis = g[1:]
        elif isinstance(g, GeometryCollection):
            obj = kml.newmultigeometry()
            for mg in g:
                self._encode(obj, mg)
        if obj:
            self._processor(obj)
        return kml

    @property
    def kml(self):
        return self._encode(self._kml, self.geometry)


class GeoConverter(object):

    def __init__(self, geometry):
        self.geometry = geometry

    def convert(self, path, format, **kwargs):
        format = format.lower()
        if format in ['kml', 'kmz']:
            encoder = KMLEncoder(self.geometry, geo_processor=geo_processor)
            geo_processor = kwargs.get('geo_processor', None)
            kml_processor = kwargs.get('kml_processor', None)
            kml = encoder.kml
            if callable(kml_processor):
                kml = kml_processor(kml)
            pretty = kwargs.get('pretty', False)            
            if format == 'kml':
                kml.save(path, format=pretty)
            elif format == 'kmz':
                kml.savekmz(path, format=pretty)
        else:
            raise AttributeError(u"Unknown format: %s" % format)
        return open(path)