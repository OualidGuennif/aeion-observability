// Immutable checks: no third-party imports, network, environment or subprocess permission.
let totalCents;
try { ({totalCents} = await import(`file://${Deno.args[0]}`)); } catch { /* report all failed checks below */ }
function rejects(items, shipping = 0) {
  try { totalCents(items, shipping); } catch (error) { return error instanceof TypeError; }
  return false;
}
const cases = {
  empty: () => totalCents([]) === 0,
  sum: () => totalCents([[125, 2], [50, 3]], 75) === 475,
  zero: () => totalCents([[0, 4], [100, 0]]) === 0,
  negative_price: () => rejects([[-1, 1]]),
  negative_quantity: () => rejects([[10, -1]]),
  negative_shipping: () => rejects([], -1),
  boolean: () => rejects([[true, 1]]),
  float: () => rejects([[1.5, 1]]),
  bad_shape: () => rejects([[1]]),
  bad_shipping: () => rejects([], "10"),
  overflow: () => rejects([[Number.MAX_SAFE_INTEGER, 2]]),
  items_type: () => rejects({}),
};
const failed = typeof totalCents !== "function" ? Object.keys(cases) : Object.entries(cases).filter(([, check]) => {
  try { return !check(); } catch { return true; }
}).map(([name]) => name);
console.log(JSON.stringify({ passed: Object.keys(cases).length - failed.length, failed, total: 12 }));
Deno.exit(failed.length ? 1 : 0);
