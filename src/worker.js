// API for tzarichkfar.com: anonymous "I was there" feedback and "I'm coming" counters.
// Storage: D1. No names, no contact details, no IP addresses are stored.
const ALL = ['אהבנו מאוד', 'היה בסדר', 'פחות התאים לנו'];
const AGES = ['לידה עד זחילה', 'זחילה עד שנה', 'שנה עד שנתיים', 'שנתיים עד שלוש', 'שלוש עד ארבע', 'ארבע עד שש'];
const GOOD = ['מוצל', 'נקי ומסודר', 'נוח עם עגלה', 'פינת החתלה', 'חניה נוחה', 'צוות נעים', 'מתאים לזוחלים', 'מדריכה מקסימה', 'מתאים לגיל', 'אווירה נעימה', 'הכרתי אמהות', 'שווה את המחיר'];
const NOTE = ['צפוף בשעות העומס', 'חניה קשה', 'להביא שמיכה', 'פחות נוח עם עגלה', 'צפוף', 'כדאי להירשם מראש'];
const MAX_PER_HOUR = 400;

let ready = false;
let names = null;
let cache = null;
let cacheAt = 0;
let cleanedAt = 0;

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' },
  });
}

async function init(env) {
  if (ready) return;
  await env.DB.batch([
    env.DB.prepare('CREATE TABLE IF NOT EXISTS fb (item TEXT NOT NULL, kind TEXT, overall TEXT, ages TEXT, good TEXT, note TEXT, cid TEXT NOT NULL, ts INTEGER NOT NULL, PRIMARY KEY (item, cid))'),
    env.DB.prepare('CREATE TABLE IF NOT EXISTS go (k TEXT NOT NULL, cid TEXT NOT NULL, ts INTEGER NOT NULL, PRIMARY KEY (k, cid))'),
  ]);
  // one-time wipe of pre-launch test data
  await env.DB.prepare('CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY)').run();
  const flag = await env.DB.prepare("SELECT k FROM meta WHERE k = 'reset2'").first();
  if (!flag) {
    await env.DB.batch([
      env.DB.prepare('DELETE FROM fb'),
      env.DB.prepare('DELETE FROM go'),
      env.DB.prepare("INSERT OR IGNORE INTO meta (k) VALUES ('reset2')"),
    ]);
  }
  ready = true;
}

// Names that exist on the site, read from the published page, so junk items are rejected.
async function siteNames(env, request) {
  if (names) return names;
  const res = await env.ASSETS.fetch(new Request(new URL('/index.html', request.url)));
  const html = await res.text();
  const set = new Set();
  const re = /<(?:span class="name"|div class="c-name")>([^<]+)</g;
  let m;
  while ((m = re.exec(html))) {
    const t = m[1].trim();
    set.add(t);
    set.add(t.split(' – ')[0]);
  }
  if (set.size) names = set;
  return set;
}

function pick(list, allowed, max) {
  if (!Array.isArray(list)) return [];
  const out = [];
  for (const v of list) if (typeof v === 'string' && allowed.includes(v) && !out.includes(v)) out.push(v);
  return out.slice(0, max);
}

async function summary(env) {
  const now = Date.now();
  if (cache && now - cacheAt < 4000) return cache;
  const [fbRows, goRows] = await env.DB.batch([
    env.DB.prepare('SELECT item, overall, ages, good, note FROM fb'),
    env.DB.prepare('SELECT k, COUNT(*) AS n FROM go GROUP BY k'),
  ]);
  const fb = {};
  for (const r of fbRows.results) {
    const o = fb[r.item] || (fb[r.item] = { n: 0, t: {} });
    o.n++;
    const tags = [];
    if (r.overall) tags.push(r.overall);
    for (const col of [r.ages, r.good, r.note]) if (col) for (const v of JSON.parse(col)) tags.push(v);
    for (const v of tags) o.t[v] = (o.t[v] || 0) + 1;
  }
  const go = {};
  for (const r of goRows.results) go[r.k] = r.n;
  cache = { fb, go };
  cacheAt = now;
  return cache;
}

async function body(request) {
  const text = await request.text();
  if (text.length > 4000) return null;
  try { return JSON.parse(text); } catch (e) { return null; }
}

const okCid = (c) => typeof c === 'string' && /^[a-z0-9-]{12,40}$/.test(c);

async function api(request, env) {
  const url = new URL(request.url);
  await init(env);
  if (request.method === 'GET' && url.pathname === '/api/s') return json(await summary(env));
  if (request.method !== 'POST') return json({ error: 'method' }, 405);
  const origin = request.headers.get('origin');
  if (origin && origin !== url.origin) return json({ error: 'origin' }, 403);
  const b = await body(request);
  if (!b || !okCid(b.cid)) return json({ error: 'bad' }, 400);
  const known = await siteNames(env, request);
  const now = Date.now();

  if (url.pathname === '/api/fb') {
    if (typeof b.item !== 'string' || !known.has(b.item)) return json({ error: 'item' }, 400);
    const recent = await env.DB.prepare('SELECT COUNT(*) AS n FROM fb WHERE ts > ?').bind(now - 3600000).first();
    if (recent && recent.n > MAX_PER_HOUR) return json({ error: 'busy' }, 429);
    const overall = ALL.includes(b.overall) ? b.overall : null;
    await env.DB.prepare('INSERT INTO fb (item, kind, overall, ages, good, note, cid, ts) VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(item, cid) DO UPDATE SET overall=excluded.overall, ages=excluded.ages, good=excluded.good, note=excluded.note, ts=excluded.ts')
      .bind(b.item, b.kind === 'place' ? 'place' : 'act', overall, JSON.stringify(pick(b.ages, AGES, 6)), JSON.stringify(pick(b.good, GOOD, 12)), JSON.stringify(pick(b.note, NOTE, 6)), b.cid, now).run();
    cache = null;
    return json(await summary(env));
  }

  if (url.pathname === '/api/go') {
    const m = typeof b.k === 'string' && /^(\d{4}-\d{2}-\d{2})\|(.+)$/.exec(b.k);
    if (!m || b.k.length > 300 || !known.has(m[2])) return json({ error: 'item' }, 400);
    if (b.on === false) {
      await env.DB.prepare('DELETE FROM go WHERE k = ? AND cid = ?').bind(b.k, b.cid).run();
    } else {
      const recent = await env.DB.prepare('SELECT COUNT(*) AS n FROM go WHERE ts > ?').bind(now - 3600000).first();
      if (recent && recent.n > MAX_PER_HOUR) return json({ error: 'busy' }, 429);
      await env.DB.prepare('INSERT OR IGNORE INTO go (k, cid, ts) VALUES (?,?,?)').bind(b.k, b.cid, now).run();
      // housekeeping: drop attendance marks 30 days after the activity, feedback after 24 months
      if (now - cleanedAt > 86400000) {
        cleanedAt = now;
        const cutoff = new Date(now - 30 * 86400000).toISOString().slice(0, 10);
        await env.DB.batch([
          env.DB.prepare('DELETE FROM go WHERE substr(k, 1, 10) < ?').bind(cutoff),
          env.DB.prepare('DELETE FROM fb WHERE ts < ?').bind(now - 730 * 86400000),
        ]);
      }
    }
    cache = null;
    return json(await summary(env));
  }
  return json({ error: 'not found' }, 404);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname.startsWith('/api/')) {
      try { return await api(request, env); } catch (e) { return json({ error: 'server' }, 500); }
    }
    return env.ASSETS.fetch(request);
  },
};
