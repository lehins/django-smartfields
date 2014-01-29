import simplekml

from django.contrib.gis.geos import Point, LineString, LinearRing, Polygon, \
    GeometryCollection
from django.utils.six import StringIO

from smartfields.utils import create_dirs

class KMLEncoder(object):
    def __init__(self, geometry, geo_processor=None):
        self.geometry = geometry
        self._kml = simplekml.Kml()
        if callable(geo_processor):
            self._processor = geo_processor
        
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
            for mg in g:
                self._encode(obj, mg)
        if obj:
            self._processor(obj)
        return kml

    @property
    def kml(self):
        return self._encode(self._kml, self.geometry)

class GMapsJSEncoder(object):
    def __init__(self, geometry):
        self.geometry = geometry
        self.b = StringIO()

    def writeLatLng(self, p):
        self.b.write("new l(")
        self.b.write(p[1])
        self.b.write(",")
        self.b.write(p[0])
        self.b.write(")")

    def writePolyline(self, polyline):
        self.b.write("processors.polyline(new pl({path:[")
        for p in polyline:
            self.writeLatLng(p)
            self.b.write(",")
        self.b.seek(-1,1)
        self.b.write("]}))")

    def writePolygon(self, polygon):
        self.b.write("processors.polygon(new pg({paths:[")
        for ls in polygon:
            self.b.write("[")
            for p in ls[:-1]: # we don't need to include last point
                self.writeLatLng(p)
                self.b.write(",")
            self.b.seek(-1,1)
            self.b.write("],")
        self.b.seek(-1,1)
        self.b.write("]}))")

    def writeGeometry(self, g):
        if isinstance(g, Point):
            self.writePoint(p)
        elif isinstance(g, LineString):
            self.writePolyline(g)
        elif isinstance(g, LinearRing):
            self.writePolygon([g])
        elif isinstance(g, Polygon):
            self.writePolygon(g)
        elif isinstance(g, GeometryCollection):
            self.b.write("[")
            for subg in g:
                self.writeGeometry(subg)
                self.b.write(",")
            self.b.seek(-1, 1)
            self.b.write("]")

    @property
    def js(self):
        self.b.write(
            "function construct(processors){"
            "var id=function(o){return o;}, l=google.maps.LatLng;"
            "var pl=google.maps.Polyline, pg=google.maps.Polygon;"
            "processors = processors || {};"
            "processors['polyline']=processors['polyline'] || id;"
            "processors['polygon']=processors['polygon'] || id;return ")
        self.writeGeometry(self.geometry)
        self.b.write(";}")
        value = self.b.getvalue()
        self.b.close()
        return value


class GeoConverter(object):

    def __init__(self, geometry):
        self.geometry = geometry

    def convert(self, path, format, **kwargs):
        format = format.lower()
        if format in ['kml', 'kmz']:
            geo_processor = kwargs.get('geo_processor', None)
            kml_processor = kwargs.get('kml_processor', None)
            encoder = KMLEncoder(self.geometry, geo_processor=geo_processor)
            kml = encoder.kml
            if callable(kml_processor):
                kml = kml_processor(kml)
            pretty = kwargs.get('pretty', False)
            create_dirs(path)
            if format == 'kml':
                kml.save(path, format=pretty)
            elif format == 'kmz':
                kml.savekmz(path, format=pretty)
            return open(path)
        elif format == "js":
            encoder = GMapsJSEncoder(self.geometry)
            create_dirs(path)
            file = open(path, 'w')
            file.write(encoder.js)
            return file
        raise AttributeError(u"Unknown format: %s" % format)

