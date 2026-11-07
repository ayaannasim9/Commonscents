import assert from 'node:assert/strict';
const base='http://127.0.0.1:3000';
async function get(path){const r=await fetch(base+path);assert.equal(r.status,200,path);return r;}
assert.equal((await (await get('/api/counterpart/health')).json()).status,'ok');
const personas=await (await get('/api/counterpart/personas')).json();assert.equal(personas.length,6);
for(const p of personas){
 const prefix='/api/counterpart/customers/'+p.id;
 const dashboard=await (await get(prefix+'/dashboard')).json();
 const html=await (await get(prefix+'/letter.html')).text();
 const escaped=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#x27;');
 for(const section of dashboard.sections)assert.ok(html.includes(escaped(section.text)),p.id+' '+section.id);
 const pdf=await get(prefix+'/letter.pdf?preview=true');assert.match(pdf.headers.get('content-type'),/application\/pdf/);assert.equal(Buffer.from(await pdf.arrayBuffer()).subarray(0,4).toString(),'%PDF');
}
const denied=await fetch(base+'/api/counterpart/demo/reset',{method:'POST',headers:{Origin:'https://example.com'}});assert.equal(denied.status,403);
const learning=await (await get('/api/learn')).json();assert.equal(learning.error,null);assert.equal(learning.lessons.filter(l=>l.journey_id==='banking-basics').length,10);
console.log('Passed: shared-origin proxy, six dashboard/letter pairs agree, six PDFs render, cross-origin mutation rejected, learning API retains original banking course.');
