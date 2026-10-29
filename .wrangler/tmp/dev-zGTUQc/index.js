var __defProp = Object.defineProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });

// .wrangler/tmp/bundle-ef3f0P/strip-cf-connecting-ip-header.js
function stripCfConnectingIPHeader(input, init) {
  const request = new Request(input, init);
  request.headers.delete("CF-Connecting-IP");
  return request;
}
__name(stripCfConnectingIPHeader, "stripCfConnectingIPHeader");
globalThis.fetch = new Proxy(globalThis.fetch, {
  apply(target, thisArg, argArray) {
    return Reflect.apply(target, thisArg, [
      stripCfConnectingIPHeader.apply(null, argArray)
    ]);
  }
});

// worker/index.js
var STEPS = /* @__PURE__ */ new Set(["view", "calc_seen", "active", "explore", "start_seen", "faq", "bottom", "feedback"]);
var LANGS = /* @__PURE__ */ new Set(["en", "it", "es"]);
var MAX_COMMENT = 1e3;
var MAX_FEEDBACK_PER_VISITOR_PER_DAY = 10;
var schemaReady = false;
var saltCache = { day: null, salt: null };
async function ensureSchema(db) {
  if (schemaReady) return;
  await db.batch([
    db.prepare(`CREATE TABLE IF NOT EXISTS events (
      day TEXT NOT NULL, step TEXT NOT NULL, vid TEXT NOT NULL,
      lang TEXT, device TEXT, source TEXT, country TEXT,
      PRIMARY KEY (day, step, vid))`),
    db.prepare(`CREATE TABLE IF NOT EXISTS feedback (
      id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, day TEXT NOT NULL, vid TEXT NOT NULL,
      lang TEXT, place TEXT, vote INTEGER, comment TEXT, device TEXT, country TEXT)`),
    db.prepare(`CREATE TABLE IF NOT EXISTS salts (day TEXT PRIMARY KEY, salt TEXT NOT NULL)`)
  ]);
  schemaReady = true;
}
__name(ensureSchema, "ensureSchema");
async function saltFor(db, day) {
  if (saltCache.day === day) return saltCache.salt;
  const fresh = [...crypto.getRandomValues(new Uint8Array(16))].map((b) => b.toString(16).padStart(2, "0")).join("");
  await db.prepare("INSERT OR IGNORE INTO salts (day, salt) VALUES (?, ?)").bind(day, fresh).run();
  const row = await db.prepare("SELECT salt FROM salts WHERE day = ?").bind(day).first();
  await db.prepare("DELETE FROM salts WHERE day < ?").bind(day).run();
  saltCache.day = day;
  saltCache.salt = row.salt;
  return row.salt;
}
__name(saltFor, "saltFor");
async function visitorId(db, request, day) {
  const salt = await saltFor(db, day);
  const ip = request.headers.get("cf-connecting-ip") || "";
  const ua = request.headers.get("user-agent") || "";
  const data = new TextEncoder().encode(`${salt}|${ip}|${ua}`);
  const hash = await crypto.subtle.digest("SHA-256", data);
  return [...new Uint8Array(hash)].slice(0, 12).map((b) => b.toString(16).padStart(2, "0")).join("");
}
__name(visitorId, "visitorId");
function deviceOf(request) {
  const ua = request.headers.get("user-agent") || "";
  return /Mobi|Android|iPhone|iPad/i.test(ua) ? "mobile" : "desktop";
}
__name(deviceOf, "deviceOf");
function isBot(request) {
  const ua = request.headers.get("user-agent") || "";
  return !ua || /bot|crawl|spider|slurp|headless|lighthouse|preview|facebookexternalhit|whatsapp/i.test(ua);
}
__name(isBot, "isBot");
function clean(value, max) {
  return typeof value === "string" ? value.trim().slice(0, max) : null;
}
__name(clean, "clean");
async function readJson(request) {
  const text = await request.text();
  if (text.length > 4e3) return null;
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}
__name(readJson, "readJson");
var noContent = /* @__PURE__ */ __name(() => new Response(null, { status: 204, headers: { "cache-control": "no-store" } }), "noContent");
var worker_default = {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (!url.pathname.startsWith("/api/")) return env.ASSETS.fetch(request);
    if (request.method !== "POST") return new Response("Method not allowed", { status: 405 });
    const origin = request.headers.get("origin") || "";
    if (origin && !/^https:\/\/(www\.)?youretfplan\.com$|\.workers\.dev$|^http:\/\/localhost(:\d+)?$/.test(origin)) {
      return new Response("Forbidden", { status: 403 });
    }
    if (isBot(request)) return noContent();
    const body = await readJson(request);
    if (!body) return new Response("Bad request", { status: 400 });
    const db = env.DB;
    await ensureSchema(db);
    const day = (/* @__PURE__ */ new Date()).toISOString().slice(0, 10);
    const vid = await visitorId(db, request, day);
    const lang = LANGS.has(body.lang) ? body.lang : null;
    const device = deviceOf(request);
    const country = request.cf && request.cf.country || null;
    if (url.pathname === "/api/e") {
      const steps = Array.isArray(body.steps) ? body.steps.filter((s) => STEPS.has(s)).slice(0, STEPS.size) : [];
      const source = clean(body.source, 80);
      if (!steps.length) return noContent();
      await db.batch(steps.map((step) => db.prepare("INSERT OR IGNORE INTO events (day, step, vid, lang, device, source, country) VALUES (?, ?, ?, ?, ?, ?, ?)").bind(day, step, vid, lang, device, source, country)));
      return noContent();
    }
    if (url.pathname === "/api/f") {
      if (body.website) return noContent();
      const vote = body.vote === 1 || body.vote === -1 ? body.vote : null;
      const comment = clean(body.comment, MAX_COMMENT) || null;
      const place = ["result", "result_comment", "bottom"].includes(body.place) ? body.place : null;
      if (vote === null && !comment) return new Response("Empty", { status: 400 });
      const { n } = await db.prepare("SELECT COUNT(*) AS n FROM feedback WHERE day = ? AND vid = ?").bind(day, vid).first();
      if (n >= MAX_FEEDBACK_PER_VISITOR_PER_DAY) return noContent();
      await db.batch([
        db.prepare("INSERT INTO feedback (ts, day, vid, lang, place, vote, comment, device, country) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)").bind((/* @__PURE__ */ new Date()).toISOString(), day, vid, lang, place, vote, comment, device, country),
        db.prepare("INSERT OR IGNORE INTO events (day, step, vid, lang, device, source, country) VALUES (?, ?, ?, ?, ?, ?, ?)").bind(day, "feedback", vid, lang, device, null, country)
      ]);
      return noContent();
    }
    return new Response("Not found", { status: 404 });
  }
};

