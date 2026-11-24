import assert from "node:assert/strict";
import { afterEach, test } from "node:test";
import { api } from "../src/api.js";

const originalFetch = globalThis.fetch;
afterEach(() => { globalThis.fetch = originalFetch; delete globalThis.window; });

test("returns a successful JSON response", async () => {
  globalThis.fetch = async () => Response.json({ items: [] });
  assert.deepEqual(await api("/equipment"), { items: [] });
});

test("malformed successful JSON rejects instead of returning null", async () => {
  globalThis.fetch = async () => new Response("truncated", { status: 200 });
  await assert.rejects(api("/dashboard"), /response.*try again/i);
});

test("body timeout after successful headers remains a retryable error", async () => {
  globalThis.fetch = async () => ({ ok: true, json: async () => { throw new DOMException("timeout", "TimeoutError"); } });
  await assert.rejects(api("/dashboard"), /took too long/i);
});

test("caller cancellation while reading the body is preserved", async () => {
  const controller = new AbortController();
  const cancellation = new DOMException("cancelled", "AbortError");
  globalThis.fetch = async () => ({ ok: true, json: async () => { controller.abort(); throw cancellation; } });
  await assert.rejects(api("/equipment", controller.signal), error => error === cancellation);
});

test("network timeout before headers gives an actionable error", async () => {
  globalThis.fetch = async () => { throw new DOMException("timeout", "TimeoutError"); };
  await assert.rejects(api("/equipment"), /took too long/i);
});

test("a body-read AbortError from the timeout gives a retryable error", async () => {
  globalThis.fetch = async () => ({ ok: true, json: async () => { throw new DOMException("timeout", "AbortError"); } });
  await assert.rejects(api("/dashboard"), /took too long/i);
});

test("HTTP errors preserve status even when their body cannot be parsed", async () => {
  globalThis.fetch = async () => new Response("gateway unavailable", { status: 503 });
  await assert.rejects(api("/equipment"), error => error.status === 503);
});

test("protected-resource 401 expires the session", async () => {
  globalThis.window = new EventTarget();
  let expired = 0;
  window.addEventListener("equiptrack:session-expired", () => expired++);
  globalThis.fetch = async () => Response.json({ error: { message: "Sign in again." } }, { status: 401 });
  await assert.rejects(api("/dashboard"), error => error.status === 401 && /Sign in/.test(error.message));
  assert.equal(expired, 1);
});

test("an invalid login does not expire an unrelated session", async () => {
  globalThis.window = new EventTarget();
  let expired = 0;
  window.addEventListener("equiptrack:session-expired", () => expired++);
  globalThis.fetch = async () => Response.json({ error: { message: "Invalid login." } }, { status: 401 });
  await assert.rejects(api("/auth/login"), error => error.status === 401);
  assert.equal(expired, 0);
});

test("malformed 401 responses still expire the session", async () => {
  globalThis.window = new EventTarget();
  let expired = 0;
  window.addEventListener("equiptrack:session-expired", () => expired++);
  globalThis.fetch = async () => new Response("broken gateway response", { status: 401 });
  await assert.rejects(api("/dashboard"), error => error.status === 401);
  assert.equal(expired, 1);
});
