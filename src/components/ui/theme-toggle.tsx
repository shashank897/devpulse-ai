'use client';
import {SunMoon} from 'lucide-react';
export function ThemeToggle(){return <button className="icon-button" aria-label="Switch color theme" onClick={()=>{const theme=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=theme;try{localStorage.setItem('devpulse-theme',theme)}catch{}}}><SunMoon size={19}/></button>;}
