import { NextRequest } from 'next/server';

async function proxy(request:NextRequest, context:{params:Promise<{path:string[]}>}) {
  const host=request.headers.get('host');
  if(!host||!/^(127\.0\.0\.1|localhost)(:\d+)?$/.test(host))return new Response('Local prototype only',{status:403});
  if(request.method!=='GET'&&request.headers.get('origin')!==`http://${host}`)return new Response('Invalid request origin',{status:403});
  const {path}=await context.params;
  if(!['customers','cases','personas','demo','health'].includes(path[0])||path.some(segment=>!/^[-a-zA-Z0-9_.]+$/.test(segment)||segment==='..'))return new Response('Not found',{status:404});
  const port=process.env.COUNTERPART_PORT||'8000';
  if(!/^\d{2,5}$/.test(port))return new Response('Invalid local backend port',{status:503});
  try {
    const response=await fetch(`http://127.0.0.1:${port}/${path.map(encodeURIComponent).join('/')}${request.nextUrl.search}`,{
      method:request.method,headers:{'Content-Type':'application/json'},
      body:request.method==='GET'?undefined:await request.text(),cache:'no-store',signal:AbortSignal.timeout(60000),
    });
    return new Response(response.body,{status:response.status,headers:{'Content-Type':response.headers.get('content-type')||'application/json','Cache-Control':'no-store'}});
  } catch { return Response.json({detail:'The dashboard service is not running. Start it with npm run dev:dashboard, then retry.'},{status:503}); }
}
export const GET=proxy;
export const POST=proxy;
