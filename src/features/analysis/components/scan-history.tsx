'use client';
import {useState} from 'react';
import {ArrowUpRight, Download, RotateCw, Trash2} from 'lucide-react';
import {Card} from '@/components/patterns/card';
import {Button} from '@/components/ui/button';
import type {Scan} from '@/types';

export function ScanHistory({scans,onOpen,onRescan,onDelete,busy}:{scans:Scan[];onOpen:(scan:Scan)=>void;onRescan:(scan:Scan)=>void;onDelete:(scan:Scan)=>void;busy:boolean}) {
  const [search,setSearch]=useState(''),[status,setStatus]=useState('all');
  const filtered=scans.filter(s=>(status==='all'||s.status===status)&&`${s.name} ${s.repository??''}`.toLowerCase().includes(search.trim().toLowerCase()));
  return <Card className="history-card"><div className="card-title"><div><h2>Your scans</h2><p>Up to 50 recent scans belonging to this browser session.</p></div><span className="tag">{filtered.length} scans</span></div>
    <div className="history-filters"><label>Search history<input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Repository or scan name…"/></label><label>Status<select value={status} onChange={e=>setStatus(e.target.value)}><option value="all">All statuses</option>{['completed','failed','queued','running'].map(s=><option key={s} value={s}>{s}</option>)}</select></label></div>
    {!filtered.length&&<p className="table-empty">{scans.length?'No scans match these filters.':'Your completed and failed scans will appear here.'}</p>}
    {filtered.map(scan=><article className="scan-history-item" key={scan.id}><div className="scan-history-title"><h3>{scan.name}</h3><span className={`tag ${scan.status==='failed'?'text-error':''}`}>{scan.status}</span></div><p className="small muted">{new Date(scan.created_at).toLocaleString()}{scan.commit?` · ${scan.commit.slice(0,7)}`:''}{scan.status==='completed'?` · ${scan.findings?.length??0} findings`:''}</p>{scan.error&&<p className="history-error">{scan.error}</p>}
      <div className="scan-actions">{scan.status==='completed'&&<><Button onClick={()=>onOpen(scan)}>Open results <ArrowUpRight size={14}/></Button><a className="button" href={`/api/v1/scans/${scan.id}/export`}><Download size={14}/> JSON</a></>}{scan.repository&&<Button disabled={busy||['queued','running'].includes(scan.status)} onClick={()=>onRescan(scan)}><RotateCw size={14}/>{scan.status==='failed'?'Retry repository':'Rescan'}</Button>}<Button disabled={busy||['queued','running'].includes(scan.status)} onClick={()=>onDelete(scan)} aria-label={`Delete scan ${scan.name}`}><Trash2 size={14}/> Delete</Button></div>
    </article>)}
  </Card>;
}
