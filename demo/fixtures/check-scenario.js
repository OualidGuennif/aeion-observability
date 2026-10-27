// Protected task cases. Workload has no environment/network/subprocess permissions.
const catalogue = JSON.parse(await Deno.readTextFile('/opt/demo/fixtures/scenarios.json'));
const scenario = catalogue[Deno.args[1]];
if (!scenario) throw new Error('unknown scenario');
let fn;
try { fn = (await import(`file://${Deno.args[0]}`))[scenario.export]; } catch { /* report failure */ }
const failed = [];
for (const item of scenario.cases) {
  let success = false;
  const args = structuredClone(item.args), before = JSON.stringify(args);
  try {
    const value = fn(...args);
    success = !item.throws && JSON.stringify(value) === JSON.stringify(item.expected) && JSON.stringify(args) === before;
  } catch (error) { success = item.throws === 'TypeError' && error instanceof TypeError; }
  if (!success) failed.push(item.name);
}
console.log(JSON.stringify({passed:scenario.cases.length-failed.length,failed,total:scenario.cases.length}));
Deno.exit(failed.length ? 1 : 0);
