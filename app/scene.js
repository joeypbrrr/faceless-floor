// Faceless Floor — LIVE scene, driven by data/live.json (real research snapshot).
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { agents, top10, feed, META } from './data.js?v=live-v1';
const T=THREE, canvas=document.querySelector('#scene'), wrap=canvas.parentElement;
const coarse=matchMedia('(pointer: coarse)').matches, small=innerWidth<720, reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
let renderer;
try{renderer=new T.WebGLRenderer({canvas,antialias:!small,powerPreference:'high-performance'});}catch(e){document.querySelector('#scene-fallback').hidden=false;throw e;}
renderer.setPixelRatio(Math.min(devicePixelRatio,small?1.5:2));
renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=1.05;
renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.PCFSoftShadowMap;
const scene=new T.Scene();
const camera=new T.PerspectiveCamera(42,1,.1,600);
const controls=new OrbitControls(camera,canvas);
controls.enableDamping=true;controls.dampingFactor=.08;controls.rotateSpeed=coarse?.6:.75;controls.zoomSpeed=.9;controls.panSpeed=.8;
controls.screenSpacePanning=false;controls.maxPolarAngle=Math.PI/2-.04;controls.minPolarAngle=.12;
controls.touches={ONE:T.TOUCH.ROTATE,TWO:T.TOUCH.DOLLY_PAN};
controls.mouseButtons={LEFT:T.MOUSE.ROTATE,MIDDLE:T.MOUSE.DOLLY,RIGHT:T.MOUSE.PAN};
canvas.style.touchAction='none';
const POSES={exterior:{pos:[30,13,40],target:[0,9,0],min:12,max:130,bound:40},interior:{pos:[0,17,25],target:[0,1.6,0],min:5,max:44,bound:16}};
function pose(v){const p=POSES[v],narrow=wrap.clientWidth/Math.max(1,wrap.clientHeight)<.8;if(!narrow)return p;if(v==='interior')return{...p,pos:[0,30,24],target:[0,0,1.5]};return{...p,pos:p.pos.map((c,i)=>p.target[i]+(c-p.target[i])*1.55)};}
let view=location.hash.includes('floor')?'interior':'exterior';
let tween=null;
function setLimits(v){const p=POSES[v];controls.minDistance=p.min;controls.maxDistance=p.max;}
function placeCamera(v){const p=pose(v);camera.position.set(...p.pos);controls.target.set(...p.target);setLimits(v);controls.update();}
controls.addEventListener('start',()=>{if(tween&&!tween.locked)tween=null;document.querySelector('#scene-hint')?.classList.add('gone');});
controls.addEventListener('change',()=>{if(tween)return;const b=POSES[view].bound,t=controls.target;t.x=T.MathUtils.clamp(t.x,-b,b);t.z=T.MathUtils.clamp(t.z,-b,b);t.y=T.MathUtils.clamp(t.y,.5,view==='exterior'?26:8);});

// ---------- helpers ----------
const std=(c,r=.7,m=0,extra={})=>new T.MeshStandardMaterial({color:c,roughness:r,metalness:m,...extra});
function add(parent,geo,mat,x=0,y=0,z=0,{cast=true,receive=true}={}){const o=new T.Mesh(geo,mat);o.position.set(x,y,z);o.castShadow=cast;o.receiveShadow=receive;parent.add(o);return o;}
function canvasTex(w,h,draw){const c=document.createElement('canvas');c.width=w;c.height=h;const g=c.getContext('2d');draw(g,w,h);const t=new T.CanvasTexture(c);t.colorSpace=T.SRGBColorSpace;t.anisotropy=4;t.userData={c,g};return t;}
const rand=(s=>()=>(s=(s*16807)%2147483647)/2147483647)(42);
const ease=t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;

// ---------- sky + lights ----------
const sky=new T.Mesh(new T.SphereGeometry(400,32,16),new T.ShaderMaterial({side:T.BackSide,depthWrite:false,uniforms:{top:{value:new T.Color(0x0a1026)},mid:{value:new T.Color(0x3a2f5c)},bottom:{value:new T.Color(0xe39a6b)}},
 vertexShader:'varying vec3 vp;void main(){vp=normalize(position);gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',
 fragmentShader:'uniform vec3 top,mid,bottom;varying vec3 vp;void main(){float h=vp.y;vec3 c=h>0.08?mix(mid,top,smoothstep(.08,.6,h)):mix(bottom,mid,smoothstep(-.05,.08,h));gl_FragColor=vec4(c,1.);}'}));
