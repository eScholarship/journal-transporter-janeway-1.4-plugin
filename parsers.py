import json

from django.http import QueryDict
from rest_framework import parsers


class MultiPartJSONParser(parsers.MultiPartParser):
    """
    Parses a multipart request with stringified JSON passed as "json".

    Any other data is overwritten with the parsed JSON.
    """
    def parse(self, stream, media_type=None, parser_context=None):
        result = super().parse(
            stream,
            media_type=media_type,
            parser_context=parser_context
        )

        raw_json = result.data.get("json")
        data = json.loads(raw_json) if raw_json else result.data

        qdict = QueryDict('', mutable=True)
        qdict.update(data)
        return parsers.DataAndFiles(qdict, result.files)
