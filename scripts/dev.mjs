import {spawn} from 'node:child_process';
import {existsSync} from 'node:fs';
const python='dashboard-and-letter/backend/.venv/bin/python';
const children=[];
let stopping=false;
function stop(code=0){if(stopping)return;stopping=true;for(const child of children)child.kill('SIGTERM');process.exitCode=code;}
function run(command,args,env=process.env){const child=spawn(command,args,{stdio:'inherit',env});children.push(child);child.on('error',error=>{console.error(error.message);stop(1)});child.on('exit',code=>stop(code??0));return child;}
const port=process.env.COUNTERPART_PORT||'8000';
let running=false;
try{const res=await fetch(`http://127.0.0.1:${port}/health`,{signal:AbortSignal.timeout(1000)});running=res.ok&&(await res.json()).status==='ok';}catch{}
if(!running){
 if(!existsSync(python)){console.error('Dashboard dependencies are missing. Run npm run setup:dashboard first.');process.exit(1);}
 run(python,['-m','uvicorn','counterpart.app:app','--host','127.0.0.1','--port',port],{...process.env,LLM_MODE:process.env.LLM_MODE||'stub'});
}
run(process.execPath,['node_modules/next/dist/bin/next','dev','--webpack','--hostname','127.0.0.1']);
process.on('SIGINT',()=>stop());process.on('SIGTERM',()=>stop());
