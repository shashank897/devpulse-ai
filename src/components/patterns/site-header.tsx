'use client';
import Link from 'next/link';
import {useState} from 'react';
import {ArrowUpRight, ChevronDown, Github, Menu, X, LayoutDashboard, ShieldAlert, Code2, Clock3, Settings2} from 'lucide-react';
import {useQuery} from '@tanstack/react-query';
import {Brand} from '@/components/ui/brand';
import {ThemeToggle} from '@/components/ui/theme-toggle';
import {api} from '@/lib/api';
import type {Capabilities} from '@/types';

export function SiteHeader({home=false}:{home?:boolean}){
  const [open,setOpen]=useState(false);
  const status=useQuery({queryKey:['capabilities'],queryFn:()=>api<Capabilities>('/capabilities')});
  return <><div className={`repo-status ${status.isError?'service-error':status.data?'service-online':'service-pending'}`}><span><i className="status-dot"/>{status.isError?'ANALYSIS SERVICE UNAVAILABLE':status.data?'ANALYSIS ENGINE ONLINE':'CONNECTING TO ENGINE'}<span className="status-storage"> · {status.data?.storage||'Checking storage'}</span></span><span className="status-promise">READ ONLY · NOTHING INSTALLED · NOTHING EXECUTED <b aria-hidden="true">▓▒░</b></span></div>
    <header className="repo-header"><div className="repo-header-inner"><Brand/><nav className="repo-nav" aria-label="Main navigation"><Link prefetch={false} className={home?'nav-pill current':'nav-pill'} href="/">Scan</Link><Link prefetch={false} href="/workspace/?view=history">Your scans</Link><details className="nav-dropdown"><summary>Learn <ChevronDown size={12}/></summary><div><Link prefetch={false} href="/docs/">Documentation <ArrowUpRight size={13}/></Link><Link prefetch={false} href="/#detection">Detection rules</Link><Link prefetch={false} href="/#questions">Questions & answers</Link></div></details><Link prefetch={false} href="/workspace/">Workspace <ArrowUpRight size={12}/></Link></nav><div className="repo-header-actions"><ThemeToggle/><a className="icon-button github-link" href="https://github.com/shashank897/devpulse-ai" aria-label="DevPulse on GitHub" target="_blank" rel="noreferrer"><Github size={18}/></a><button className="icon-button mobile-menu-button" aria-label={open?'Close menu':'Open menu'} aria-expanded={open} aria-controls="mobile-navigation" onClick={()=>setOpen(!open)}>{open?<X size={20}/>:<Menu size={20}/>}</button></div></div>{open&&<nav id="mobile-navigation" className="mobile-navigation" aria-label="Mobile navigation"><Link prefetch={false} href="/" onClick={()=>setOpen(false)}>Scan a repository</Link><Link prefetch={false} href="/workspace/" onClick={()=>setOpen(false)}>Workspace</Link><Link prefetch={false} href="/workspace/?view=history" onClick={()=>setOpen(false)}>Your scans</Link><Link prefetch={false} href="/docs/">Documentation</Link></nav>}</header></>;
}

export function WorkspaceNav({view}:{view:string}){
  return <nav className="workspace-tabs" aria-label="Workspace navigation">{[{id:'overview',icon:LayoutDashboard,label:'Overview'},{id:'findings',icon:ShieldAlert,label:'Findings'},{id:'files',icon:Code2,label:'Code DNA'},{id:'history',icon:Clock3,label:'Scan history'},{id:'settings',icon:Settings2,label:'Settings'}].map(({id,icon:Icon,label})=><Link prefetch={false} href={`/workspace/?view=${id}`} key={id} className={view===id?'active':''} aria-current={view===id?'page':undefined}><Icon size={15}/>{label}</Link>)}</nav>;
}
