// Usage (needs: npm i puppeteer-core, Chrome):  BASE=https://veriaguide.gr node scripts/contrast_scan.cjs '["/","/contact"]'
//   exit code 1 when any text has insufficient contrast in the dark or light scheme of the Zeitalter theme.
// Scans every visible text element for contrast against its effective background (walks ancestors, composites alpha).
const puppeteer = require('puppeteer-core'); const B=process.env.BASE||'http://localhost:8767';
const pages = JSON.parse(process.argv[2]); const schemes=['dark','light'];
function lum([r,g,b]){const f=c=>{c/=255;return c<=0.03928?c/12.92:Math.pow((c+0.055)/1.055,2.4)};return 0.2126*f(r)+0.7152*f(g)+0.0722*f(b)}
(async()=>{
 const b=await puppeteer.launch({executablePath:process.env.CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:'new',args:['--no-sandbox']});
 let total=0;
 for (const scheme of schemes) for (const path of pages) {
  const p=await b.newPage(); await p.setViewport({width:1440,height:900});
  await p.setCookie({name:'vg_theme',value:'zeitalter',url:B},{name:'cookie_consent',value:'essential',url:B});
  await p.evaluateOnNewDocument(s=>{try{localStorage.setItem('vg_scheme',s)}catch(e){}}, scheme);
  await p.goto(B+path,{waitUntil:'networkidle2'});
  const h=await p.evaluate(()=>document.documentElement.scrollHeight);
  for(let y=0;y<h;y+=600){await p.evaluate(y=>window.scrollTo(0,y),y);await new Promise(r=>setTimeout(r,80));}
  await new Promise(r=>setTimeout(r,1200));
  const res=await p.evaluate(()=>{
    const parse=c=>{const m=c.match(/rgba?\(([^)]+)\)/); if(!m) return null; const a=m[1].split(',').map(Number); return [a[0],a[1],a[2],a.length>3?a[3]:1]};
    const lum=([r,g,b])=>{const f=c=>{c/=255;return c<=0.03928?c/12.92:Math.pow((c+0.055)/1.055,2.4)};return 0.2126*f(r)+0.7152*f(g)+0.0722*f(b)};
    const bgOf=el=>{ // composite backgrounds from root to el; null if an image/gradient is involved
      const chain=[]; for(let e=el;e;e=e.parentElement) chain.unshift(e);
      let base=[255,255,255]; let unknown=false;
      for(const e of chain){const cs=getComputedStyle(e); if(cs.backgroundImage!=='none') {unknown=true;} const c=parse(cs.backgroundColor); if(c&&c[3]>0){base=base.map((v,i)=>Math.round(c[i]*c[3]+v*(1-c[3])))}}
      return {base,unknown};};
    const out=[]; const seen=new Set();
    const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
    while(walker.nextNode()){const t=walker.currentNode; if(!t.nodeValue.trim()) continue; const el=t.parentElement; if(!el||seen.has(el)) continue; seen.add(el);
      const cs=getComputedStyle(el); if(cs.visibility==='hidden'||cs.display==='none'||Number(cs.opacity)===0) continue;
      const r=el.getBoundingClientRect(); if(r.width<2||r.height<2) continue;
      if(el.closest('script,style,noscript,.leaflet-container,.cookie-consent,[aria-hidden="true"],svg,.zt-outdoor__hero,.ag-hero,.ag-backdrop')) continue;
      let op=1; for(let e=el;e;e=e.parentElement){op*=Number(getComputedStyle(e).opacity)} if(op<0.5) continue;
      const fg=parse(cs.color); if(!fg) continue; const {base,unknown}=bgOf(el); if(unknown) continue;
      const f=fg.slice(0,3).map((v,i)=>Math.round(v*fg[3]+base[i]*(1-fg[3])));
      const L1=lum(f),L2=lum(base); const ratio=(Math.max(L1,L2)+0.05)/(Math.min(L1,L2)+0.05);
      const size=parseFloat(cs.fontSize), bold=parseInt(cs.fontWeight)>=700; const large=size>=24||(size>=18.66&&bold);
      if(ratio<(large?3:4.5)) out.push({ratio:+ratio.toFixed(2),txt:t.nodeValue.trim().slice(0,38),cls:(el.className&&el.className.baseVal===undefined?el.className:'').toString().slice(0,45),tag:el.tagName.toLowerCase(),fg:f.join(','),bg:base.join(',')});
    }
    return out;});
  total+=res.length;
  console.log(`\n== ${scheme} ${path}: ${res.length} violations`);
  const uniq=new Map(); for(const r of res){const k=r.tag+'|'+r.cls+'|'+r.fg+'|'+r.bg; if(!uniq.has(k)) uniq.set(k,r)}
  for(const r of [...uniq.values()].slice(0,14)) console.log(`  ${r.ratio}  <${r.tag} class="${r.cls}"> "${r.txt}"  fg(${r.fg}) bg(${r.bg})`);
  await p.close();
 }
 console.log('\nTOTAL violations:',total); await b.close(); process.exit(total?1:0);
})();
