"""Frozen coding tasks and trusted replay solutions; never ship solutions to agent images."""
import json
from pathlib import Path

SCENARIOS=json.loads((Path(__file__).resolve().parent.parent/'fixtures/scenarios.json').read_text())
SOLUTIONS={
 'pricing-js-v1':'''export function totalCents(items, shippingCents=0) {
 const valid=n=>Number.isSafeInteger(n)&&n>=0;
 if(!Array.isArray(items)||!valid(shippingCents))throw new TypeError('invalid');
 let total=shippingCents;
 for(const pair of items){if(!Array.isArray(pair)||pair.length!==2||!pair.every(valid))throw new TypeError('invalid');total+=pair[0]*pair[1];if(!valid(total))throw new TypeError('overflow');}
 return total;
}''',
 'shipping-js-v1':'''export function shippingCents(country,weightGrams,subtotalCents){
 if(!['FR','DE','ES'].includes(country)||!Number.isSafeInteger(weightGrams)||weightGrams<=0||!Number.isSafeInteger(subtotalCents)||subtotalCents<0)throw new TypeError('invalid');
 if(country==='FR')return subtotalCents>=5000?0:weightGrams<=500?350:weightGrams<=2500?550:900;
 return subtotalCents>=10000?0:weightGrams<=1000?800:1400;
}''',
 'discounts-js-v1':'''export function quoteCents(subtotalCents,discountBps=0,shippingCents=0){
 if(![subtotalCents,discountBps,shippingCents].every(n=>Number.isSafeInteger(n)&&n>=0)||discountBps>10000)throw new TypeError('invalid');
 const result=BigInt(subtotalCents)-BigInt(subtotalCents)*BigInt(discountBps)/10000n+BigInt(shippingCents);
 if(result>BigInt(Number.MAX_SAFE_INTEGER))throw new TypeError('overflow');return Number(result);
}''',
 'cart-js-v1':'''export function normalizeCart(rows){
 if(!Array.isArray(rows))throw new TypeError('invalid');const groups=new Map();
 for(const row of rows){if(!row||typeof row!=='object'||typeof row.sku!=='string'||!row.sku||row.sku.trim()!==row.sku||![row.priceCents,row.quantity].every(n=>Number.isSafeInteger(n)&&n>=0))throw new TypeError('invalid');
 const old=groups.get(row.sku);if(old&&old.priceCents!==row.priceCents)throw new TypeError('conflict');const quantity=(old?.quantity??0)+row.quantity;if(!Number.isSafeInteger(quantity))throw new TypeError('overflow');groups.set(row.sku,{sku:row.sku,priceCents:row.priceCents,quantity});}
 return [...groups.values()].sort((a,b)=>a.sku<b.sku?-1:a.sku>b.sku?1:0);
}'''
}


def contract(task_id):
    return SCENARIOS[task_id]['contract']+' Edit only src/pricing.js. No imports, files or tests. The supervisor executes protected checks in OpenShell after you stop.'
