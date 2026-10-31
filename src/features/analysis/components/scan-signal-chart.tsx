'use client';
import {useId, useState} from 'react';
import type {Scan} from '@/types';

// A bounded SVG plot avoids a chart runtime, resize observers and animation loops.
export function ScanSignalChart({scans}:{scans:Scan[]}) {
  const titleId=useId();
  const [selectedId,setSelectedId]=useState<string|null>(null);
  const points=[...scans].reverse().map((scan,index,items)=>({
    id:scan.id,
    label:`Scan ${index+1}`,
    name:scan.name,
    risk:scan.risk_score??0,
    x:40+index*500/Math.max(1,items.length-1),
    y:180-Math.max(0,Math.min(100,scan.risk_score??0))*1.6,
  }));
  const selected=points.find(point=>point.id===selectedId)??points.at(-1);
  if(!points.length)return null;
  const line=points.map(point=>`${point.x},${point.y}`).join(' ');
  return <div className="scan-signal-chart">
    <svg viewBox="0 0 560 210" role="group" aria-labelledby={titleId}>
      <title id={titleId}>Risk signals for recent completed scans, from oldest to newest. Values range from 0 to 100.</title>
      {[0,25,50,75,100].map(value=><g key={value} aria-hidden="true">
        <line x1="40" x2="540" y1={180-value*1.6} y2={180-value*1.6} stroke="var(--border)"/>
        <text x="30" y={184-value*1.6} textAnchor="end">{value}</text>
      </g>)}
      <polygon points={`40,180 ${line} ${points.at(-1)!.x},180`} fill="var(--primary-subtle)"/>
      <polyline points={line} fill="none" stroke="var(--primary)" strokeWidth="2" strokeLinejoin="round"/>
      {points.map(point=><g key={point.id} tabIndex={0} role="img"
        aria-label={`${point.label}: ${point.name}, risk signal ${point.risk} out of 100`}
        onFocus={()=>setSelectedId(point.id)} onPointerEnter={()=>setSelectedId(point.id)} onClick={()=>setSelectedId(point.id)}>
        <title>{point.label}: {point.name} — {point.risk}/100</title>
        <circle className="signal-hit-target" cx={point.x} cy={point.y} r="10" fill="transparent"/>
        <circle className="signal-point" cx={point.x} cy={point.y} r={selected?.id===point.id?4:2.5} fill="var(--primary)"/>
      </g>)}
      <text x="40" y="204" aria-hidden="true">Scan 1</text>
      {points.length>1&&<text x="540" y="204" textAnchor="end" aria-hidden="true">Scan {points.length}</text>}
    </svg>
    <p className="signal-value" aria-live="polite">{selected?.label} · {selected?.name}: <strong>{selected?.risk}/100</strong></p>
    <details className="signal-data"><summary>View scan values</summary><div className="table-wrap"><table>
      <caption className="sr-only">Risk signals in chronological order</caption>
      <thead><tr><th scope="col">Scan</th><th scope="col">Name</th><th scope="col">Risk signal</th></tr></thead>
      <tbody>{points.map(point=><tr key={point.id}><th scope="row">{point.label}</th><td>{point.name}</td><td>{point.risk}/100</td></tr>)}</tbody>
    </table></div></details>
  </div>;
}
