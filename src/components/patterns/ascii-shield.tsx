'use client';
import {useEffect,useRef} from 'react';

/** Original projected character artwork; no images or code from the reference. */
export function AsciiShield(){
  const ref=useRef<HTMLCanvasElement>(null);
  useEffect(()=>{
    const canvas=ref.current;if(!canvas)return;
    const context=canvas.getContext('2d');if(!context)return;
    const motion=matchMedia('(prefers-reduced-motion: reduce)');
    let frame=0,last=0,visible=true,time=0,width=520,height=480;
    let pointerX=0,pointerY=0,turnX=0,turnY=0;
    let color='',accent='';
    const colors=()=>{const style=getComputedStyle(document.documentElement);color=style.getPropertyValue('--primary').trim();accent=style.getPropertyValue('--accent').trim();};
    colors();
    const points:{x:number;y:number;z:number;edge:boolean;glyph:string}[]=[];
    for(let row=0;row<45;row++)for(let col=0;col<43;col++){
      const y=row/44*2-1,x=col/42*2-1;
      const span=y<-.45?.82:.82*Math.pow(Math.max(0,1-(y+.45)/1.5),.65);
      if(Math.abs(x)>span)continue;
      const edge=Math.abs(x)>span-.065||row<2;
      points.push({x:x*130,y:y*155,z:Math.cos(x*1.8)*20,edge,glyph:edge?'+':((row*3+col)%7===0?'*':':')});
    }
    const draw=(stamp:number)=>{
      frame=0;
      if(stamp-last<32&&!motion.matches){schedule();return;}last=stamp;
      if(!motion.matches)time+=.022;
      turnX+=(pointerX*.65+Math.sin(time*.22)*.12-turnX)*.055;
      turnY+=(pointerY*.3-turnY)*.055;
      context.clearRect(0,0,width,height);
      const scale=width/520,cx=width/2,cy=height/2;
      context.font=`${9*scale}px ui-monospace, monospace`;context.textAlign='center';
      // Orbital character field echoes the scanner's commit snapshot boundary.
      for(let ring=0;ring<7;ring++)for(let i=0;i<100;i++){
        const angle=i/100*Math.PI*2+time*(ring%2?.012:-.01),radius=(190+ring*8)*scale;
        const x=Math.cos(angle)*radius,y=Math.sin(angle)*radius*.95;
        context.globalAlpha=.1+(i%9===0?.16:0);context.fillStyle=color;
        context.fillText(i%7===0?'+':'.',cx+x,cy+y);
      }
      for(const p of points){
        const x=p.x*Math.cos(turnX)+p.z*Math.sin(turnX),z=-p.x*Math.sin(turnX)+p.z*Math.cos(turnX);
        const y=p.y*Math.cos(turnY)-z*Math.sin(turnY);
        const scan=1-Math.min(1,Math.abs(p.y-((time*60)%360-180))/22);
        context.fillStyle=scan>.3?accent:color;
        context.globalAlpha=(p.edge?.8:.23)+scan*.2;
        const glitch=!motion.matches&&Math.sin(time*.8)>.997&&p.y>15&&p.y<38?Math.sin(stamp*.06)*4:0;
        context.fillText(p.glyph,cx+(x+glitch)*scale,cy+y*scale);
      }
      context.globalAlpha=.85;context.fillStyle=accent;context.font=`${13*scale}px ui-monospace, monospace`;
      const pulse=[[-38,0],[-20,-14],[0,19],[22,-29],[39,0]];
      for(let i=0;i<pulse.length-1;i++){
        const a=pulse[i],b=pulse[i+1],n=12;
        for(let j=0;j<n;j++)context.fillText('·',cx+(a[0]+(b[0]-a[0])*j/n)*scale,cy+(a[1]+(b[1]-a[1])*j/n)*scale);
      }
      context.globalAlpha=1;schedule();
    };
    function schedule(){if(!frame&&visible&&!document.hidden&&!motion.matches)frame=requestAnimationFrame(draw);}
    const resize=()=>{const rect=canvas.getBoundingClientRect();width=rect.width;height=rect.height;const dpr=Math.min(devicePixelRatio||1,1.5);canvas.width=width*dpr;canvas.height=height*dpr;context.setTransform(dpr,0,0,dpr,0,0);cancelAnimationFrame(frame);frame=0;draw(performance.now());};
    const move=(event:PointerEvent)=>{const rect=canvas.getBoundingClientRect();pointerX=(event.clientX-(rect.left+rect.width/2))/innerWidth;pointerY=(event.clientY-(rect.top+rect.height/2))/innerHeight;};
    const observer=new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;if(!visible){cancelAnimationFrame(frame);frame=0;}else schedule();});observer.observe(canvas);
    const sizeObserver=new ResizeObserver(resize);sizeObserver.observe(canvas);
    const themeObserver=new MutationObserver(()=>{colors();if(motion.matches)draw(performance.now());});themeObserver.observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
    const visibility=()=>{if(document.hidden){cancelAnimationFrame(frame);frame=0;}else schedule();};
    const preference=()=>{cancelAnimationFrame(frame);frame=0;draw(performance.now());};
    window.addEventListener('pointermove',move,{passive:true});document.addEventListener('visibilitychange',visibility);motion.addEventListener('change',preference);
    resize();
    return()=>{cancelAnimationFrame(frame);observer.disconnect();sizeObserver.disconnect();themeObserver.disconnect();window.removeEventListener('pointermove',move);document.removeEventListener('visibilitychange',visibility);motion.removeEventListener('change',preference);};
  },[]);
  return <canvas className="ascii-shield" ref={ref} aria-hidden="true"/>;
}
