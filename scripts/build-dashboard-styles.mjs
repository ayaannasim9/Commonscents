import fs from 'node:fs';
import postcss from 'postcss';
const files=['tokens','base','shell','dashboard','screens'];
let out='/* Generated scoped styles from dashboard-and-letter. Run npm run styles:dashboard to refresh. */\n';
for(const name of files){
 const root=postcss.parse(fs.readFileSync(`dashboard-and-letter/frontend/src/styles/${name}.css`,'utf8'));
 root.walkAtRules('font-face',rule=>rule.remove());
 root.walkRules(rule=>{
  if(rule.parent?.type==='atrule'&&rule.parent.name.includes('keyframes'))return;
  rule.selectors=rule.selectors.map(selector=>{
   if(selector.startsWith(':root'))return selector.replace(':root','.counterpart');
   if(selector==='body'||selector==='html')return '.counterpart';
   return `.counterpart ${selector}`;
  });
 });out+=root.toString()+'\n';
}
out+=fs.readFileSync('app/dashboard-theme.css','utf8');
fs.writeFileSync('app/dashboard-integrated.css',out);