scene.add(sky);
const starGeo=new T.BufferGeometry(),sp=[];for(let i=0;i<700;i++){const th=rand()*Math.PI*2,ph=Math.acos(.15+rand()*.85);sp.push(380*Math.sin(ph)*Math.cos(th),380*Math.cos(ph),380*Math.sin(ph)*Math.sin(th));}
starGeo.setAttribute('position',new T.Float32BufferAttribute(sp,3));scene.add(new T.Points(starGeo,new T.PointsMaterial({color:0xfff4e0,size:1.4,sizeAttenuation:false,transparent:true,opacity:.75})));
scene.fog=new T.Fog(0x2b2547,70,260);
const hemi=new T.HemisphereLight(0x8fa0d8,0x2a1d18,.9);scene.add(hemi);
const sun=new T.DirectionalLight(0xffc49a,1.6);sun.position.set(-40,45,35);sun.castShadow=true;
sun.shadow.mapSize.set(small?1024:2048,small?1024:2048);Object.assign(sun.shadow.camera,{left:-45,right:45,top:45,bottom:-45,near:5,far:160});sun.shadow.bias=-.0004;sun.shadow.normalBias=.03;scene.add(sun);

// ---------- EXTERIOR ----------
const ext=new T.Group();scene.add(ext);
const stoneTex=canvasTex(512,512,(g,w,h)=>{g.fillStyle='#5b5650';g.fillRect(0,0,w,h);for(let y=0;y<8;y++)for(let x=0;x<8;x++){const v=82+((rand()*18)|0);g.fillStyle=`rgb(${v+6},${v+2},${v-4})`;g.fillRect(x*64+2,y*64+2,60,60);}});
stoneTex.wrapS=stoneTex.wrapT=T.RepeatWrapping;stoneTex.repeat.set(16,10);
add(ext,new T.BoxGeometry(130,.4,80),std(0xffffff,.85,0,{map:stoneTex}),0,-.2,-14,{cast:false});
add(ext,new T.BoxGeometry(220,.3,16),std(0x1c1d24,.55,.1),0,-.25,34,{cast:false});
for(let x=-100;x<=100;x+=8)add(ext,new T.BoxGeometry(3.6,.02,.22),std(0xe8d9b0,.6,0,{emissive:0x3a3320}),x,-.09,34,{cast:false});
add(ext,new T.BoxGeometry(220,.35,1.2),std(0x77716a),0,0,26,{cast:false});add(ext,new T.BoxGeometry(220,.35,1.2),std(0x77716a),0,0,42,{cast:false});
const ivory=std(0xe7dfcf,.62),ivoryDark=std(0xcfc5b2,.7),bronze=std(0x9a7a4a,.35,.8),glassWarm=std(0x2a1a0e,.15,.2,{emissive:0xffb35c,emissiveIntensity:1.25});
for(let i=0;i<6;i++)add(ext,new T.BoxGeometry(30-i*.6,.38,3.4-i*.0),ivoryDark,0,.19+i*.38,14.2-i*.55);
add(ext,new T.BoxGeometry(28,.6,18),ivory,0,2.3,4.2);
const colGeo=new T.LatheGeometry([[0,0],[1.05,0],[1.05,.25],[.9,.4],[.8,.55],[.74,1],[.68,10.4],[.8,10.6],[1.0,10.85],[1.1,11.1],[0,11.1]].map(p=>new T.Vector2(p[0],p[1])),28);
const COLS=8,colZ=11.4;for(let i=0;i<COLS;i++){const x=-11.9+i*3.4;add(ext,colGeo,ivory,x,2.6,colZ);}
add(ext,new T.BoxGeometry(28.6,.9,4),ivory,0,14.15,colZ);
const friezeTex=canvasTex(2048,128,(g,w,h)=>{g.fillStyle='#ded5c3';g.fillRect(0,0,w,h);g.fillStyle='#4b3f2e';g.font='600 64px "Instrument Serif", Georgia, serif';g.textAlign='center';g.textBaseline='middle';g.letterSpacing='18px';g.fillText('FACELESS  FLOOR  EXCHANGE  ·  LIVE',w/2,h/2+4);});
add(ext,new T.BoxGeometry(28.6,1.5,4),[ivory,ivory,ivory,ivory,std(0xffffff,.6,0,{map:friezeTex}),ivory],0,15.35,colZ);
add(ext,new T.BoxGeometry(29.4,.5,4.4),ivoryDark,0,16.35,colZ);
const ped=new T.Shape();ped.moveTo(-14.6,0);ped.lineTo(14.6,0);ped.lineTo(0,4.2);ped.closePath();
const pedM=add(ext,new T.ExtrudeGeometry(ped,{depth:3.6,bevelEnabled:true,bevelSize:.12,bevelThickness:.12,bevelSegments:1}),ivory,0,16.6,colZ-1.8);
const tymp=new T.Shape();tymp.moveTo(-12.4,0);tymp.lineTo(12.4,0);tymp.lineTo(0,3.2);tymp.closePath();add(ext,new T.ShapeGeometry(tymp),std(0xb9ad97,.8),0,17.0,colZ+1.95,{cast:false});
// body + facade windows
add(ext,new T.BoxGeometry(26,13,15),std(0xd6cdbb,.75),0,8.9,1.5);
for(let r=0;r<3;r++)for(let i=0;i<7;i++){const x=-10.2+i*3.4;if(r===0&&i===3)continue;const w=add(ext,new T.BoxGeometry(1.5,r===0?3.4:2.4,.12),glassWarm,x,r===0?5.0:9.2+(r-1)*3,9.04,{cast:false});w.material=rand()<.18?std(0x161a26,.2,.4,{emissive:0x1d2a44,emissiveIntensity:.6}):glassWarm;add(ext,new T.BoxGeometry(1.8,.18,.4),ivoryDark,x,r===0?3.2:7.9+(r-1)*3,9.1);}
const door=add(ext,new T.BoxGeometry(3,5.2,.15),std(0x3a2410,.25,.3,{emissive:0xffa64a,emissiveIntensity:1.6}),0,5.2,9.06,{cast:false});door.name='door';
add(ext,new T.BoxGeometry(3.8,.3,.5),bronze,0,7.9,9.1);
// tower with lit windows
function windowTex(cols,rows,warm,seed){return canvasTex(cols*16,rows*16,(g,w,h)=>{g.fillStyle='#1a1d27';g.fillRect(0,0,w,h);for(let y=0;y<rows;y++)for(let x=0;x<cols;x++){const on=rand()<(warm?.55:.4);g.fillStyle=on?(warm?(rand()<.5?'#ffcf8a':'#ffe2b3'):(rand()<.5?'#bcd6ff':'#ffe6c0')):'#232838';g.fillRect(x*16+3,y*16+3,10,10);}});}
const towers=[];// towers fade when they sit between the camera and its target, so no orbit angle is blocked
function tower(x,z,w,h,d,warm,color,extra=0){const tex=windowTex(Math.round(w*1.6),Math.round(h*1.2),warm);const m=std(color,.4,.35,{map:tex,emissive:0xffffff,emissiveMap:tex,emissiveIntensity:.85,transparent:true});add(ext,new T.BoxGeometry(w,h,d),m,x,h/2,z);towers.push({box:new T.Box3(new T.Vector3(x-w/2,0,z-d/2),new T.Vector3(x+w/2,h+extra,z+d/2)),mats:[m],o:1});return m;}
// HQ tower stands on its own lot behind the exchange: exchange back wall is z=-6, tower front is z=-16 (10-unit alley).
const TZ=-22;tower(0,TZ,18,38,12,true,0xb9ac96,12);{const cr=[ivory.clone(),ivory.clone(),bronze.clone()];cr.forEach(m=>m.transparent=true);add(ext,new T.BoxGeometry(19,1.2,13),cr[0],0,38.6,TZ);add(ext,new T.BoxGeometry(12,4,8),cr[1],0,41,TZ);
add(ext,new T.ConeGeometry(4.6,6,4),cr[2],0,46,TZ).rotation.y=Math.PI/4;towers[towers.length-1].mats.push(...cr);}
const beacon=add(ext,new T.SphereGeometry(.45,16,12),std(0xff5a3a,.3,0,{emissive:0xff4a2a,emissiveIntensity:3}),0,49.4,TZ,{cast:false});
add(ext,new T.BoxGeometry(46,.04,8),std(0x1c1d24,.55,.1),0,.02,-11,{cast:false});
for(const [x,z,w,h,d] of [[-34,-6,12,30,12],[35,-8,13,44,13],[-50,-24,14,56,14],[52,-28,14,34,14],[-24,-38,12,48,12],[25,-40,12,60,12]])tower(x,z,w,h,d,false,0x7f8aa3);
// lamps, planters, flags
const lampMat=std(0x1f1d1b,.4,.8),bulb=std(0xfff1d6,.2,0,{emissive:0xffcf8f,emissiveIntensity:2.6});
for(let x=-24;x<=24;x+=8){if(Math.abs(x)<4)continue;add(ext,new T.CylinderGeometry(.12,.18,5.2,10),lampMat,x,2.6,22);add(ext,new T.SphereGeometry(.42,16,12),bulb,x,5.4,22,{cast:false});}
const warmL=new T.PointLight(0xffb36b,60,34,1.6);warmL.position.set(0,6,18);ext.add(warmL);
const planter=std(0x6c655b,.8),leaf=std(0x2f4a35,.9);
for(const x of [-17,-13,13,17]){add(ext,new T.BoxGeometry(2.2,1,2.2),planter,x,.5,17);add(ext,new T.IcosahedronGeometry(1.25,1),leaf,x,1.9,17);}
const flags=[];for(const x of [-15.5,15.5]){add(ext,new T.CylinderGeometry(.08,.08,10,8),bronze,x,5,20);const f=add(ext,new T.PlaneGeometry(2.6,1.5,10,4),std(x<0?0x1d2c55:0x7a1f2a,.8,0,{side:T.DoubleSide}),x+1.3,9.1,20);f.userData.base=f.geometry.attributes.position.array.slice();flags.push(f);}
// street pedestrians (exterior ambience)
const peds=[];const pedMat=[std(0x2b2f3a),std(0x5a4636),std(0x3b4a5c)];for(let i=0;i<10;i++){const g=new T.Group();add(g,new T.CapsuleGeometry(.28,.8,4,8),pedMat[i%3],0,.95,0);add(g,new T.SphereGeometry(.22,12,10),std(0xd7cfc2,.6),0,1.75,0);ext.add(g);peds.push({g,lane:i%2?23.5:44.5,x:-60+rand()*120,s:(i%2?1:-1)*(1.1+rand()*.6)});}

