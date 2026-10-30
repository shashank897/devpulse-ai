"""Convert official CodeXGLUE parquet splits to DevPulse JSONL without redistribution."""
import json
from pathlib import Path
import pyarrow.parquet as pq

def prepare(directory='data', output='data/devign.jsonl'):
    rows=[]
    for split in ('train','validation','test'):
        path=Path(directory)/f'{split}.parquet'
        table=pq.read_table(path,columns=['func','target','project'])
        for row in table.to_pylist():
            if not row['func'] or row['target'] is None or not row['project']:
                continue
            rows.append({'func':row['func'],'target':int(row['target']),'project':row['project']})
    if not rows: raise ValueError('No usable records. Check that all three parquet files are present.')
    target=Path(output)
    with target.open('w',encoding='utf-8',newline='\n') as stream:
        for row in rows: stream.write(json.dumps(row,ensure_ascii=False)+'\n')
    print(f'Prepared {len(rows):,} examples across {len({r["project"] for r in rows})} projects at {target}.')

if __name__=='__main__': prepare()
