const assert=require('assert');
const {launch}=require('./lib.cjs');
(async()=>{const b=await launch(390,844);try{
 for(const scenario of [{ready:false,active:false},{ready:true,active:true},{ready:true,active:false}]){
 const p=await b.newPage();await p.setRequestInterception(true);
 p.on('request',r=>{if(r.url().endsWith('/api/plan'))return r.respond({status:200,contentType:'application/json',body:JSON.stringify({purchase_available:scenario.ready,active:scenario.active,product_id:'interviewanchor_pro_yearly'})});r.continue()});
 await p.evaluateOnNewDocument(()=>{window.getDigitalGoodsService=async()=>({getDetails:async()=>[{itemId:'interviewanchor_pro_yearly',price:{currency:'INR',value:'599.00'}}],listPurchases:async()=>[]});});
 await p.goto('http://127.0.0.1:8124/plans',{waitUntil:'networkidle0'});
 assert.equal(await p.$eval('#buyPlan',e=>e.disabled),!scenario.ready||scenario.active);
 assert.equal(await p.$eval('#restorePlan',e=>e.disabled),false);
 console.log(JSON.stringify({scenario,passed:true}));await p.close();
 }
}finally{await b.close()}})().catch(e=>{console.error(e);process.exitCode=1});