// ---------- INTERIOR ----------
const int=new T.Group();scene.add(int);
const floorTex=canvasTex(512,512,(g,w,h)=>{g.fillStyle='#2a221c';g.fillRect(0,0,w,h);for(let y=0;y<16;y++)for(let x=0;x<4;x++){const v=50+((rand()*22)|0);g.fillStyle=`rgb(${v+28},${v+12},${v-4})`;g.fillRect(x*128+((y%2)*64),y*32+1,126,30);}});
floorTex.wrapS=floorTex.wrapT=T.RepeatWrapping;floorTex.repeat.set(5,4);
add(int,new T.BoxGeometry(44,.3,32),std(0xffffff,.32,.05,{map:floorTex}),0,-.15,0,{cast:false});
add(int,new T.BoxGeometry(30,.04,18),std(0x3a1d1f,.95),0,.02,0,{cast:false});
const wallM=std(0xd9cfbe,.85);
add(int,new T.BoxGeometry(44,11,.6),wallM,0,5.5,-16);add(int,new T.BoxGeometry(.6,11,32),wallM,-22,5.5,0);add(int,new T.BoxGeometry(.6,11,32),wallM,22,5.5,0);
add(int,new T.BoxGeometry(44,.6,.9),std(0xb59b6d,.4,.6),0,11,-16);
for(const z of [-10,-2,6,12]){for(const x of [-21.6,21.6]){add(int,new T.BoxGeometry(.2,6.6,3.2),std(0x101627,.15,.3,{emissive:0x33406e,emissiveIntensity:.9}),x,5,z,{cast:false});}}
const pil=new T.CylinderGeometry(.55,.6,11,20);for(const x of [-16,16])for(const z of [-12,-4,4,12])add(int,pil,wallM,x,5.5,z);
// boards
const feedTex=canvasTex(1024,512,()=>{}),topTex=canvasTex(1024,640,()=>{});
function drawFeed(off=0){const {g}=feedTex.userData,w=1024,h=512;g.fillStyle='#0d1220';g.fillRect(0,0,w,h);g.fillStyle='#e8c27a';g.font='600 34px Inter, Arial';g.fillText('LIVE FEED',40,58);g.fillStyle='#ff8f6b';g.font='700 22px Inter, Arial';g.fillText(('LIVE · UPDATED '+META.updated_label).toUpperCase(),300,56);g.font='22px Inter, Arial';for(let i=0;i<9;i++){const f=feed[(i+off)%feed.length];g.fillStyle=i%2?'#c9d1e8':'#f1ead9';g.fillText(`${f.t}  ${f.who.split(' · ')[0]} — ${f.msg}`.slice(0,84),40,110+i*44);}feedTex.needsUpdate=true;}
function drawTop(){const {g}=topTex.userData,w=1024,h=640;g.fillStyle='#120f0b';g.fillRect(0,0,w,h);g.fillStyle='#e8c27a';g.font='italic 52px "Instrument Serif", Georgia, serif';g.fillText('Top 10 Faceless Pages',40,74);g.fillStyle='#ff8f6b';g.font='700 22px Inter, Arial';g.fillText('VERIFIED DATA ONLY',700,70);g.font='26px Inter, Arial';if(!top10.length){g.fillStyle='#d8cfbd';g.font='28px Inter, Arial';g.fillText('No page qualifies yet.',40,160);}top10.forEach((p,i)=>{g.fillStyle=i%2?'#d8cfbd':'#fff6e4';g.fillText(`${String(p.rank).padStart(2,'0')}  ${p.handle}`,40,130+i*49);g.fillStyle='#9fb0d6';g.fillText(`${p.platform}`,470,130+i*49);g.fillStyle='#e8c27a';g.fillText(`${p.followers}`,800,130+i*49);});topTex.needsUpdate=true;}
const frame=std(0x8a6d3e,.35,.8);
add(int,new T.BoxGeometry(17,8.6,.3),frame,-6,5.6,-15.5);add(int,new T.PlaneGeometry(16.4,8.0),new T.MeshBasicMaterial({map:feedTex,toneMapped:false}),-6,5.6,-15.33,{cast:false,receive:false});
add(int,new T.BoxGeometry(.3,9.4,15.2),frame,21.5,5.6,-4);const tb=add(int,new T.PlaneGeometry(14.6,9.1),new T.MeshBasicMaterial({map:topTex,toneMapped:false}),21.33,5.6,-4,{cast:false,receive:false});tb.rotation.y=-Math.PI/2;
const clockTex=canvasTex(512,256,(g,w,h)=>{g.fillStyle='#0d1220';g.fillRect(0,0,w,h);g.fillStyle='#e8c27a';g.font='italic 70px "Instrument Serif", Georgia, serif';g.textAlign='center';g.fillText(META.qualified+' of 10',w/2,110);g.fillStyle='#8fe3b0';g.font='700 26px Inter, Arial';g.fillText('VERIFIED · LIVE RESEARCH',w/2,180);});
add(int,new T.BoxGeometry(8.6,4.6,.3),frame,10,6.6,-15.5);add(int,new T.PlaneGeometry(8,4),new T.MeshBasicMaterial({map:clockTex,toneMapped:false}),10,6.6,-15.33,{cast:false,receive:false});
// chandeliers + warm lights
const chand=std(0xfff0d0,.2,0,{emissive:0xffc77a,emissiveIntensity:2.2});const iLights=[];
for(const x of [-9,9]){add(int,new T.CylinderGeometry(.03,.03,3,6),bronze,x,9.5,0,{cast:false});add(int,new T.TorusGeometry(1.1,.08,8,32),bronze,x,8,0,{cast:false}).rotation.x=Math.PI/2;add(int,new T.SphereGeometry(.55,20,14),chand,x,7.9,0,{cast:false});const l=new T.PointLight(0xffb870,small?70:90,30,1.5);l.position.set(x,7.5,0);int.add(l);iLights.push(l);}
// desks (instanced)
const TEAMCOL={'TikTok scouts':0x4fd1c5,'YouTube Shorts scouts':0xe2685f,'Instagram Reels scouts':0xc77dde,'Meme page scouts':0xf2c14e,'Faceless niche scouts':0x8fb4ff,'Why-it-works analysts':0xe8c27a,'Engagement verifiers':0x7ed49b,'Floor lead':0xf4efe6};
const seatsX=[-12.6,-9,-5.4,-1.8,1.8,5.4,9,12.6],seatsZ=[-9.5,-4.5,.5,5.5,10.5];const deskN=40;
const deskTop=new T.InstancedMesh(new T.BoxGeometry(2.6,.12,1.3),std(0x5a3a22,.45,.1),deskN),deskBase=new T.InstancedMesh(new T.BoxGeometry(2.3,.9,.9),std(0x2a2522,.6),deskN),
 mon=new T.InstancedMesh(new T.BoxGeometry(.95,.6,.05),std(0x111317,.4,.5),deskN*2),scr=new T.InstancedMesh(new T.PlaneGeometry(.88,.52),new T.MeshBasicMaterial({color:0xffffff,toneMapped:false}),deskN*2),
 chair=new T.InstancedMesh(new T.BoxGeometry(.7,.5,.1),std(0x1d2230,.6),deskN),lampI=new T.InstancedMesh(new T.SphereGeometry(.09,8,6),bulb,deskN);
