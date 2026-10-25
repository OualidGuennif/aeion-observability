import { Hono } from "hono";
import { bodyLimit } from "npm:hono@4.10.2/body-limit";

const app = new Hono();
app.use("/api/*", bodyLimit({maxSize: 4096, onError: (c) => c.json({error: "body_too_large"}, 413)}));
const page = await Deno.readTextFile(new URL("./pages/index.html", import.meta.url));
app.get("/", (c) => c.html(page));
app.get("/health", (c) => c.json({status: "ok", runtime: "deno", framework: "hono"}));
app.post("/api/quote", async (c) => {
  try {
    const body = await c.req.json();
    if (!Array.isArray(body.items) || body.items.length > 20) return c.json({error: "invalid_items"}, 400);
    // Only the supervisor publishes this fixed file, after independent checks pass.
    const source = await Deno.readTextFile("/work/published/pricing.js");
    const { totalCents } = await import(`data:text/javascript,${encodeURIComponent(source)}`);
    const total = totalCents(body.items, body.shippingCents ?? 0);
    return c.json({totalCents: total, currency: "EUR"});
  } catch (error) {
    const invalid = error instanceof TypeError || error instanceof SyntaxError;
    return c.json({error: invalid ? "invalid_quote" : "artifact_not_ready"}, invalid ? 400 : 503);
  }
});
app.onError((_error, c) => c.json({error: "request_failed"}, 500));
Deno.serve({hostname: "0.0.0.0", port: 8000, onListen() {}}, app.fetch);
