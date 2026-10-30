import base64
import re
from pathlib import PurePosixPath
import httpx
from .analyzer import LANGUAGES, MAX_BYTES

def repository_files(repository: str):
    match = re.fullmatch(r'(?:https://github\.com/)?([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?', repository.strip())
    if not match: raise ValueError('Enter a public GitHub repository as owner/name.')
    owner, repo = match.groups()
    base = f'https://api.github.com/repos/{owner}/{repo}'
    # Intentionally unauthenticated: this feature cannot access private repositories.
    with httpx.Client(timeout=15, headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'DevPulse-AI'}, follow_redirects=False) as client:
        def get(url):
            r = client.get(url)
            if r.status_code == 403: raise ValueError('GitHub rate limit reached. Try again later or analyze a snippet.')
            if r.status_code == 404: raise ValueError('Repository not found or not public.')
            r.raise_for_status()
            return r.json()
        metadata = get(base)
        commit = get(base + '/commits/' + metadata['default_branch'])['sha']
        tree = get(base + '/git/trees/' + commit + '?recursive=1')
        candidates = [f for f in tree.get('tree', []) if f['type'] == 'blob' and f.get('size', MAX_BYTES+1) <= MAX_BYTES and PurePosixPath(f['path']).suffix in LANGUAGES and not any(p in ('node_modules','vendor','.git','dist','build') for p in PurePosixPath(f['path']).parts)]
        files, warnings = [], []
        if tree.get('truncated'): warnings.append('GitHub truncated the repository tree; discovery is partial.')
        if len(candidates) > 20: warnings.append(f'Preview limit: analyzed the first 20 of {len(candidates)} eligible source files.')
        total = 0
        for entry in candidates[:20]:
            blob = get(base + '/git/blobs/' + entry['sha'])
            content = base64.b64decode(blob.get('content',''), validate=False)
            total += len(content)
            if total > 1_000_000: warnings.append('Stopped at the 1 MB repository budget.'); break
            files.append((entry['path'], LANGUAGES[PurePosixPath(entry['path']).suffix], content.decode('utf-8', errors='replace')))
        if not files: warnings.append('No supported source files were found within the preview limits.')
        return files, commit, warnings
