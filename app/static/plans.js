'use strict';
(async()=>{
 const $=id=>document.getElementById(id);let service=null,plan=null,details=null;
 async function request(path,body){const r=await fetch(path,{method:body===undefined?'GET':'POST',headers:body===undefined?{}:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)});const j=await r.json();if(!r.ok)throw new Error(j.detail||'Please try again later.');return j}
 async function restoreOne(token){return request('/api/billing/play/verify',{purchase_token:token})}
 async function refresh(){
  plan=await request('/api/plan');
  $('launchStatus').textContent=plan.active?'Your verified Pro plan is active.':plan.enabled?'Free practice is ready. Sign in to buy or restore your yearly plan.':'Pro is being prepared. No paid purchases are available yet; existing AI preview access has not been changed.';
  if(!plan.purchase_available)return;
  if(!('getDigitalGoodsService' in window)){$('result').textContent='Play purchases work only in the compatible Android app installed through Google Play.';return}
  service=await window.getDigitalGoodsService('https://play.google.com/billing');
  const products=await service.getDetails([plan.product_id]);details=products.find(x=>x.itemId===plan.product_id);
  if(!details||!details.price)throw new Error('This plan is not available from Google Play yet.');
  $('storePrice').textContent=new Intl.NumberFormat(navigator.language,{style:'currency',currency:details.price.currency}).format(details.price.value)+' / year';
  $('buyPlan').textContent='Buy one year on Google Play';$('buyPlan').disabled=false;$('restorePlan').disabled=false;
 }
 $('buyPlan').onclick=async()=>{
  if(!service||!details||!plan.purchase_available)return;
  let response;try{
   const me=await request('/api/auth/me');if(!me.user)throw new Error('Sign in to InterviewAnchor first, then return to Plans.');
   $('buyPlan').disabled=true;
   await request('/api/billing/play/prepare',{});
   const pr=new PaymentRequest([{supportedMethods:'https://play.google.com/billing',data:{sku:plan.product_id}}],{total:{label:details.title||'InterviewAnchor Pro',amount:{currency:details.price.currency,value:details.price.value}}});
   response=await pr.show();
   const token=response.details&&response.details.purchaseToken;if(!token)throw new Error('Google Play did not return a purchase to verify.');
   const verified=await restoreOne(token);if(!verified.ok||!['active','grace'].includes(verified.state))throw new Error('Payment is pending. Access starts only when Google Play confirms payment.');
   await response.complete('success');response=null;$('result').textContent='Purchase verified. Your yearly plan is active.';await refresh();
  }catch(e){if(response)try{await response.complete('fail')}catch(_){}$('result').textContent=e.name==='AbortError'?'Purchase canceled. No plan was granted.':e.message+' If Google Play took payment, use Restore purchase; do not buy twice.';}finally{$('buyPlan').disabled=!service}
 };
 $('restorePlan').onclick=async()=>{try{
  const me=await request('/api/auth/me');if(!me.user)throw new Error('Sign in to the InterviewAnchor account that bought the plan.');
  const purchases=await service.listPurchases();let found=false;
  for(const p of purchases){if(p.itemId!==plan.product_id)continue;const r=await restoreOne(p.purchaseToken);if(r.ok&&['active','grace'].includes(r.state))found=true;}
  $('result').textContent=found?'Your Play purchase is restored.':'No active purchase was found for this Play account.';await refresh();
 }catch(e){$('result').textContent=e.message}};
 try{await refresh()}catch(e){$('launchStatus').textContent='Plan information is temporarily unavailable. No purchase has started.';$('result').textContent=e.message}
})();
