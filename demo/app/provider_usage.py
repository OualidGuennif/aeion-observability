"""Read only typed usage metadata from SSE; never retain or log text/tool payloads."""
import json
import math


class ReportedUsage:
    def __init__(self):
        self.buffer = b''
        self.ended = False
        self.cost = self.resource_cost = None
        self.input_tokens = self.output_tokens = self.cache_read_tokens = None

    def feed(self, block):
        self.buffer += block
        if len(self.buffer) > 1048576:
            raise ValueError('USAGE_FRAME_TOO_LARGE')
        while b'\n' in self.buffer:
            line, self.buffer = self.buffer.split(b'\n', 1)
            if not line.startswith(b'data:'):
                continue
            data = line[5:].strip()
            if data == b'[DONE]':
                self.ended = True
                continue
            try:
                event = json.loads(data)
            except (ValueError, UnicodeError):
                continue
            if not isinstance(event, dict):
                continue
            if event.get('type') == 'message_stop':
                self.ended = True
            usage = event.get('usage') or (event.get('message') or {}).get('usage')
            if not isinstance(usage, dict):
                continue
            for field, names in (('input_tokens', ('prompt_tokens', 'input_tokens')),
                                 ('output_tokens', ('completion_tokens', 'output_tokens'))):
                for key in names:
                    if type(usage.get(key)) is int and usage[key] >= 0:
                        setattr(self, field, usage[key])
                        break
            details = usage.get('prompt_tokens_details')
            cached = (details.get('cached_tokens') if isinstance(details, dict) and 'prompt_tokens' in usage
                      else usage.get('cache_read_input_tokens'))
            if type(cached) is int and cached >= 0:
                self.cache_read_tokens = cached
            if type(usage.get('input_tokens')) is int and 'prompt_tokens' not in usage:
                cached = [usage.get(key, 0) for key in ('cache_read_input_tokens','cache_creation_input_tokens')]
                self.input_tokens = (usage['input_tokens'] + sum(cached)
                                     if usage['input_tokens'] >= 0 and all(type(v) is int and v >= 0 for v in cached)
                                     else None)
            cost = usage.get('cost', usage.get('cost_usd'))
            if type(cost) in (int, float) and math.isfinite(cost) and cost >= 0:
                self.cost = float(cost)
                amounts = [self.cost]
                detail = usage.get('opencode')
                if isinstance(detail, dict):
                    for key in ('list_cost', 'allowance'):
                        value = detail.get(key)
                        if type(value) in (int, float) and math.isfinite(value) and value >= 0:
                            amounts.append(float(value))
                self.resource_cost = max(amounts)

    def summary(self):
        return {'complete': self.ended and self.cost is not None,
                'cost_usd': self.resource_cost, 'charged_usd': self.cost,
                'input_tokens': self.input_tokens, 'output_tokens': self.output_tokens,
                'cache_read_tokens': self.cache_read_tokens,
                'basis': 'provider_reported_resource_cost' if self.cost is not None else 'provider_cost_unreported'}
