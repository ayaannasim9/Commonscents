import {spawn} from 'node:child_process';
import {existsSync} from 'node:fs';
const python='dashboard-and-letter/backend/.venv/bin/python';
const children=[];
let stopping=false;
function stop(code=0){if(stopping)return;stopping=true;for(const child of children)child.kill('SIGTERM');process.exitCode=code;}
function run(command,args,env=process.env,cwd=undefined){const child=spawn(command,args,{stdio:'inherit',env,cwd});children.push(child);child.on('error',error=>{console.error(error.message);stop(1)});child.on('exit',code=>stop(code??0));return child;}
const port=process.env.COUNTERPART_PORT||'8000';
let running=false;
try{const res=await fetch(`http://127.0.0.1:${port}/health`,{signal:AbortSignal.timeout(1000)});running=res.ok&&(await res.json()).status==='ok';}catch{}
if(!running){
 if(!existsSync(python)){console.error('Dashboard dependencies are missing. Run npm run setup:dashboard first.');process.exit(1);}
 run(python,['-m','uvicorn','counterpart.app:app','--host','127.0.0.1','--port',port],{...process.env,LLM_MODE:process.env.LLM_MODE||'stub'});
}
// ML engine (forecasts, risk model, reports) on :8001
const mlPort=process.env.ML_PORT||'8001';
let mlRunning=false;
try{const res=await fetch(`http://127.0.0.1:${mlPort}/health`,{signal:AbortSignal.timeout(1000)});mlRunning=res.ok;}catch{}
if(!mlRunning)run('python3',['-m','uvicorn','api:app','--host','127.0.0.1','--port',mlPort],process.env,'ml');
run(process.execPath,['node_modules/next/dist/bin/next','dev','--webpack','--hostname','127.0.0.1']);
process.on('SIGINT',()=>stop());process.on('SIGTERM',()=>stop());