// ../../../tmp/claude-0/-home-claude/932b4fc8-fe06-54d3-86f6-f4a5f9f43e4c/scratchpad/wr/node_modules/wrangler/templates/middleware/middleware-ensure-req-body-drained.ts
var drainBody = /* @__PURE__ */ __name(async (request, env, _ctx, middlewareCtx) => {
  try {
    return await middlewareCtx.next(request, env);
  } finally {
    try {
      if (request.body !== null && !request.bodyUsed) {
        const reader = request.body.getReader();
        while (!(await reader.read()).done) {
        }
      }
    } catch (e) {
      console.error("Failed to drain the unused request body.", e);
    }
  }
}, "drainBody");
var middleware_ensure_req_body_drained_default = drainBody;

// ../../../tmp/claude-0/-home-claude/932b4fc8-fe06-54d3-86f6-f4a5f9f43e4c/scratchpad/wr/node_modules/wrangler/templates/middleware/middleware-miniflare3-json-error.ts
function reduceError(e) {
  return {
    name: e?.name,
    message: e?.message ?? String(e),
    stack: e?.stack,
    cause: e?.cause === void 0 ? void 0 : reduceError(e.cause)
  };
}
__name(reduceError, "reduceError");
var jsonError = /* @__PURE__ */ __name(async (request, env, _ctx, middlewareCtx) => {
  try {
    return await middlewareCtx.next(request, env);
  } catch (e) {
    const error = reduceError(e);
    return Response.json(error, {
      status: 500,
      headers: { "MF-Experimental-Error-Stack": "true" }
    });
  }
}, "jsonError");
var middleware_miniflare3_json_error_default = jsonError;

// .wrangler/tmp/bundle-ef3f0P/middleware-insertion-facade.js
var __INTERNAL_WRANGLER_MIDDLEWARE__ = [
  middleware_ensure_req_body_drained_default,
  middleware_miniflare3_json_error_default
];
var middleware_insertion_facade_default = worker_default;

