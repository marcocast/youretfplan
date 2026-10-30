// youretfplan.com API: anonymous usage events and feedback, stored in D1.
// Static pages are served from ./public by Workers static assets; only requests that do
// not match a file (here /api/*) reach this script.
//
// Privacy: no cookies, no IP stored. A visitor is identified only by a hash of
// (random salt of the day + IP + user agent). The salt is replaced every day and old
// salts are deleted, so visitors cannot be linked across days or traced back.

const STEPS = new Set(['view', 'hook', 'plan', 'calc_seen', 'active', 'explore', 'start_seen', 'faq', 'bottom', 'feedback']);
// Scenario pages (bank vs ETF, ...): sc_<scenario>_view and sc_<scenario>_active.
const SCENARIO_STEP = /^sc_(bank|buy|inherit|own)_(view|active)$/;
const isStep = s => STEPS.has(s) || SCENARIO_STEP.test(s);
const LANGS = new Set(['en', 'it', 'es']);
const MAX_COMMENT = 1000;
const MAX_FEEDBACK_PER_VISITOR_PER_DAY = 10;

let schemaReady = false;
const saltCache = { day: null, salt: null };

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
    db.prepare(`CREATE TABLE IF NOT EXISTS salts (day TEXT PRIMARY KEY, salt TEXT NOT NULL)`),
  ]);
  schemaReady = true;
}

async function saltFor(db, day) {
  if (saltCache.day === day) return saltCache.salt;
  const fresh = [...crypto.getRandomValues(new Uint8Array(16))].map(b => b.toString(16).padStart(2, '0')).join('');
  await db.prepare('INSERT OR IGNORE INTO salts (day, salt) VALUES (?, ?)').bind(day, fresh).run();
  const row = await db.prepare('SELECT salt FROM salts WHERE day = ?').bind(day).first();
  await db.prepare('DELETE FROM salts WHERE day < ?').bind(day).run();
  saltCache.day = day;
  saltCache.salt = row.salt;
  return row.salt;
}

async function visitorId(db, request, day) {
  const salt = await saltFor(db, day);
  const ip = request.headers.get('cf-connecting-ip') || '';
  const ua = request.headers.get('user-agent') || '';
  const data = new TextEncoder().encode(`${salt}|${ip}|${ua}`);
  const hash = await crypto.subtle.digest('SHA-256', data);
  return [...new Uint8Array(hash)].slice(0, 12).map(b => b.toString(16).padStart(2, '0')).join('');
}

function deviceOf(request) {
  const ua = request.headers.get('user-agent') || '';
  return /Mobi|Android|iPhone|iPad/i.test(ua) ? 'mobile' : 'desktop';
}

function isBot(request) {
  const ua = request.headers.get('user-agent') || '';
  return !ua || /bot|crawl|spider|slurp|headless|lighthouse|preview|facebookexternalhit|whatsapp/i.test(ua);
}

function clean(value, max) {
  return typeof value === 'string' ? value.trim().slice(0, max) : null;
}

async function readJson(request) {
  // sendBeacon sends text/plain, so parse the body ourselves.
  const text = await request.text();
  if (text.length > 4000) return null;
  try { return JSON.parse(text); } catch { return null; }
}

const noContent = () => new Response(null, { status: 204, headers: { 'cache-control': 'no-store' } });

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (!url.pathname.startsWith('/api/')) return env.ASSETS.fetch(request);
    if (request.method !== 'POST') return new Response('Method not allowed', { status: 405 });

    // Only accept calls from our own pages.
    const origin = request.headers.get('origin') || '';
    if (origin && !/^https:\/\/(www\.)?youretfplan\.com$|\.workers\.dev$|^http:\/\/localhost(:\d+)?$/.test(origin)) {
      return new Response('Forbidden', { status: 403 });
    }
    if (isBot(request)) return noContent();

    const body = await readJson(request);
    if (!body) return new Response('Bad request', { status: 400 });

    const db = env.DB;
    await ensureSchema(db);
    const day = new Date().toISOString().slice(0, 10);
    const vid = await visitorId(db, request, day);
    const lang = LANGS.has(body.lang) ? body.lang : null;
    const device = deviceOf(request);
    const country = (request.cf && request.cf.country) || null;

    if (url.pathname === '/api/e') {
      const steps = Array.isArray(body.steps) ? body.steps.filter(s => typeof s === 'string' && isStep(s)).slice(0, 12) : [];
      const source = clean(body.source, 80);
      if (!steps.length) return noContent();
      await db.batch(steps.map(step =>
        db.prepare('INSERT OR IGNORE INTO events (day, step, vid, lang, device, source, country) VALUES (?, ?, ?, ?, ?, ?, ?)')
          .bind(day, step, vid, lang, device, source, country)));
      return noContent();
    }

    if (url.pathname === '/api/f') {
      if (body.website) return noContent(); // honeypot field filled in: a bot
      const vote = body.vote === 1 || body.vote === -1 ? body.vote : null;
      const comment = clean(body.comment, MAX_COMMENT) || null;
      const place = ['result', 'result_comment', 'bottom'].includes(body.place) || /^sc_(bank|buy|inherit|own)$/.test(body.place || '') ? body.place : null;
      if (vote === null && !comment) return new Response('Empty', { status: 400 });
      const { n } = await db.prepare('SELECT COUNT(*) AS n FROM feedback WHERE day = ? AND vid = ?').bind(day, vid).first();
      if (n >= MAX_FEEDBACK_PER_VISITOR_PER_DAY) return noContent();
      await db.batch([
        db.prepare('INSERT INTO feedback (ts, day, vid, lang, place, vote, comment, device, country) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)')
          .bind(new Date().toISOString(), day, vid, lang, place, vote, comment, device, country),
        db.prepare('INSERT OR IGNORE INTO events (day, step, vid, lang, device, source, country) VALUES (?, ?, ?, ?, ?, ?, ?)')
          .bind(day, 'feedback', vid, lang, device, null, country),
      ]);
      return noContent();
    }

    return new Response('Not found', { status: 404 });
  },
};
