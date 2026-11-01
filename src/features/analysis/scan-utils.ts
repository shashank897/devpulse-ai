import type {Finding, Scan} from '@/types';

export const severityOrder = {critical:0, high:1, medium:2, low:3};
export function normalizeRepository(value:string) {
  const repo=value.trim().replace(/^https?:\/\/(?:www\.)?github\.com\//i,'').replace(/^(?:www\.)?github\.com\//i,'').replace(/\/$/,'').replace(/\.git$/,'');
  if(!/^[A-Za-z0-9-]+\/[A-Za-z0-9_.-]+$/.test(repo)||['.','..'].includes(repo.split('/')[1]))throw new Error('Enter a public GitHub repository as owner/repository or a GitHub URL.');
  return repo;
}
export function sourceUrl(scan:Scan, finding?:Finding) {
  if(!scan.repository||!scan.commit||! /^[a-f0-9]{40}$/i.test(scan.commit))return null;
  let repo:string;
  try{repo=normalizeRepository(scan.repository);}catch{return null;}
  const base=`https://github.com/${repo}/`;
  if(!finding)return `${base}tree/${scan.commit}`;
  const path=finding.file_path.replace(/::cell-\d+$/,'');
  if(path.split('/').some(part=>part==='..'||part==='.')||path.startsWith('/'))return null;
  const line=finding.file_path.includes('::cell-')?'':`#L${Math.max(1,finding.start_line)}`;
  return `${base}blob/${scan.commit}/${path.split('/').map(encodeURIComponent).join('/')}${line}`;
}
export function filterFindings(findings:Finding[], search:string, severity:string, status:string, file:string, sort:string) {
  const query=search.trim().toLowerCase();
  return findings.filter(f=>(severity==='all'||f.severity===severity)
    &&(status==='all'||(status==='actionable'?['open','confirmed'].includes(f.status):f.status===status))
    &&(file==='all'||f.file_path===file)
    &&`${f.title} ${f.file_path} ${f.rule_id}`.toLowerCase().includes(query))
    .sort((a,b)=>(sort==='severity'?severityOrder[a.severity]-severityOrder[b.severity]:0)
      ||a.file_path.localeCompare(b.file_path)||a.start_line-b.start_line||a.id.localeCompare(b.id));
}
export function previousRepositoryScan(scan:Scan, scans:Scan[]) {
  if(!scan.repository)return undefined;
  const repository=repositoryKey(scan.repository);
  if(!repository)return undefined;
  return scans.filter(s=>s.id!==scan.id&&s.status==='completed'&&repositoryKey(s.repository)===repository
    &&new Date(s.created_at).getTime()<new Date(scan.created_at).getTime())
    .sort((a,b)=>Date.parse(b.created_at)-Date.parse(a.created_at))[0];
}
export function compareScans(current:Scan, previous:Scan) {
  if(!repositoryKey(current.repository)||repositoryKey(current.repository)!==repositoryKey(previous.repository))return null;
  const beforePaths=new Set(previous.files?.map(f=>f.path));
  const commonPaths=new Set(current.files?.filter(f=>beforePaths.has(f.path)).map(f=>f.path));
  if(!commonPaths.size)return null;
  const key=(f:Finding)=>JSON.stringify([f.file_path,f.rule_id,f.evidence.trim()]);
  const remaining=new Map<string,number>();
  for(const f of previous.findings??[])if(commonPaths.has(f.file_path))remaining.set(key(f),(remaining.get(key(f))??0)+1);
  let added=0, repeated=0;
  for(const f of current.findings??[]){
    if(!commonPaths.has(f.file_path))continue;
    const count=remaining.get(key(f))??0;
    if(count){repeated++;remaining.set(key(f),count-1);}else added++;
  }
  return {added,repeated,notReported:[...remaining.values()].reduce((sum,n)=>sum+n,0),commonFiles:commonPaths.size};
}
function repositoryKey(value:string|undefined) {
  try{return value?normalizeRepository(value).toLowerCase():null;}catch{return null;}
}
export function findingsCsv(findings:Finding[]) {
  // Treat spreadsheet formula prefixes as text even when an attacker controls a filename.
  const cell=(value:unknown)=>{const text=String(value??'');return '"'+(/^[\s]*[=+\-@]|^[\t\r\n]/.test(text)?"'"+text:text).replaceAll('"','""')+'"';};
  return [['Rule','Severity','Status','Title','File','Line','Evidence','Suggested remediation'],
    ...findings.map(f=>[f.rule_id,f.severity,f.status,f.title,f.file_path,f.start_line,f.evidence,f.suggestion])]
    .map(row=>row.map(cell).join(',')).join('\r\n');
}
