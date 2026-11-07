// LIVE data: fetched from the published research snapshot (data/live.json). Nothing here is sample data.
const res = await fetch('./data/live.json?t=' + Math.floor(Date.now() / 60000), { cache: 'no-store' });
export const LIVE = await res.json();
export const META = { updated_label: LIVE.updated_label, qualified: LIVE.counts.qualified };
export const agents = LIVE.agents;
export const top10 = LIVE.top10.map(c => ({ ...c, followers: (c.followers && c.followers.display) || 'unknown', platform: c.platform }));
export const feed = (LIVE.feed.length ? LIVE.feed : [{ t: '', who: 'Floor', msg: 'No activity yet' }]).slice(0, 40);
