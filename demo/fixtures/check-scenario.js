// Protected task cases arrive on stdin from the supervisor, so expected results never sit in
// the agent's image or workspace. Workload has no environment/network/subprocess permissions.
const scenario = JSON.parse(await new Response(Deno.stdin.readable).text());
if (typeof scenario?.export !== 'string' || !Array.isArray(scenario.cases)) throw new Error('invalid scenario');
let fn;
try { fn = (await import(`file://${Deno.args[0]}`))[scenario.export]; } catch { /* report failure */ }
const failed = [];
for (const item of scenario.cases) {
  let success = false;
  const args = structuredClone(item.args), before = JSON.stringify(args);
  // An unloadable or missing export must not satisfy cases that expect a TypeError.
  if (typeof fn === 'function') try {
    const value = fn(...args);
    success = !item.throws && JSON.stringify(value) === JSON.stringify(item.expected) && JSON.stringify(args) === before;
  } catch (error) { success = item.throws === 'TypeError' && error instanceof TypeError; }
  if (!success) failed.push(item.name);
}
console.log(JSON.stringify({passed:scenario.cases.length-failed.length,failed,total:scenario.cases.length}));
Deno.exit(failed.length ? 1 : 0);
