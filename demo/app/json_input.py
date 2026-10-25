"""Unambiguous JSON at the inference admission boundary."""
import json


def loads(raw):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("CONTEXT_UNKNOWN")
            value[key] = item
        return value
    def finite(_value):
        raise ValueError("CONTEXT_UNKNOWN")
    return json.loads(raw, object_pairs_hook=unique, parse_constant=finite)
