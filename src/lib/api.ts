export async function api<T>(path:string, options:RequestInit = {}):Promise<T> {
  const response = await fetch('/api/v1'+path,{...options,headers:{'Content-Type':'application/json',...options.headers},credentials:'same-origin'});
  if (!response.ok) { const body=await response.json().catch(()=>({detail:'The service is unavailable. Please retry.'})); throw new Error(typeof body.detail==='string'?body.detail:'Check the input and try again.'); }
  return response.json();
}
export const sampleCode = `import sqlite3

def find_user(username):
    connection = sqlite3.connect("users.db")
    query = f"SELECT * FROM users WHERE name = '{username}'"
    return connection.execute(query).fetchall()`;
