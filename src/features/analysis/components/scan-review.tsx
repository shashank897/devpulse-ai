import {ArrowUpRight, Check, ShieldAlert} from 'lucide-react';
import {Card} from '@/components/patterns/card';
import type {Finding, Scan} from '@/types';
import {compareScans, previousRepositoryScan, sourceUrl} from '../scan-utils';

export function ScanReview({scan,scans,onSeverity}:{scan:Scan;scans:Scan[];onSeverity:(severity:string)=>void}) {
  const actionable=(scan.findings??[]).filter(f=>['open','confirmed'].includes(f.status));
  const urgent=actionable.filter(f=>['critical','high'].includes(f.severity)).length;
  const warnings=scan.warnings??[];
  const previous=previousRepositoryScan(scan,scans);
  const comparison=previous?compareScans(scan,previous):null;
  const url=sourceUrl(scan);
  return <div className="review-grid">
    <Card className="review-summary">
      <div className="card-title"><h2>Review summary</h2><span className="tag">{urgent?'Priority findings':warnings.length?'Coverage needs review':actionable.length?'Review needed':'No open findings'}</span></div>
      <p>{urgent?`${urgent} high or critical findings need attention.`:actionable.length?`${actionable.length} findings are open or confirmed.`:'No open findings in the inspected source.'} Check the evidence before changing code.</p>
      <div className="severity-summary" aria-label="Open and confirmed findings by severity">{(['critical','high','medium','low'] as Finding['severity'][]).map(severity=><button key={severity} onClick={()=>onSeverity(severity)} aria-label={`Show ${severity} actionable findings`}><strong>{actionable.filter(f=>f.severity===severity).length}</strong><span className={`severity ${severity}`}>{severity}</span></button>)}</div>
      <p className="small muted">{(scan.findings?.length??0)-actionable.length} marked resolved or false positive. Review status is recorded by you.</p>
    </Card>
    <Card className="scan-coverage">
      <div className="card-title"><h2>What was inspected</h2>{warnings.length?<ShieldAlert size={18}/>:<Check size={18}/>}</div>
      <p><strong>{scan.files?.length??0}</strong> files / cells · <strong>{scan.lines??0}</strong> lines · selected static rules</p>
      <p className="small">{scan.repository?'Public repository snapshot. Preview limits apply.':'Submitted snippet only.'} A low risk score does not confirm safe code.</p>
      {url&&<a className="mono-link" href={url} target="_blank" rel="noreferrer">Commit {scan.commit?.slice(0,7)} <ArrowUpRight size={13}/></a>}
      {warnings.length>0&&<details className="coverage-details" open><summary>{warnings.length} coverage {warnings.length===1?'notice':'notices'}</summary><ul>{warnings.map((warning,i)=><li key={i}>{warning}</li>)}</ul></details>}
    </Card>
    {scan.repository&&<Card className="comparison-card"><div className="card-title"><h2>Since the previous scan</h2><span className="muted small">Same repository</span></div>
      {comparison&&previous?<><p className="small">Compared with {new Date(previous.created_at).toLocaleString()} · {previous.commit?.slice(0,7)||'commit unavailable'}</p><div className="comparison-values"><span><strong>{comparison.added}</strong> Newly reported</span><span><strong>{comparison.repeated}</strong> Reported again</span><span><strong>{comparison.notReported}</strong> No longer reported</span></div><p className="small muted">Compared {comparison.commonFiles} shared files / cells by rule and evidence. Missing findings are not proof of a fix; source edits, redaction, analysis warnings and scan limits can change the comparison.</p></>:<p className="small">{previous?'No shared files or cells were inspected in both scans.':'Rescan this repository to compare with an earlier scan in your history.'}</p>}
    </Card>}
  </div>;
}
