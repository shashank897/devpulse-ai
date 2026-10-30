import {Activity} from 'lucide-react';
import Link from 'next/link';
export function Brand(){return <Link href="/" className="brand" aria-label="DevPulse AI home"><span className="brand-icon"><Activity size={23}/></span><span>DevPulse<span className="brand-ai"> AI</span></span></Link>;}
