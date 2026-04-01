import json

from django.core.serializers.json import DjangoJSONEncoder


def build_collector_transfer_snapshot(artwork, request):
    from artwork.serializers.artwork import ArtworkSerializer

    data = ArtworkSerializer(artwork, context={'request': request}).data
    # JSONField/psycopg2 requires JSON-serializable values (e.g. uuid.UUID → str).
    return json.loads(json.dumps(data, cls=DjangoJSONEncoder))
