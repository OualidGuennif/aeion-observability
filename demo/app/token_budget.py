"""Local request counting with the official pinned model tokenizer/chat template."""
import json
from pathlib import Path
from jinja2.sandbox import ImmutableSandboxedEnvironment
from tokenizers import Tokenizer
from json_input import loads

ROOT = Path(__file__).resolve().parent.parent
MODELS = {"glm-5.3-flash": "glm", "deepseek-v4.1-flash": "deepseek"}
HARD_CONTEXT_LIMIT = 300000
PROVIDER_RESERVE = 20000
MAX_OUTPUT = 4096


class TokenBudget:
    def __init__(self, model):
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
