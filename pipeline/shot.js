const {chromium}=require('playwright');const path=require('path');
(async()=>{const [out,...names]=process.argv.slice(2);const b=await chromium.launch();
const p=await b.newPage({viewport:{width:1080,height:1350}});
for(const n of names){await p.goto('file://'+path.resolve(out,n+'.html'));await p.waitForTimeout(1500);
await p.screenshot({path:path.resolve(out,n+'.png'),type:'png'});}
await b.close()})();
