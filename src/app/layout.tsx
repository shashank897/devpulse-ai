import type {Metadata} from 'next';
import {Providers} from './providers';
import '@/styles/tokens.css';
import '@/styles/globals.css';
import '@/styles/scan-site.css';
export const metadata:Metadata={title:'DevPulse AI — Understand your code',description:'Evidence-first code analysis. Explore repository risk, review findings, and ship with a clearer picture.'};
const themeScript=`try{document.documentElement.dataset.theme=localStorage.getItem('devpulse-theme')||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light')}catch{document.documentElement.dataset.theme='dark'}`;
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en" suppressHydrationWarning><head><script dangerouslySetInnerHTML={{__html:themeScript}}/></head><body><a className="skip-link" href="#main">Skip to content</a><Providers>{children}</Providers></body></html>;}
