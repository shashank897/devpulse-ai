'use client';
import {useEffect,useState} from 'react';
import {api} from '@/lib/api';
import {Button} from '@/components/ui/button';

type Category='security'|'performance';
type Suggestion={id:string;title:string;change:string;code:string;note:string};
type Result={category:Category;suggestions:Suggestion[];message:string};

export function CodeOptimizer({code,language,onApply}:{code:string;language:string;onApply:(code:string)=>void}){
  const [category,setCategory]=useState<Category>('security');
  const [result,setResult]=useState<Result|null>(null);
  const [error,setError]=useState('');
  const [busy,setBusy]=useState(false);
  const [applied,setApplied]=useState(false);
  const [previewSource,setPreviewSource]=useState('');
  useEffect(()=>{if(result&&code!==previewSource&&!result.suggestions.some(item=>item.code===code)){setResult(null);setApplied(false);}},[code,result,previewSource]);
  async function suggest(next:Category){
    setCategory(next);setResult(null);setError('');setApplied(false);setBusy(true);
    try{setResult(await api<Result>('/optimize-preview',{method:'POST',body:JSON.stringify({code,language,category:next})}));setPreviewSource(code);}
    catch(e){setError(e instanceof Error?e.message:'Could not prepare a code preview.');}
    finally{setBusy(false);}
  }
  return <section className="optimizer-panel" aria-label="Code suggestions">
    <div className="optimizer-heading"><div><h3>Review code suggestions</h3><p className="small muted">Suggestions are prepared for this snippet only. They are never run or saved.</p></div></div>
    <div className="optimizer-actions"><Button type="button" aria-pressed={category==='security'} onClick={()=>void suggest('security')}>Security suggestion</Button><Button type="button" aria-pressed={category==='performance'} onClick={()=>void suggest('performance')}>Performance suggestion</Button></div>
    {busy&&<p className="small muted" role="status">Preparing preview…</p>}
    {error&&<p className="form-error" role="alert">{error}</p>}
    {result&&<div className="optimizer-result" role="region" aria-label={`${category} suggestion preview`}>
      {result.suggestions.length===0?<p className="small">{result.message}</p>:result.suggestions.map(item=><article key={item.id}>
        <h4>{item.title}</h4><p className="small">{item.change}</p><div className="optimizer-code-grid"><div><strong>Current code</strong><pre>{code}</pre></div><div><strong>Suggested preview</strong><pre>{item.code}</pre></div></div>
        <p className="small muted">{item.note}</p><Button type="button" variant="primary" onClick={()=>{onApply(item.code);setApplied(true);}}>Apply preview to editor</Button>
      </article>)}
      {applied&&<p className="small" role="status">Preview applied to the editor. Review it, then submit the scan when ready.</p>}
    </div>}
  </section>;
}
