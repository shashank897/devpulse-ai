import {Suspense} from 'react';
import {Workspace} from '@/features/analysis/components/workspace';
export default function Page(){return <Suspense fallback={<main id="main" className="loading-page">Loading workspace…</main>}><Workspace/></Suspense>;}
