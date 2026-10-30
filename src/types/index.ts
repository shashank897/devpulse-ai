export type Finding = { id:string; rule_id:string; file_path:string; start_line:number; title:string; severity:'critical'|'high'|'medium'|'low'; description:string; suggestion:string; evidence:string; source:string; status:string };
export type FileMetric = {path:string; language:string; lines:number; complexity:number|null; functions:number; findings:number};
export type Scan = {id:string; name:string; status:'queued'|'running'|'completed'|'failed'; created_at:string; findings?:Finding[]; files?:FileMetric[]; risk_score?:number; lines?:number; warnings?:string[]; commit?:string; repository?:string; error?:string; coverage?:string};
export type Capabilities = {static_analysis:boolean; github_public:boolean; github_app:boolean; ai:boolean; ml:boolean; storage:string};
