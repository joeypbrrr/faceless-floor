// Isolated headless Chrome test: camera controls, overflow, screenshots. Uses puppeteer-core read from wallet-hunters' test deps (not modified).
const path=require('node:path'),fs=require('node:fs'),assert=require('node:assert/strict');
const puppeteer=require('/workspace/wallet-hunters/.run/control-tests/node_modules/puppeteer-core');
const URL=process.env.TEST_URL||'http://127.0.0.1:8811/preview/',OUT=process.env.TEST_OUT||'/workspace/faceless-shots/local';fs.mkdirSync(OUT,{recursive:true});
const delay=ms=>new Promise(r=>setTimeout(r,ms)),dist=(a,b)=>Math.hypot(...a.map((v,i)=>v-b[i]));
(async()=>{const browser=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});const results=[];try{
for(const mobile of [true,false]){const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
 await page.setViewport(mobile?{width:390,height:844,deviceScaleFactor:3,isMobile:true,hasTouch:true}:{width:1440,height:900,deviceScaleFactor:2});
 const cdp=await page.createCDPSession();const tag=mobile?'phone':'desktop';
 await page.goto(URL+'?t='+Date.now(),{waitUntil:'networkidle2',timeout:90000});await page.waitForFunction(v=>window.facelessFloor?.version===v,{timeout:60000},process.env.VERSION||'preview-v1');await delay(2500);
 const get=()=>page.evaluate(()=>window.facelessFloor.cameraState());
 const box=()=>page.$eval('#scene',e=>{const b=e.getBoundingClientRect();return{x:b.x,y:b.y,w:b.width,h:b.height}});
 const P=(x,y,id)=>({x,y,id,radiusX:5,radiusY:5,force:1});
 async function touch(seq){await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:seq[0]});for(const s of seq.slice(1)){await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:s});await delay(20)}await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await delay(800)}
 async function camTest(v){const b=await box();const start=await get();assert.equal(start.view,v);assert.equal(start.touchAction,'none');let r,z,p;
  if(mobile){const x=b.x+b.w*.35,y=b.y+b.h*.45;await touch(Array.from({length:14},(_,i)=>[P(x+i*6,y,1)]));r=await get();const cx=b.x+b.w/2,cy=b.y+b.h*.45;await touch(Array.from({length:14},(_,i)=>[P(cx-30-i*3,cy,1),P(cx+30+i*3,cy,2)]));z=await get();await touch(Array.from({length:14},(_,i)=>[P(cx-50+i*3,cy+i*2,1),P(cx+50+i*3,cy+i*2,2)]));p=await get();}
  else{const x=b.x+b.w*.4,y=b.y+b.h*.5;await page.mouse.move(x,y);await page.mouse.down();await page.mouse.move(x+120,y+20,{steps:12});await page.mouse.up();await delay(800);r=await get();await page.mouse.wheel({deltaY:-400});await delay(800);z=await get();await page.mouse.move(x,y);await page.mouse.down({button:'right'});await page.mouse.move(x+110,y+40,{steps:12});await page.mouse.up({button:'right'});await delay(800);p=await get();}
  const res={tag,view:v,azimuth_delta:+(r.azimuth-start.azimuth).toFixed(4),zoom_distance_delta:+(z.distance-r.distance).toFixed(4),pan_target_delta:+dist(p.target,z.target).toFixed(4)};
  assert.ok(Math.abs(res.azimuth_delta)>.03,'rotate '+tag+v);assert.ok(Math.abs(res.zoom_distance_delta)>.25,'zoom '+tag+v);assert.ok(res.pan_target_delta>.1,'pan '+tag+v);
  await delay(1500);const h1=await get();await delay(1500);const h2=await get();res.drift_toward_start=+(dist(h1.position,start.position)-dist(h2.position,start.position)).toFixed(4);assert.ok(res.drift_toward_start<.3,'no snap-back '+tag+v);res.no_snapback=true;
  await page.click('#reset-view');await delay(1500);results.push(res);}
 async function overflow(stage){const m=await page.evaluate(()=>({vw:document.documentElement.clientWidth,sw:document.documentElement.scrollWidth,bw:document.body.scrollWidth,scrollX,off:[...document.querySelectorAll('body *')].filter(e=>e.getClientRects().length&&e.getBoundingClientRect().right>document.documentElement.clientWidth+.5&&!e.closest('.team ul')).map(e=>e.tagName+'.'+e.className).slice(0,10)}));m.stage=stage;m.tag=tag;assert.ok(m.sw<=m.vw&&m.bw<=m.vw&&m.scrollX===0&&m.off.length===0,'overflow '+JSON.stringify(m));results.push(m);}
 await overflow('initial');
 await page.screenshot({path:path.join(OUT,tag+'-exterior.png')});
 await camTest('exterior');
 await page.click('[data-view="interior"]');await page.waitForFunction(()=>window.facelessFloor.cameraState().view==='interior'&&window.facelessFloor.ready(),{timeout:30000});await delay(1500);
 await page.screenshot({path:path.join(OUT,tag+'-interior.png')});
 await camTest('interior');
 await page.evaluate(()=>window.selectAgent('agent-07'));await delay(800);await page.screenshot({path:path.join(OUT,tag+'-interior-agent.png')});
 if(mobile){await page.evaluate(()=>scrollTo(0,0));await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[P(350,60,1)]});for(let i=1;i<=14;i++){await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[P(350-i*20,60,1)]});await delay(15)}await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await delay(500);await overflow('after horizontal swipe');}
 await page.$eval('#top10',e=>e.scrollIntoView({block:'start',behavior:'instant'}));await delay(700);
 await page.screenshot({path:path.join(OUT,tag+'-top10.png')});await overflow('top10');
 await page.screenshot({path:path.join(OUT,tag+'-fullpage.png'),fullPage:true});
 results.push({tag,errors});assert.deepEqual(errors,[]);await page.close();}
fs.writeFileSync(path.join(OUT,'results.json'),JSON.stringify(results,null,2));console.log(JSON.stringify(results.filter(r=>r.view||r.errors),null,1));console.log('ALL PASS');
}finally{await browser.close()}})().catch(e=>{console.error(e);process.exit(1)});
