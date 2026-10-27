const $ = (id) => document.getElementById(id);
let refreshing = false;
let busy = false, evidence = 'real', cachedRuns = [], cachedRows = [], signature = '', catalog = {}, recommendations = {}, campaigns = [];
const pretty = (n) => Number(n ?? 0).toLocaleString('en-US');
const money = (n) => n == null ? '—' : '$' + Number(n).toFixed(5);
const seconds = (n) => n == null ? '—' : (n / 1000).toFixed(1) + 's';
const label = (name) => Object.values(catalog.profiles??{}).find(p=>p.model===name)?.name ?? (name==='synthetic-replay'?'Synthetic replay':name??'Unknown model');
const taskInfo = (id) => catalog.scenarios?.[id] ?? catalog.triage?.[id];
const checkTotal = (r) => r.check?.total ?? taskInfo(r.task_id ?? 'pricing-js-v1')?.checks ?? '—';
function el(tag, text = '', cls = '') { const e = document.createElement(tag); e.textContent = text; e.className = cls; return e; }
function selected(r) { return r.synthetic === (evidence === 'synthetic') && r.profile_version===catalog.profile_version && (r.runtime??'legacy')===$('runtime').value && (r.task_id??'pricing-js-v1')===$('scenario').value; }
function syncTasks() { const ids=catalog.runtimes?.[$('runtime').value]?.tasks??[]; if(!ids.length||ids.join()===[...$('scenario').options].map(o=>o.value).join())return; $('scenario').replaceChildren(...ids.map(id=>{const o=el('option',taskInfo(id)?.name??id);o.value=id;return o;})); }
function setFilter(value) {
  evidence = value;
  $('recalled').replaceChildren(el('p','Recall analyses from the selected evidence bank.','muted'));
  document.querySelectorAll('[data-filter]').forEach(b => {b.classList.toggle('selected', b.dataset.filter === value); b.setAttribute('aria-pressed', String(b.dataset.filter === value));});
  render();
}
function render() {
  $('task-title').textContent=taskInfo($('scenario').value)?.name??'Cart totals';
  const runs = cachedRuns.filter(selected), rows = cachedRows.filter(selected), latest = runs[0];
  $('runs').replaceChildren(); $('kpi-cards').replaceChildren(); $('model-rows').replaceChildren(); $('checkpoints').replaceChildren();
  const completed = runs.filter(r=>r.ended_ns), successes = completed.filter(r=>r.status==='passed' && !r.human_interventions);
  const costs = runs.reduce((s,r)=>s+Number(r.native_cost_usd),0);
  const costResolved=runs.length>0&&runs.every(r=>r.synthetic||r.usage_complete===true)&&runs.every(r=>r.ended_ns);
  const times = completed.map(r=>(r.ended_ns-r.started_ns)/1e6).sort((a,b)=>a-b);
  const median = times.length ? (times[Math.floor((times.length-1)/2)] + times[Math.ceil((times.length-1)/2)])/2 : null;
  const usages = runs.flatMap(r=>r.events.filter(e=>e.name==='gen_ai.request'));
  const cards = [
    ['Verified autonomy', completed.length ? Math.round(successes.length/completed.length*100)+'%' : '—', `${successes.length} / ${completed.length} completed tasks · fixture only`],
    ['Model cost / success*', successes.length&&costResolved ? money(costs/successes.length) : '—', evidence==='synthetic'?'Synthetic replay · no model calls':costResolved?'All attempts included · CLI estimate':'Usage coverage incomplete · no cost ranking'],
    ['Median elapsed time', seconds(median), `${completed.length} completed tasks · end to end`],
    ['Input + output tokens', pretty(usages.reduce((s,e)=>s+e['gen_ai.usage.input_tokens']+e['gen_ai.usage.output_tokens'],0)), `${runs.reduce((s,r)=>s+r.events.filter(e=>e.name==='agent.handover').length,0)} deterministic handover(s)`]
  ];
  for(const [title,value,note] of cards) { const c=el('article','','kpi');c.append(el('span',title,'eyebrow'),el('strong',value),el('small',note));$('kpi-cards').append(c); }
  $('execution-status').textContent = latest ? latest.status.replaceAll('_',' ') : 'Ready';
  document.querySelector('.execution-panel').classList.toggle('running', latest?.status==='running');
  const peak = Math.max(0,...(latest?.events ?? []).map(e=>e['aeion.context.observed'] ?? 0));
  $('context-value').textContent = `${pretty(peak)} / ${pretty(latest?.limit ?? 250000)}`;
  $('context-fill').style.width = Math.min(100,peak/(latest?.limit ?? 250000)*100)+'%';
  $('active-detail').replaceChildren();
  if(latest) {
    const detail=$('active-detail');
    detail.append(el('p', latest.synthetic ? 'A fresh agent. The same useful work.' : label(latest.model)+' · build', 'detail-heading'));
    const info=el('div','','detail-meta');info.append(el('div',`${latest.agents} agent(s) · ${latest.check?.passed ?? '—'}/${checkTotal(latest)} checks · ${latest.human_interventions ? 'human assisted' : 'no human intervention recorded'}`));
    info.append(el('div',latest.events.some(e=>e.name==='agent.handover') ? 'Old runtime retired. Artifact preserved. New session created.' : 'Fixed task · protected verifier · bounded authority.'));
    info.append(el('code',`Trace ${latest.trace_id ?? 'pending'}`));detail.append(info);
    const statuses=el('div','','memory-status');statuses.append(el('span',latest.claude_mem_id ? `claude-mem · checkpoint #${latest.claude_mem_id} read back` : 'claude-mem · waiting'),el('span',`Hindsight · ${latest.memory?.status ?? 'waiting'}`));detail.append(statuses);
  } else $('active-detail').append(el('p','Start a live build or replay the boundary. Verified execution and memory acknowledgements appear here.'));
  for(const run of runs) {
    const card=el('article','','run'), head=el('div','','run-header');
    head.append(el('h3',run.synthetic ? '250k boundary · synthetic replay' : label(run.model)+' · '+(taskInfo(run.task_id)?.name??run.task_id??'Cart totals')),el('span',run.status.replaceAll('_',' '),'tag'));card.append(head);
    const cost = run.synthetic ? 'synthetic · no model call' : run.usage_complete ? `${money(run.native_cost_usd)} native estimate` : 'cost unresolved';
    card.append(el('div',`${run.agents} agent(s) · ${run.check?.passed ?? '—'}/${checkTotal(run)} checks · ${cost} · ${run.human_interventions ? 'assisted' : 'no intervention recorded'}`,'run-meta'));
    const timeline=el('div','','timeline');
    const names={'agent.started':'Agent started','gen_ai.request':'Model response','gate.closed':'Gate closed','agent.handover':'Fresh session','artifact.checked':'Artifact checked','memory.checkpoint':'Checkpoint read back','app.verified':'Hono API verified','task.failed':'Task stopped','handover.prepared':'Handover MD ready','handover.acknowledged':'MD acknowledged','context.preflight':'Input counted','memory.retained':'Analysis retained','process.retired':'Process retired','session.wiped':'Context wiped','model.step.started':'Model step','tool.finished':'Tool finished'};
    for(const event of run.events) {let text=names[event.name]??event.name;if(event['aeion.context.observed']!==undefined)text+=' · '+pretty(event['aeion.context.observed']);timeline.append(el('span',text,'event'+(['agent.handover','gate.closed'].includes(event.name)?' handover':'')));}
    card.append(timeline);
    const actions=el('div','','run-actions');
    const copy=el('button','Copy trace ID','text-button');copy.onclick=()=>navigator.clipboard?.writeText(run.trace_id ?? '').then(()=>{$('message').textContent='Trace ID copied.';});actions.append(copy);
    if(run.ended_ns && !run.human_interventions) {const assist=el('button','Declare human assistance','text-button');assist.disabled=busy;assist.onclick=async()=>{await post({mode:'intervention',run_id:run.id});};actions.append(assist);}
    const logs=el('a','Correlated logs ↗','text-button');logs.href=`/api/runs/${run.id}/logs`;logs.target='_blank';actions.append(logs);if(run.handover_md_sha256){const md=el('a','HANDOVER.md ↗','text-button');md.href=`/api/runs/${run.id}/handover`;md.target='_blank';actions.append(md);}card.append(actions);if(run.failure)card.append(el('p',run.failure,'fineprint'));$('runs').append(card);
    if(run.claude_mem_id) {const item=el('div','','memory-item');item.append(el('strong',`Checkpoint #${run.claude_mem_id} · ${run.agents} agent(s)`),el('span',`${run.check?.passed ?? 0}/${checkTotal(run)} checks · saved and retrieved`),el('code',`SHA-256 ${run.artifact_sha256 ?? 'pending'}`));$('checkpoints').append(item);}
  }
  if(!runs.length)$('runs').append(el('p',evidence==='real' ? 'No real runs yet. Start a Go build to collect evidence.' : 'Replay the handover to populate this room.','empty'));
  if(!$('checkpoints').children.length)$('checkpoints').append(el('p','No checkpoints in this evidence group yet.','muted'));
  for(const row of rows) {
    const tr=el('tr');const model=el('td',label(row.model));model.append(el('small',`${row.synthetic?'Synthetic':'Real Go'} · ${row.profile_version??'unversioned'} · ${pretty(row.limit)} ${row.metric.replaceAll('_',' ')}`));tr.append(model);
    for(const text of [`${row.completed} / ${row.offered}`,`${row.autonomous} / ${row.completed}`,seconds(row.median_ms),`${pretty(row.input_tokens)} / ${pretty(row.output_tokens)}`,money(row.cost_per_autonomous_success_usd)])tr.append(el('td',text));$('model-rows').append(tr);
  }
  const recommendation=recommendations[$('scenario').value];
  $('decision').textContent = evidence==='synthetic' ? 'Synthetic replay explains the mechanism. It cannot rank real models.' : recommendation?.basis==='best_observed_for_task' ? `${label(recommendation.model)} is the best observed profile for this task (${recommendation.objective}). At least two complete autonomous successes are required. This remains a small sample.` : 'Provisional default: GLM Flash. Collect at least two complete autonomous successes per comparable profile before choosing from measurements.';
  chart(rows);
}
function svg(tag,attrs={},text='') {const e=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,v]of Object.entries(attrs))e.setAttribute(k,String(v));e.textContent=text;return e;}
function chart(rows) {
  const host=$('pareto');host.replaceChildren();const points=rows.filter(r=>r.median_ms!==null&&r.cost_per_autonomous_success_usd!==null);
  for(let i=0;i<4;i++){const y=35+i*58;host.append(svg('line',{x1:65,x2:570,y1:y,y2:y,stroke:'#d5d7c9','stroke-dasharray':'3 5'}));}
  host.append(svg('line',{x1:65,x2:570,y1:225,y2:225,stroke:'#aab5a5'}),svg('line',{x1:65,x2:65,y1:25,y2:225,stroke:'#aab5a5'}));
  host.append(svg('text',{x:65,y:17},'Estimated model cost / autonomous success ($)'),svg('text',{x:390,y:277},'Median elapsed time (seconds) →'));
  const xmax=Math.max(10,...points.map(r=>r.median_ms/1000))*1.2,ymax=Math.max(.0001,...points.map(r=>Number(r.cost_per_autonomous_success_usd)))*1.3;
  for(let i=0;i<4;i++){const v=i*ymax/3;host.append(svg('text',{x:3,y:228-i*62},v.toFixed(5)));host.append(svg('text',{x:65+i*165,y:247},(i*xmax/3).toFixed(1)));}
  points.forEach((row,i)=>{const x=65+row.median_ms/1000/xmax*495,y=225-Number(row.cost_per_autonomous_success_usd)/ymax*186;const circle=svg('circle',{cx:x,cy:y,r:12,fill:row.autonomous_rate===1?'#25382e':'#c79270',stroke:'#fffcf5','stroke-width':3,tabindex:0});circle.append(svg('title',{},`${label(row.model)}: ${row.autonomous}/${row.completed} autonomous, ${seconds(row.median_ms)}, ${money(row.cost_per_autonomous_success_usd)}/success`));host.append(circle,svg('text',{x:Math.min(x+16,455),y:y+(i%2?22:-17)},label(row.model)));});
  if(!points.length)host.append(svg('text',{x:185,y:130},'Verified runs make the picture.'));
  $('chart-count').textContent=`${points.length} profile(s) · ${evidence==='real'?'real evidence':'synthetic evidence'}`;
}
async function refresh() {
  if(refreshing)return;
  refreshing=true;
  try {
    const [health,runs,rows,configuration,choices,batches]=await Promise.all(['/api/health','/api/runs','/api/kpis','/api/catalog','/api/recommendations?objective='+$('objective').value+'&runtime='+$('runtime').value,'/api/campaigns'].map(url=>fetch(url).then(r=>r.json())));
    catalog=configuration;recommendations=choices;campaigns=batches;syncTasks();
    busy=campaigns.some(c=>c.status==='running')||runs.some(r=>r.status==='running'||r.postprocessing||r.memory?.status==='pending');
    $('limit').replaceChildren(document.createTextNode(pretty(health.limit)+' '),el('small','tokens'));
    $('metric').textContent=health.metric==='active_context'?'Active input context · cache included':'Cumulative input per agent';
    const tier=health.ready?.[$('runtime').value];
    $('live').disabled=busy||!tier?.live;$('simulate').disabled=busy||!tier?.simulation;$('tour').disabled=busy||!tier?.simulation;$('benchmark').disabled=busy||!health.live_ready;
    $('sandbox-status').textContent=health.sandbox_ready?'OpenShell qualified · NVIDIA telemetry disabled':'OpenShell unavailable or qualification expired · execution blocked';
    const batch=campaigns[0];$('campaign-status').textContent=batch?`${batch.status} · ${batch.run_ids.length}/${batch.planned} runs · ${money(batch.native_cost_estimate_usd)} native estimate`:'';
    const next=JSON.stringify([runs,rows,evidence,choices,$('runtime').value,$('scenario').value]);cachedRuns=runs;cachedRows=rows;if(next!==signature){signature=next;render();}
  } catch {$('message').textContent='Observer temporarily unavailable.';} finally {refreshing=false;}
}
async function integrations(){try{const states=await fetch('/api/integrations').then(r=>r.json());let connected=0;document.querySelectorAll('[data-service]').forEach(e=>{const good=states[e.dataset.service]==='connected';e.classList.toggle('connected',good);e.title=good?'Connected':'Unavailable';if(good)connected++;});$('system-dot').classList.toggle('connected',connected===4);$('system-status').textContent=`${connected}/4 tools connected`;}catch{$('system-status').textContent='Checking services';}}
async function post(payload){$('message').textContent='';try{const r=await fetch('/api/runs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const result=await r.json();if(!r.ok)$('message').textContent=result.error;}catch{$('message').textContent='Unable to submit request.';}await refresh();}
async function start(mode){setFilter(mode==='simulation'?'synthetic':'real');await post({mode,profile:$('profile').value,task_id:$('scenario').value,objective:$('objective').value,runtime:$('runtime').value});}
$('benchmark').onclick=()=>post({mode:'benchmark'});$('scenario').onchange=()=>{render();$('recalled').replaceChildren(el('p','Recall analyses for the selected bank.','muted'));};$('objective').onchange=refresh;$('runtime').onchange=()=>{syncTasks();refresh();};
$('simulate').onclick=()=>start('simulation');$('live').onclick=()=>start('live');$('tour').onclick=async()=>{document.getElementById('sessions').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});await start('simulation');};
document.querySelectorAll('[data-filter]').forEach(b=>b.onclick=()=>setFilter(b.dataset.filter));
$('recall').onclick=async()=>{const button=$('recall');button.disabled=true;$('recalled').replaceChildren(el('p','Recalling retained analyses…','muted'));try{const r=await fetch('/api/memory'+(evidence==='synthetic'?'?synthetic=true':''));const result=await r.json();$('recalled').replaceChildren();for(const item of result.results??[]){const e=el('div','','memory-item');let text=item.text;try{const a=JSON.parse(item.text);text=a.schema==='aeion.model-decision.v1'?`Task-specific decisions: ${Object.values(a.recommendations??{}).map(r=>`${r.task_id}: ${label(r.model)} (${r.basis})`).join('; ')}`:`${a.task??'Task'} · ${label(a.model)} · ${a.status} · ${a.input_tokens} input tokens · ${seconds(a.duration_ms)} · ${a.human_interventions} human intervention(s). ${a.assessment}`;}catch{}e.append(el('strong',evidence==='real'?'Recalled real-session evidence':'Recalled synthetic-session evidence'),el('span',text));$('recalled').append(e);}if(!$('recalled').children.length)$('recalled').append(el('p',result.status==='ok'?'No retained analyses in this bank yet.':'Memory backend unavailable.','muted'));}catch{$('recalled').replaceChildren(el('p','Memory backend unavailable.','muted'));}finally{button.disabled=false;}};
refresh();integrations();setInterval(refresh,1500);setInterval(integrations,20000);