for(const m of [deskTop,deskBase,mon,chair]){m.castShadow=true;m.receiveShadow=true;int.add(m);}int.add(scr);int.add(lampI);
const M=new T.Matrix4(),Q=new T.Quaternion(),S=new T.Vector3(1,1,1),P=new T.Vector3(),scrCols=[0x4fd1c5,0xe8c27a,0x8fb4ff,0xe2685f,0xc77dde];const deskPos=[];
let di=0;for(const z of seatsZ)for(const x of seatsX){deskPos.push([x,z]);M.compose(P.set(x,.97,z),Q.identity(),S);deskTop.setMatrixAt(di,M);M.compose(P.set(x,.47,z-.1),Q,S);deskBase.setMatrixAt(di,M);
 for(let k=0;k<2;k++){const mx=x+(k?.5:-.5);M.compose(P.set(mx,1.42,z-.4),Q,S);mon.setMatrixAt(di*2+k,M);M.compose(P.set(mx,1.42,z-.37),Q,S);scr.setMatrixAt(di*2+k,M);scr.setColorAt(di*2+k,new T.Color(scrCols[(di+k)%5]).multiplyScalar(.9));}
 M.compose(P.set(x,.78,z+1.2),Q,S);chair.setMatrixAt(di,M);M.compose(P.set(x-1.1,1.12,z-.3),Q,S);lampI.setMatrixAt(di,M);di++;}
