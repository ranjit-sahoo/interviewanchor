const {launch}=require('./lib.cjs');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await launch(390,844);
 for(const pref of [null,{v:2,accent:'en-US',rate:1.0,voice:'Test US'},{v:2,accent:'en-GB',rate:.8}]){
  const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.evaluateOnNewDocument(p=>{
   localStorage.setItem('ip_voice',JSON.stringify(p));
   window.__spoken=[];window.__recognizers=[];
   window.SpeechSynthesisUtterance=class{constructor(text){this.text=text}};
   Object.defineProperty(window,'speechSynthesis',{value:{cancel(){},getVoices(){return [{name:'Test US',lang:'en-US'}]},speak(u){window.__spoken.push({text:u.text,lang:u.lang,rate:u.rate})}}});
   window.SpeechRecognition=class{constructor(){window.__recognizers.push(this)}start(){}stop(){}};
  },pref);
  await page.goto('http://127.0.0.1:8123/#sessions',{waitUntil:'networkidle0'});
  await page.waitForSelector('[data-role]');await page.click('[data-role]');await page.click('#sessStartBtn');await page.click('#sessShow');
  await page.evaluate(()=>[...document.querySelectorAll('#sessRoot button')].find(e=>e.textContent==='Read it aloud').click());
  await page.evaluate(()=>[...document.querySelectorAll('#sessRoot button')].find(e=>e.textContent==='Speak my answer').click());
  const data=await page.evaluate(()=>({speech:window.__spoken.at(-1),mic:window.__recognizers.at(-1).lang}));
  assert.equal(data.speech.lang,pref?.accent||'en-US');assert.equal(data.mic,pref?.accent||'en-US');assert.equal(data.speech.rate,pref?.rate||1);assert.deepEqual(errors,[]);
  console.log('PASS practice voice settings',JSON.stringify(data));await page.close();
 }
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
