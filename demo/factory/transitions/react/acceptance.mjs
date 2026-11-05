import test from 'node:test';
import assert from 'node:assert/strict';
import {chromium} from 'playwright';
const origin='http://127.0.0.1:8080';
test('production React shell, local assets, health and deep links',async()=>{
 assert.equal((await fetch(origin+'/healthz',{signal:AbortSignal.timeout(3000)})).status,200);
 const browser=await chromium.launch({headless:true,channel:'chromium',chromiumSandbox:true});
 try {
  const page=await browser.newPage();const external=[],errors=[];
  page.on('request',r=>{if(!r.url().startsWith(origin+'/')&&!r.url().startsWith('data:'))external.push(1)});
  page.on('pageerror',()=>errors.push(1));
  assert.equal((await page.goto(origin+'/',{waitUntil:'networkidle',timeout:15000})).status(),200);
  assert.ok(await page.locator('#root').innerText());
  assert.ok(await page.locator('main').count());
  assert.ok((await page.locator('script[src]').evaluateAll(xs=>xs.map(x=>x.src))).some(x=>/\/assets\/.+[-.][A-Za-z0-9_-]+\.js/.test(x)));
  assert.equal((await page.goto(origin+'/browser-deep-link-probe',{waitUntil:'networkidle',timeout:15000})).status(),200);
  assert.ok(await page.locator('#root').innerText());
  assert.equal(external.length,0);assert.equal(errors.length,0);
 }finally{await browser.close()}
});
