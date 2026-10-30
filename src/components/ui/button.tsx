import { ButtonHTMLAttributes } from 'react';
export function Button({className='',variant='secondary',...props}:ButtonHTMLAttributes<HTMLButtonElement>&{variant?:'primary'|'secondary'|'ghost'}) {return <button className={`button ${variant} ${className}`} {...props}/>;}
