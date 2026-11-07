// PREVIEW ONLY. Every value in this file is SAMPLE / PLACEHOLDER data. No real accounts, no real numbers.
export const SAMPLE = true;
const first=['Ada','Bram','Cleo','Dex','Eira','Fitz','Gus','Hana','Ivo','Juno','Kai','Lux','Milo','Nia','Oren','Pia','Quin','Rhea','Sol','Tess','Uma','Vic','Wren','Xan','Yara','Zed','Arlo','Bea','Cy','Dot','Eli','Faye','Gio','Hux','Ines','Jax','Kit','Lena','Max','Noor','Otto','Pax','Rue','Sage','Theo','Uri','Vera','Wes','Yuki','Zia'];
const traits=['meticulous','restless','skeptical','cheerful','quiet','competitive','curious','blunt','patient','chaotic'];
const teams=[
  {team:'TikTok scouts',count:8,task:'Placeholder task: scan sample TikTok trend feed, slice'},
  {team:'YouTube Shorts scouts',count:7,task:'Placeholder task: scan sample Shorts trend feed, slice'},
  {team:'Instagram Reels scouts',count:7,task:'Placeholder task: scan sample Reels trend feed, slice'},
  {team:'Meme page scouts',count:5,task:'Placeholder task: watch sample meme-page feed, slice'},
  {team:'Faceless niche scouts',count:10,task:'Placeholder task: sample niche sweep'},
  {team:'Why-it-works analysts',count:7,task:'Placeholder task: deep-dive sample page'},
  {team:'Engagement verifiers',count:4,task:'Placeholder task: real-vs-fake check on sample page'},
  {team:'Floor lead',count:2,task:'Placeholder task: merge sample shortlist, batch'}];
const niches=['AI-voiceover facts','stock-footage motivation','Reddit-story narration','satisfying clips','product / affiliate','history shorts','space facts','quotes','cooking hands-only','lofi edits'];
export const agents=[];let n=0;
for(const t of teams)for(let i=0;i<t.count;i++){n++;const id=String(n).padStart(2,'0');
  const extra=t.team==='Faceless niche scouts'?` "${niches[i%niches.length]}" (sample)`:` #${i+1} (sample)`;
  agents.push({id:'agent-'+id,name:`${first[n-1]} · Sample Agent ${id}`,team:t.team,personality:`${traits[n%traits.length]} (placeholder)`,task:t.task+extra,status:['at desk','walking','at desk','at desk','reviewing'][n%5]});}
const platforms=['TikTok','YouTube Shorts','Instagram Reels','TikTok + YT Shorts','Instagram','YouTube Shorts','TikTok','Instagram Reels','YouTube Shorts','TikTok'];
const routes=['ad revenue (placeholder)','affiliate links (placeholder)','own product (placeholder)','creator fund (placeholder)','sponsorships (placeholder)'];
const fmt=n=>n.toLocaleString('en-US');
export const top10=Array.from({length:10},(_,i)=>{const k=i+1,id=String(k).padStart(2,'0');return{
  rank:k,handle:'@sample_page_'+id,url:null,platform:platforms[i],niche:niches[i]+' (sample)',
  followers:fmt((11-k)*111111),views:fmt((11-k)*1234567),likes:fmt((11-k)*12345),revenue:'$'+fmt((11-k)*1000)+' / mo',
  faceless:'SAMPLE — placeholder evidence',monetization:routes[i%routes.length],
  why:'Placeholder reasoning: sample hook, sample format, sample posting cadence. Not research.',
  verifier:'SAMPLE — not checked'}});
export const feed=Array.from({length:14},(_,i)=>({t:`SAMPLE ${String(12+((i/6)|0)).padStart(2,'0')}:${String((i*7)%60).padStart(2,'0')}`,
  who:agents[(i*7)%50].name,msg:['flagged @sample_page_'+String(1+i%10).padStart(2,'0')+' as a faceless candidate (placeholder)','logged a placeholder views-to-likes ratio','marked a sample source as blocked (placeholder)','moved a sample page to the shortlist (placeholder)','wrote a placeholder why-it-works note'][i%5]}));