// agents
const skin=std(0xe9e1d3,.55);// faceless mannequin heads — a quiet nod to the brief
const agentObjs=[];const pickables=[];
function makeAgent(a){const g=new T.Group(),c=TEAMCOL[a.team]||0xcccccc,body=std(c,.6),dark=std(0x23262e,.7);
 const torso=add(g,new T.CapsuleGeometry(.27,.55,4,10),body,0,1.25,0);const head=add(g,new T.SphereGeometry(.21,16,12),skin,0,1.88,0);
 const legL=new T.Group(),legR=new T.Group();legL.position.set(-.13,.82,0);legR.position.set(.13,.82,0);add(legL,new T.BoxGeometry(.16,.8,.18),dark,0,-.4,0);add(legR,new T.BoxGeometry(.16,.8,.18),dark,0,-.4,0);g.add(legL,legR);
 const armL=new T.Group(),armR=new T.Group();armL.position.set(-.36,1.5,0);armR.position.set(.36,1.5,0);add(armL,new T.BoxGeometry(.12,.6,.14),body,0,-.3,0);add(armR,new T.BoxGeometry(.12,.6,.14),body,0,-.3,0);g.add(armL,armR);
 const ring=add(g,new T.RingGeometry(.45,.58,32),new T.MeshBasicMaterial({color:0xe8c27a,transparent:true,opacity:0,side:T.DoubleSide}),0,.04,0,{cast:false,receive:false});ring.rotation.x=-Math.PI/2;
 g.traverse(o=>{if(o.isMesh){o.userData.agent=a.id;pickables.push(o);}});int.add(g);return {a,g,torso,head,legL,legR,armL,armR,ring};}
