"""Paid Go profiles with pinned request counting; no free/Contributor fallback."""
import datetime

PROFILE_VERSION='openshell-go-v4'
PROFILES={
 'glm':{'model':'opencode-go/glm-5.3-flash','name':'GLM 5.3 Flash','tokenizer':'glm','input':0.15,'output':0.50,'context':1000000},
 'deepseek':{'model':'opencode-go/deepseek-v4.1-flash','name':'DeepSeek V4.1 Flash','tokenizer':'deepseek','input':0.15,'output':0.60,'context':1000000,'valid_until':'2026-10-31'},
 'glm-full':{'model':'opencode-go/glm-5.3','name':'GLM 5.3','tokenizer':'glm-full','input':1.40,'output':4.40,'context':1000000},
 'glm52':{'model':'opencode-go/glm-5.2','name':'GLM 5.2','tokenizer':'glm52','input':1.40,'output':4.40,'context':1000000},
 'minimax':{'model':'opencode-go/minimax-m3.1-flash','name':'MiniMax M3.1 Flash','tokenizer':'minimax','input':0.15,'output':0.60,'context':1000000},
}


def available(key):
    p=PROFILES[key]
    return not p.get('valid_until') or datetime.date.today().isoformat()<=p['valid_until']
