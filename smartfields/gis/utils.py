import simplekml

from django.contrib.gis.geos import Point, LineString, LinearRing, Polygon, \
    GeometryCollection
from django.utils.six import StringIO

from smartfields.utils import create_dirs

class KMLEncoder(object):
    def __init__(self, geometry, path=None, geo_processor=None, 
                 kml_processor=None, pretty=False, **kwargs):
        self.geometry = geometry
        self.path = path
        self._kml = simplekml.Kml()
        if callable(geo_processor):
            self._processor = geo_processor
        self._kml_processor = kml_processor
        self._pretty = pretty
        
    def _processor(self, obj):
        pass

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
            for sg in g:
                self._encode(obj, sg)
        self._processor(obj)
        return kml

    def get_kml(self):
        kml = self._encode(self._kml, self.geometry)
        if callable(self._kml_processor):
            self._kml_processor(kml)
        return kml

    @property
    def kml(self):
        self.get_kml().save(self.path, format=self._pretty)

    @property
    def kmz(self):
        self.get_kml().savekmz(self.path, format=self._pretty)

class GeoConverter(object):

    def __init__(self, geometry, encoder=None):
        self.geometry = geometry
        self.encoder = encoder or KMLEncoder

    def convert(self, path, format, **kwargs):
        format = format.lower()
        encoder = self.encoder(
            self.geometry, path=path, **kwargs)
        return getattr(encoder, format)