const walkPaths=[];const W=[[-15,-12.5],[15,-12.5],[15,13],[-15,13]];
agents.forEach((a,i)=>{const o=makeAgent(a);o.phase=rand()*6.28;
 if(i<deskN){const [x,z]=deskPos[i];o.mode='desk';o.g.position.set(x,.0,z+.95);o.g.rotation.y=Math.PI;o.legL.rotation.x=o.legR.rotation.x=-Math.PI/2+.1;o.legL.position.y=o.legR.position.y=.98;o.g.position.y=-.32;o.armL.rotation.x=o.armR.rotation.x=-1.1;}
 else{o.mode='walk';o.speed=1.05+rand()*.35;o.dir=i%2?1:-1;o.t=rand();o.inset=(i%3)*.9;}
 agentObjs.push(o);});
function perimeterPoint(t,inset){const pts=W.map(([x,z])=>[x-Math.sign(x)*inset,z-Math.sign(z)*inset]);const segs=pts.map((p,i)=>{const q=pts[(i+1)%4];return{p,q,len:Math.hypot(q[0]-p[0],q[1]-p[1])};});const total=segs.reduce((s,x)=>s+x.len,0);let d=((t%1)+1)%1*total;for(const s of segs){if(d<=s.len){const f=d/s.len;return [s.p[0]+(s.q[0]-s.p[0])*f,s.p[1]+(s.q[1]-s.p[1])*f,total];}d-=s.len;}return [pts[0][0],pts[0][1],total];}

