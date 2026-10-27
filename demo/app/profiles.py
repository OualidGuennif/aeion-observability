"""Paid Go profiles with pinned request counting; no free/Contributor fallback.

Prices are USD per 1M tokens from the OpenCode Go page (checked 2026-10-27). DeepSeek uses its
peak rate so the harness estimate stays an upper bound; estimates are never invoices.
"""
import datetime

PROFILE_VERSION='flue-openshell-v1'
PROFILES={
 'glm':{'model':'opencode-go/glm-5.3-flash','name':'GLM 5.3 Flash','tokenizer':'glm','input':0.15,'output':0.50,'cache_read':0.03,'context':1000000},
 'deepseek':{'model':'opencode-go/deepseek-v4.1-flash','name':'DeepSeek V4.1 Flash','tokenizer':'deepseek','input':0.30,'output':1.20,'cache_read':0.006,'context':1000000,'valid_until':'2026-10-31'},
 'glm-full':{'model':'opencode-go/glm-5.3','name':'GLM 5.3','tokenizer':'glm-full','input':1.40,'output':4.40,'cache_read':0.26,'context':1000000},
 'glm52':{'model':'opencode-go/glm-5.2','name':'GLM 5.2','tokenizer':'glm52','input':1.40,'output':4.40,'cache_read':0.26,'context':1000000},
 'minimax':{'model':'opencode-go/minimax-m3.1-flash','name':'MiniMax M3.1 Flash','tokenizer':'minimax','input':0.15,'output':0.60,'cache_read':0.015,'context':1000000},
}


def available(key):
    p=PROFILES[key]
    return not p.get('valid_until') or datetime.date.today().isoformat()<=p['valid_until']


def model_metadata(key):
    # Single source for the harness provider: catalog id, context window and price rates.
    p=PROFILES[key]
    return {'id':p['model'].split('/',1)[1],'name':p['name'],'context':p['context'],
            'input':p['input'],'output':p['output'],'cacheRead':p['cache_read']}
