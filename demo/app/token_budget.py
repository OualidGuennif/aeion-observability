"""Pinned local token counts; closed-profile byte bounds are for cost reservation only."""
import json
import unicodedata
from pathlib import Path
from json_input import loads
from profiles import PROFILES

ROOT = Path(__file__).resolve().parent.parent
MODELS = {p["model"].split("/",1)[1]:p["tokenizer"] for p in PROFILES.values()}
HARD_CONTEXT_LIMIT = 300000
PROVIDER_RESERVE = 20000
MAX_OUTPUT = 65536


class TokenBudget:
    def __init__(self, model):
        if model not in MODELS:
            raise ValueError('CONTEXT_UNKNOWN')
        self.context_basis = 'local_tokenizer'
        if MODELS[model] is None:
            # Keep the byte bound for cost reservation, never as a measured context count.
            self.tokenizer = None
            self.revision = 'unicode-byte-bound-v1'
            self.context_basis = 'provider_usage'
            return
        # Imported here, not at module scope: the bootstrap helpers and the teardown tests
        # must be importable on a host that has neither the tokenizer wheels nor jinja2.
        from jinja2.sandbox import ImmutableSandboxedEnvironment
        from tokenizers import Tokenizer
        slug = MODELS[model]
        path = ROOT / "tokenizers" / slug
        self.tokenizer = Tokenizer.from_file(str(path / "tokenizer.json"))
        self.config = json.loads((path / "tokenizer_config.json").read_text())
        environment = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True, extensions=["jinja2.ext.loopcontrols"])
        environment.filters["tojson"] = lambda value, **kw: json.dumps(value, **{"ensure_ascii": False, **kw})
        def refuse(_message):
            raise ValueError("CONTEXT_UNKNOWN")
        environment.globals["raise_exception"] = refuse
        self.template = environment.from_string((path / "chat_template.jinja").read_text())
        self.revision = json.loads((ROOT / "tokenizers.json").read_text())[slug]["revision"]

    def count(self, payload):
        messages = payload.get("messages")
        if not isinstance(messages, list) or not messages or len(messages) > 256:
            raise ValueError("CONTEXT_UNKNOWN")
        if self.tokenizer is None:
            def text_blocks(content):
                if content is None or isinstance(content, str):
                    return
                if not isinstance(content, list):
                    raise ValueError('CONTEXT_UNKNOWN')
                for block in content:
                    if not isinstance(block, dict):
                        raise ValueError('CONTEXT_UNKNOWN')
                    kind = block.get('type')
                    if kind in ('text', 'thinking'):
                        field = 'text' if kind == 'text' else 'thinking'
                        if not isinstance(block.get(field), str):
                            raise ValueError('CONTEXT_UNKNOWN')
                    elif kind == 'tool_result':
                        text_blocks(block.get('content'))
                    elif kind != 'tool_use':
                        # A byte count cannot bound remote images or hidden provider state.
                        raise ValueError('CONTEXT_UNKNOWN')
            for message in messages:
                if not isinstance(message, dict) or message.get('role') not in {'system', 'user', 'assistant', 'tool'}:
                    raise ValueError('CONTEXT_UNKNOWN')
                text_blocks(message.get('content'))
            text = json.dumps(payload, ensure_ascii=False, allow_nan=False, sort_keys=True)
            size = max(len(text.encode('utf-8')), len(unicodedata.normalize('NFKC', text).encode('utf-8')))
            return 2 * size + 512 * len(messages) + 16384
        messages = json.loads(json.dumps(messages))
        for message in messages:
            if message.get("role") not in {"system", "user", "assistant", "tool"}:
                raise ValueError("CONTEXT_UNKNOWN")
            content = message.get("content")
            if isinstance(content, list):
                if any(not isinstance(v, dict) or v.get("type") != "text" or not isinstance(v.get("text"), str) for v in content):
                    raise ValueError("CONTEXT_UNKNOWN")
            elif content is not None and not isinstance(content, str):
                raise ValueError("CONTEXT_UNKNOWN")
            for call in message.get("tool_calls", []):
                function = call.get("function", call)
                if isinstance(function.get("arguments"), str):
                    function["arguments"] = loads(function["arguments"])
        rendered = self.template.render(messages=messages, tools=payload.get("tools", []),
                                        add_generation_prompt=True, drop_thinking=False, clear_thinking=False,
                                        **self.config)
        if not rendered:
            raise ValueError("CONTEXT_UNKNOWN")
        return len(self.tokenizer.encode(rendered, add_special_tokens=False).ids)


def admit(input_tokens, max_output):
    if type(input_tokens) is not int or input_tokens < 1 or type(max_output) is not int or not 1 <= max_output <= MAX_OUTPUT:
        raise ValueError("CONTEXT_UNKNOWN")
    return input_tokens + max_output + PROVIDER_RESERVE <= HARD_CONTEXT_LIMIT