// ---------- views & transitions ----------
const fade=document.querySelector('#scene-fade');
function applyVisibility(){ext.visible=view==='exterior';sky.visible=view==='exterior';scene.background=view==='exterior'?null:new T.Color(0x120e0b);scene.fog.color.set(view==='exterior'?0x2b2547:0x120e0b);int.visible=view==='interior';hemi.intensity=view==='exterior'?.9:.75;hemi.color.set(view==='exterior'?0x8fa0d8:0xffe2bd);sun.intensity=view==='exterior'?1.6:.55;sun.position.set(...(view==='exterior'?[-40,45,35]:[-12,30,14]));scene.fog.near=view==='exterior'?70:40;scene.fog.far=view==='exterior'?260:120;
 document.querySelectorAll('[data-view]').forEach(b=>{const on=b.dataset.view===view;b.classList.toggle('active',on);b.setAttribute('aria-pressed',on);});document.body.dataset.view=view;}
function flyTo(pos,target,ms,locked){return new Promise(res=>{tween={from:camera.position.clone(),fromT:controls.target.clone(),to:new T.Vector3(...pos),toT:new T.Vector3(...target),t0:performance.now(),ms:reduced?1:ms,res,locked};});}
let busy=false;
async function go(v){if(busy||v===view)return;busy=true;controls.enabled=false;
 if(v==='interior'){setLimits('exterior');controls.minDistance=0;await flyTo([0,5.4,17],[0,5.2,9],1300,true);}else{await flyTo([0,10,24],[0,2,-10],900,true);}
 fade.classList.add('on');await new Promise(r=>setTimeout(r,reduced?0:380));view=v;applyVisibility();
 if(v==='interior'){camera.position.set(0,5,15.5);controls.target.set(0,2.2,0);}else{camera.position.set(0,5.4,19);controls.target.set(0,5.2,9);}
 fade.classList.remove('on');setLimits(v);controls.minDistance=0;controls.maxDistance=999;const p=pose(v);await flyTo(p.pos,p.target,1500,true);setLimits(v);controls.enabled=true;busy=false;
 history.replaceState(null,'',v==='interior'?'#floor':'#exterior');}
