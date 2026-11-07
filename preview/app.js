import { agents, top10, feed } from './data.js';
const $=s=>document.querySelector(s),esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const S='<b class="tag">Sample</b>';
$('#pages').innerHTML=top10.map(p=>`<article class="page glass"><div class="rank">${String(p.rank).padStart(2,'0')}</div><div class="pmain"><div class="ph"><h3>${esc(p.handle)}</h3>${S}</div><div class="meta">${esc(p.platform)} · ${esc(p.niche)}</div>
<dl><div><dt>Followers</dt><dd>${p.followers}</dd></div><div><dt>Recent views</dt><dd>${p.views}</dd></div><div><dt>Likes</dt><dd>${p.likes}</dd></div><div><dt>Revenue</dt><dd>${p.revenue}</dd></div></dl>
<p class="why">${esc(p.why)}</p><div class="chips"><span>Faceless: ${esc(p.faceless)}</span><span>Monetization: ${esc(p.monetization)}</span><span>Verifier: ${esc(p.verifier)}</span></div></div></article>`).join('');
const teams=[...new Set(agents.map(a=>a.team))];
$('#teams').innerHTML=teams.map(t=>{const list=agents.filter(a=>a.team===t);return `<div class="team glass"><div class="th"><h3>${esc(t)}</h3><span>${list.length}</span></div><ul>${list.map(a=>`<li><button data-agent="${a.id}"><b>${esc(a.name.split(' · ')[0])}</b><small>${esc(a.task)}</small></button></li>`).join('')}</ul></div>`}).join('');
$('#feedlist').innerHTML=feed.map(f=>`<li><time>${esc(f.t)}</time><span><b>${esc(f.who.split(' · ')[0])}</b> ${esc(f.msg)}</span></li>`).join('');
const card=$('#agent-card');
window.selectAgent=id=>{const a=agents.find(x=>x.id===id);if(!a)return;card.hidden=false;card.innerHTML=`<button class="x" aria-label="Close">×</button><span class="eyebrow">${esc(a.team)} · ${S}</span><h3>${esc(a.name)}</h3><p><b>Personality</b> ${esc(a.personality)}</p><p><b>Task</b> ${esc(a.task)}</p><p><b>Status</b> ${esc(a.status)} (sample)</p>`;card.querySelector('.x').onclick=()=>{card.hidden=true;window.highlightAgent?.(null)};window.highlightAgent?.(id);};
document.addEventListener('click',e=>{const b=e.target.closest('[data-agent]');if(!b)return;const id=b.dataset.agent;$('.scene-wrap').scrollIntoView({behavior:'smooth',block:'start'});const open=()=>window.selectAgent(id);if(document.body.dataset.view!=='interior'){document.querySelector('[data-view="interior"]').click();setTimeout(open,3400);}else open();});
