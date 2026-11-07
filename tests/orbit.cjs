// Exterior orbit screenshots at several azimuths (phone + desktop) to check tower separation.
const path=require('node:path'),fs=require('node:fs');
const puppeteer=require('/workspace/wallet-hunters/.run/control-tests/node_modules/puppeteer-core');
const URL=process.env.TEST_URL||'http://127.0.0.1:8811/preview/',OUT=process.env.TEST_OUT||'/workspace/faceless-shots/orbit-local';fs.mkdirSync(OUT,{recursive:true});
const delay=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{const browser=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});const out=[];try{
for(const mobile of [true,false]){const page=await browser.newPage();await page.setViewport(mobile?{width:390,height:844,deviceScaleFactor:3,isMobile:true,hasTouch:true}:{width:1440,height:900,deviceScaleFactor:2});
 await page.goto(URL+'?t='+Date.now(),{waitUntil:'networkidle2',timeout:90000});await page.waitForFunction(()=>window.facelessFloor,{timeout:60000});await delay(2500);
 const tag=mobile?'phone':'desktop';const b=await page.$eval('#scene',e=>{const r=e.getBoundingClientRect();return{x:r.x,y:r.y,w:r.width,h:r.height}});
 // zoom out a bit first so the whole block is visible
 for(let i=0;i<4;i++){const st=await page.evaluate(()=>facelessFloor.cameraState());const shot=path.join(OUT,`${tag}-exterior-angle${i+1}.png`);await page.screenshot({path:shot});out.push({tag,angle:i+1,azimuth_deg:+(st.azimuth*180/Math.PI).toFixed(1),distance:+st.distance.toFixed(1),shot});
  const x=b.x+b.w*.2,y=b.y+b.h*.55;await page.mouse.move(x,y);await page.mouse.down();await page.mouse.move(x+b.w*.55,y,{steps:20});await page.mouse.up();await delay(4500);}
 await page.close();}
console.log(JSON.stringify(out,null,1));}finally{await browser.close()}})().catch(e=>{console.error(e);process.exit(1)});