function reset(){if(busy)return;const p=pose(view);flyTo(p.pos,p.target,900,false).then(()=>setLimits(view));}
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>go(b.dataset.view)));
document.querySelector('#reset-view').addEventListener('click',reset);
// picking (tap without drag)
const ray=new T.Raycaster(),ndc=new T.Vector2();let down=null,selected=null;
canvas.addEventListener('pointerdown',e=>{down={x:e.clientX,y:e.clientY,t:performance.now(),moved:false};});
canvas.addEventListener('pointermove',e=>{if(down&&Math.hypot(e.clientX-down.x,e.clientY-down.y)>7)down.moved=true;});
canvas.addEventListener('pointerup',e=>{if(!down||down.moved||busy){down=null;return;}down=null;const r=canvas.getBoundingClientRect();ndc.set((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1);ray.setFromCamera(ndc,camera);
 if(view==='exterior'){if(ray.intersectObjects(ext.children,false).length)go('interior');return;}
 const hit=ray.intersectObjects(pickables,false)[0];if(hit)window.selectAgent?.(hit.object.userData.agent);});
window.highlightAgent=id=>{selected=id;agentObjs.forEach(o=>o.ring.material.opacity=o.a.id===id?.95:0);};
// diagnostics for regression tests (read-only)
window.facelessFloor=Object.freeze({version:'live-v1',ready:()=>!busy,cameraState:()=>({view,position:camera.position.toArray(),target:controls.target.toArray(),azimuth:controls.getAzimuthalAngle(),polar:controls.getPolarAngle(),distance:controls.getDistance(),busy,touchAction:canvas.style.touchAction})});
// resize: only touches aspect/size, never the camera pose
function resize(){const w=wrap.clientWidth,h=wrap.clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.fov=w<520?52:42;camera.updateProjectionMatrix();}
resize();placeCamera(view);new ResizeObserver(resize).observe(wrap);applyVisibility();drawFeed();drawTop();
document.fonts?.ready.then(()=>{drawFeed();drawTop();});
let feedOff=0;setInterval(()=>{drawFeed(++feedOff);},2600);
// ---------- loop ----------
const occRay=new T.Ray(),occHit=new T.Vector3();const clock=new T.Clock();let visible=true;new IntersectionObserver(([e])=>visible=e.isIntersecting).observe(wrap);
renderer.setAnimationLoop(()=>{const dt=Math.min(clock.getDelta(),.05),t=clock.elapsedTime;if(!visible)return;
 if(tween){const k=Math.min(1,(performance.now()-tween.t0)/tween.ms),e=ease(k);camera.position.lerpVectors(tween.from,tween.to,e);controls.target.lerpVectors(tween.fromT,tween.toT,e);if(k>=1){const r=tween.res;tween=null;r();}}
 controls.update();
 if(ext.visible){occRay.origin.copy(camera.position);occRay.direction.subVectors(controls.target,camera.position);const span=occRay.direction.length();occRay.direction.normalize();for(const tw of towers){const inside=tw.box.containsPoint(camera.position),hit=occRay.intersectBox(tw.box,occHit);const want=(inside||(hit&&camera.position.distanceTo(occHit)<span-1))?.12:1;tw.o+=(want-tw.o)*Math.min(1,dt*8);for(const m of tw.mats){m.opacity=tw.o;m.depthWrite=tw.o>.95;}}
  beacon.material.emissiveIntensity=2+Math.sin(t*2.4)*1.2;for(const f of flags){const a=f.geometry.attributes.position,b=f.userData.base;for(let i=0;i<a.count;i++){const x=b[i*3];a.array[i*3+2]=Math.sin(x*2.2+t*3)*.12*(x+1.3);}a.needsUpdate=true;}
  for(const p of peds){p.x+=p.s*dt;if(p.x>70)p.x=-70;if(p.x<-70)p.x=70;p.g.position.set(p.x,0,p.lane);p.g.rotation.y=p.s>0?Math.PI/2:-Math.PI/2;p.g.position.y=Math.abs(Math.sin(t*6+p.lane))*.05;}}
 if(int.visible){for(const o of agentObjs){if(o.mode==='desk'){const k=Math.sin(t*9+o.phase);o.armL.rotation.x=-1.1+k*.08;o.armR.rotation.x=-1.1-k*.08;o.head.rotation.y=Math.sin(t*.4+o.phase)*.25;o.head.position.y=1.88+Math.sin(t*1.3+o.phase)*.012;}
  else{const [,,total]=perimeterPoint(0,o.inset);o.t+=o.dir*o.speed*dt/total;const [x,z]=perimeterPoint(o.t,o.inset),[nx,nz]=perimeterPoint(o.t+o.dir*.004,o.inset);o.g.position.set(x,Math.abs(Math.sin(t*6.4*o.speed+o.phase))*.06,z);
   const target=Math.atan2(nx-x,nz-z);let d=target-o.g.rotation.y;d=Math.atan2(Math.sin(d),Math.cos(d));o.g.rotation.y+=d*Math.min(1,dt*8);const s=Math.sin(t*6.4*o.speed+o.phase);o.legL.rotation.x=s*.5;o.legR.rotation.x=-s*.5;o.armL.rotation.x=-s*.4;o.armR.rotation.x=s*.4;}
   if(o.ring.material.opacity>0)o.ring.rotation.z=t;}
  iLights.forEach((l,i)=>l.intensity=(small?70:90)*(1+Math.sin(t*1.7+i)*.03));}
 renderer.render(scene,camera);});
window.dispatchEvent(new Event('faceless-scene-ready'));
