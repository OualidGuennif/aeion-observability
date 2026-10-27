import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, writeFileSync, existsSync, rmSync, linkSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { decision, measure } from "../gate-policy.mjs";
import { ContextGate } from "../context-gate.mjs";

const message = (id, input, read = 0, write = 0) => ({info:{id, role:"assistant", finish:"tool-calls", cost:0, tokens:{input, cache:{read,write}}}});
test("exact boundary and cached input are included without summing active contexts", () => {
  assert.equal(decision([message("a", 249999)],250000).action,"continue");
  assert.equal(decision([message("a", 10000,239999,1)],250000).action,"handover");
  assert.equal(decision([message("a",140000),message("b",140000)],250000).action,"continue");
  assert.equal(decision([message("a",140000),message("b",140000)],250000,"cumulative_input").action,"handover");
});
test("duplicates do not inflate cumulative usage", () => {
  assert.equal(decision([message("a",140000),message("a",140000)],250000,"cumulative_input").observed,140000);
});
test("missing, invalid and incomplete usage fails closed", () => {
  for(const tokens of [{}, {input:0,cache:{read:0,write:0}}, {input:-1,cache:{read:0,write:0}}, {input:NaN,cache:{read:0,write:0}}]) assert.throws(()=>measure(tokens));
  assert.throws(()=>decision([{info:{role:"assistant", id:"a"}}],250000));
  assert.throws(()=>decision([message("a",100)],250001));
  assert.throws(()=>decision([],250000,"typo"));
});
test("hook writes only a bounded decision and prevents subsequent dispatch", async () => {
  const folder=mkdtempSync(join(tmpdir(),"aeion-gate-"));
  const file=join(folder,"gate.json");
  process.env.AEION_GATE_FILE=file;process.env.AEION_CONTEXT_LIMIT="250000";process.env.AEION_CONTEXT_METRIC="active_context";
  process.env.AEION_CHECKPOINT_REQUEST=join(folder,"request.json");process.env.AEION_CHECKPOINT_ACK=join(folder,"ack.json");
  const ack=setInterval(()=>{
    if(existsSync(process.env.AEION_CHECKPOINT_REQUEST)) {
      const request=JSON.parse(readFileSync(process.env.AEION_CHECKPOINT_REQUEST));
      writeFileSync(process.env.AEION_CHECKPOINT_ACK,JSON.stringify({id:request.id,ready:true,sha256:'a'.repeat(64)}));
    }
  },10);
  try {
    const hook=await ContextGate(); let dispatched=0;
    const request=async(messages)=>{await hook["experimental.chat.messages.transform"]({}, {messages});dispatched++;};
    await request([]);assert.equal(existsSync(file),false);
    await assert.rejects(request([message("a",250000)]),/AEION_GATE_CLOSED/);
    assert.equal(dispatched,1);assert.deepEqual(JSON.parse(readFileSync(file)),{action:"handover",observed:250000,metric:"active_context",limit:250000});
    await assert.rejects(request([{info:{role:"assistant",id:"bad"}}]));
    assert.equal(JSON.parse(readFileSync(file)).reason,"USAGE_UNKNOWN");
  } finally {clearInterval(ack);rmSync(folder,{recursive:true});}
});
test("gate decisions replace the file atomically instead of rewriting it in place", async () => {
  const folder=mkdtempSync(join(tmpdir(),"aeion-atomic-"));
  const file=join(folder,"gate.json"), observer=join(folder,"observer.json");
  process.env.AEION_GATE_FILE=file;process.env.AEION_CONTEXT_LIMIT="250000";process.env.AEION_CONTEXT_METRIC="active_context";
  try {
    // A hard link sees in-place truncation; a rename leaves the previous inode intact.
    writeFileSync(observer,'{"previous":true}');linkSync(observer,file);
    const hook=await ContextGate();
    await assert.rejects(hook["experimental.chat.messages.transform"]({}, {messages:[{info:{role:"assistant",id:"bad"}}]}),/AEION_GATE_CLOSED/);
    assert.equal(readFileSync(observer,"utf8"),'{"previous":true}');
    assert.deepEqual(JSON.parse(readFileSync(file)),{action:"stop",reason:"USAGE_UNKNOWN"});
    assert.equal(existsSync(file+".tmp"),false);
  } finally {rmSync(folder,{recursive:true});}
});
test("output is capped to 4096 without raising a smaller model ceiling", async()=>{
  const hooks=await ContextGate();
  for(const [initial,expected] of [[undefined,4096],[1000,1000],[8000,4096]]) {
    const output={maxOutputTokens:initial};await hooks["chat.params"]({},output);assert.equal(output.maxOutputTokens,expected);
  }
});
test("real credentials require a single admitted build request", async()=>{
  process.env.AEION_OPENCODE_KEY="synthetic-test-key";
  const hooks=await ContextGate();const headers={};
  await assert.rejects(hooks["chat.headers"]({agent:"build"},{headers}));
  await hooks["experimental.chat.messages.transform"]({}, {messages:[]});
  await hooks["chat.headers"]({agent:"build"},{headers});
  assert.equal(headers.Authorization,"Bearer synthetic-test-key");
  await assert.rejects(hooks["chat.headers"]({agent:"build"},{headers:{}}));
  await hooks["experimental.chat.messages.transform"]({}, {messages:[]});
  await assert.rejects(hooks["chat.headers"]({agent:"summary"},{headers:{}}));
});
test("missing or stale Markdown acknowledgement never releases model admission", async(t)=>{
  const folder=mkdtempSync(join(tmpdir(),"aeion-no-ack-"));
  process.env.AEION_GATE_FILE=join(folder,"gate.json");
  process.env.AEION_CHECKPOINT_REQUEST=join(folder,"request.json");
  process.env.AEION_CHECKPOINT_ACK=join(folder,"ack.json");
  process.env.AEION_CONTEXT_LIMIT="250000";process.env.AEION_CONTEXT_METRIC="active_context";
  let calls=0;t.mock.method(Date,'now',()=>calls++<2?0:20001);
  try{
    for(const stale of [false,true]) {
      calls=0;
      if(stale) writeFileSync(process.env.AEION_CHECKPOINT_ACK,JSON.stringify({id:'old-request',ready:true,sha256:'a'.repeat(64)}));
      const hooks=await ContextGate();
      await assert.rejects(hooks['experimental.chat.messages.transform']({}, {messages:[message('a',250000)]}),/AEION_GATE_CLOSED/);
      assert.equal(JSON.parse(readFileSync(process.env.AEION_GATE_FILE)).reason,'HANDOVER_NOT_READY');
      await assert.rejects(hooks['chat.headers']({agent:'build'},{headers:{}}),/AEION_GATE_CLOSED/);
    }
  }finally{rmSync(folder,{recursive:true});}
});
