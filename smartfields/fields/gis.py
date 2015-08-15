from django.contrib.gis.db.models import fields

from smartfields.fields import Field

__all__ = [
    'GeometryField', 'PointField', 'LineStringField', 'PolygonField',
    'MultiPointField', 'MultiLineStringField', 'MultiPolygonField',
    'GeometryCollectionField'
]

class GeometryField(Field, fields.GeometryField):
    pass


class PointField(GeometryField, fields.PointField):
    pass


class LineStringField(GeometryField, fields.LineStringField):
    pass


class PolygonField(GeometryField, fields.PolygonField):
    pass


class MultiPointField(GeometryField, fields.MultiPointField):
    pass


class MultiLineStringField(GeometryField, fields.MultiLineStringField):
    pass


class MultiPolygonField(GeometryField, fields.MultiPolygonField):
    pass


class GeometryCollectionField(GeometryField, fields.GeometryCollectionField):
    pass
