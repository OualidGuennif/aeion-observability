"""Paid Go profiles with pinned request counting; no free/Contributor fallback.

Prices are USD per 1M tokens from the OpenCode Go page (checked 2026-10-27). DeepSeek uses its
peak rate so the harness estimate stays an upper bound; estimates are never invoices. MiniMax
M3.1 Flash keeps the pinned Go rates already recorded here (0.15/0.60/0.015, context 1000000).

`budget_multiplier` is what one list-price dollar costs the factory budget. Go reports a plan
`allowance` draw beside `list_cost`, at a fixed multiple per model; the budget counts the larger.
Measured 2026-11-06 (work/validation.md): GLM 1.33, DeepSeek 1.2, Qwen 2.67, Haiku 4, Luna 4,
rounded up. MiniMax has no measured multiple yet: 4 is the highest measured Go multiple, an
upper bound until this model is measured, not a measured MiniMax rate.
"""
import datetime

PROFILE_VERSION='flue-openshell-v4'
PROFILES={
 'glm':{'model':'opencode-go/glm-5.3-flash','name':'GLM 5.3 Flash','tokenizer':'glm','input':0.15,'output':0.50,'cache_read':0.03,'context':1000000,'budget_multiplier':'1.34'},
 'deepseek':{'model':'opencode-go/deepseek-v4.1-flash','name':'DeepSeek V4.1 Flash','tokenizer':'deepseek','input':0.30,'output':1.20,'cache_read':0.006,'context':1000000,'budget_multiplier':'1.2'},
 'glm-full':{'model':'opencode-go/glm-5.3','name':'GLM 5.3','tokenizer':'glm-full','input':1.40,'output':4.40,'cache_read':0.26,'context':1000000},
 'glm52':{'model':'opencode-go/glm-5.2','name':'GLM 5.2','tokenizer':'glm52','input':1.40,'output':4.40,'cache_read':0.26,'context':1000000},
}

# Runtime profiles follow the owner's four-model allowlist. Older entries remain readable
# for historical reports but cannot start a worker. Prices use the documented upper tier.
PROFILES.update({
 'qwen': {'model':'opencode-go/qwen3.8-flash','name':'Qwen 3.8 Flash','tokenizer':None,
          'input':0.15,'output':0.47,'cache_read':0.016,'cache_write':0.20,'context':1000000,
          'api':'anthropic-messages','thinking':'max','counting':'provider-usage-v1',
          'budget_multiplier':'2.67'},
 'haiku': {'model':'opencode-go/claude-haiku-5-5','name':'Claude Haiku 5.5','tokenizer':None,
           'input':0.50,'output':2.50,'cache_read':0.05,'cache_write':0.625,'context':1000000,
           'api':'anthropic-messages','thinking':'max','counting':'provider-usage-v1',
           'budget_multiplier':'4'},
 # Owner request 2026-11-06. Measured that day: GPT-6 Luna validates reasoning_effort and accepts
 # "max" on Go chat completions.
 'luna': {'model':'opencode-go/gpt-6-luna','name':'GPT-6 Luna','tokenizer':None,
          'input':0.20,'output':0.75,'cache_read':0.02,'cache_write':0.25,'context':1050000,
          'counting':'provider-usage-v1','efforts':{'max':'max','low':'low'},'budget_multiplier':'4'},
 # Owner request 2026-11-08: replace Mistral Large 4. No effort map until one is measured,
 # so the relay does not send reasoning_effort. budget_multiplier 4 is the unmeasured upper bound.
 'minimax': {'model':'opencode-go/minimax-m3.1-flash','name':'MiniMax M3.1 Flash','tokenizer':'minimax',
             'input':0.15,'output':0.60,'cache_read':0.015,'context':1000000,
             'counting':'provider-usage-v1','budget_multiplier':'4'},
})


# The owner-authorized workers are keyed by the factory catalog, which is the one
# eligibility authority: this module must not keep a second expiry for them.
SHARED_MODELS = {'glm': 'glm-5.3-flash', 'deepseek': 'deepseek-4.1-flash',
                 'qwen': 'qwen-3.8-flash', 'haiku': 'claude-haiku-5.5',
                 'luna': 'gpt-6-luna', 'minimax': 'minimax-m3.1-flash'}


def available(key):
    shared = SHARED_MODELS.get(key)
    if shared is not None:
        from factory.models import eligibility
        return eligibility(shared)[0]
    return False


def budget_multiplier(key):
    # No measured multiple means no paid run: an unknown allowance rate fails closed.
    value = PROFILES[key].get('budget_multiplier')
    if value is None:
        raise ValueError('BUDGET_MULTIPLIER_UNKNOWN')
    return value


def model_metadata(key):
    # Single source for the harness provider: catalog id, context window and price rates.
    p=PROFILES[key]
    return {'id':p['model'].split('/',1)[1],'name':p['name'],'context':p['context'],
            'input':p['input'],'output':p['output'],'cacheRead':p['cache_read'],
            'cacheWrite':p.get('cache_write',0),'api':p.get('api','openai-completions'),
            'thinking':p.get('thinking')}