// ../../../tmp/claude-0/-home-claude/932b4fc8-fe06-54d3-86f6-f4a5f9f43e4c/scratchpad/wr/node_modules/wrangler/templates/middleware/common.ts
var __facade_middleware__ = [];
function __facade_register__(...args) {
  __facade_middleware__.push(...args.flat());
}
__name(__facade_register__, "__facade_register__");
function __facade_invokeChain__(request, env, ctx, dispatch, middlewareChain) {
  const [head, ...tail] = middlewareChain;
  const middlewareCtx = {
    dispatch,
    next(newRequest, newEnv) {
      return __facade_invokeChain__(newRequest, newEnv, ctx, dispatch, tail);
    }
  };
  return head(request, env, ctx, middlewareCtx);
}
__name(__facade_invokeChain__, "__facade_invokeChain__");
function __facade_invoke__(request, env, ctx, dispatch, finalMiddleware) {
  return __facade_invokeChain__(request, env, ctx, dispatch, [
    ...__facade_middleware__,
    finalMiddleware
  ]);
}
__name(__facade_invoke__, "__facade_invoke__");

// .wrangler/tmp/bundle-ef3f0P/middleware-loader.entry.ts
var __Facade_ScheduledController__ = class ___Facade_ScheduledController__ {
  constructor(scheduledTime, cron, noRetry) {
    this.scheduledTime = scheduledTime;
    this.cron = cron;
    this.#noRetry = noRetry;
  }
  static {
    __name(this, "__Facade_ScheduledController__");
  }
  #noRetry;
  noRetry() {
    if (!(this instanceof ___Facade_ScheduledController__)) {
      throw new TypeError("Illegal invocation");
    }
    this.#noRetry();
  }
};
function wrapExportedHandler(worker) {
  if (__INTERNAL_WRANGLER_MIDDLEWARE__ === void 0 || __INTERNAL_WRANGLER_MIDDLEWARE__.length === 0) {
    return worker;
  }
  for (const middleware of __INTERNAL_WRANGLER_MIDDLEWARE__) {
    __facade_register__(middleware);
  }
  const fetchDispatcher = /* @__PURE__ */ __name(function(request, env, ctx) {
    if (worker.fetch === void 0) {
      throw new Error("Handler does not export a fetch() function.");
    }
    return worker.fetch(request, env, ctx);
  }, "fetchDispatcher");
  return {
    ...worker,
    fetch(request, env, ctx) {
      const dispatcher = /* @__PURE__ */ __name(function(type, init) {
        if (type === "scheduled" && worker.scheduled !== void 0) {
          const controller = new __Facade_ScheduledController__(
            Date.now(),
            init.cron ?? "",
            () => {
            }
          );
          return worker.scheduled(controller, env, ctx);
        }
      }, "dispatcher");
      return __facade_invoke__(request, env, ctx, dispatcher, fetchDispatcher);
    }
  };
}
__name(wrapExportedHandler, "wrapExportedHandler");
function wrapWorkerEntrypoint(klass) {
  if (__INTERNAL_WRANGLER_MIDDLEWARE__ === void 0 || __INTERNAL_WRANGLER_MIDDLEWARE__.length === 0) {
    return klass;
  }
  for (const middleware of __INTERNAL_WRANGLER_MIDDLEWARE__) {
    __facade_register__(middleware);
  }
  return class extends klass {
    #fetchDispatcher = /* @__PURE__ */ __name((request, env, ctx) => {
      this.env = env;
      this.ctx = ctx;
      if (super.fetch === void 0) {
        throw new Error("Entrypoint class does not define a fetch() function.");
      }
      return super.fetch(request);
    }, "#fetchDispatcher");
    #dispatcher = /* @__PURE__ */ __name((type, init) => {
      if (type === "scheduled" && super.scheduled !== void 0) {
        const controller = new __Facade_ScheduledController__(
          Date.now(),
          init.cron ?? "",
          () => {
          }
        );
        return super.scheduled(controller);
      }
    }, "#dispatcher");
    fetch(request) {
      return __facade_invoke__(
        request,
        this.env,
        this.ctx,
        this.#dispatcher,
        this.#fetchDispatcher
      );
    }
  };
}
__name(wrapWorkerEntrypoint, "wrapWorkerEntrypoint");
var WRAPPED_ENTRY;
if (typeof middleware_insertion_facade_default === "object") {
  WRAPPED_ENTRY = wrapExportedHandler(middleware_insertion_facade_default);
} else if (typeof middleware_insertion_facade_default === "function") {
  WRAPPED_ENTRY = wrapWorkerEntrypoint(middleware_insertion_facade_default);
}
var middleware_loader_entry_default = WRAPPED_ENTRY;
export {
  __INTERNAL_WRANGLER_MIDDLEWARE__,
  middleware_loader_entry_default as default
};
//# sourceMappingURL=index.js.map
