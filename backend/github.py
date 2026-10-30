"""Read bounded public GitHub snapshots without spending REST API quota."""
import io
import json
import re
import stat
import time
import zipfile
from pathlib import PurePosixPath

import httpx
from .analyzer import LANGUAGES, MAX_BYTES

MAX_ARCHIVE_BYTES = 8_000_000
MAX_NOTEBOOK_BYTES = 2_000_000
MAX_TOTAL_BYTES = 1_000_000
MAX_FILES = 20
EXCLUDED = {'node_modules', 'vendor', '.git', 'dist', 'build', '.venv', '__pycache__'}


def repository_files(repository: str):
    match = re.fullmatch(r'(?:https://github\.com/)?([A-Za-z0-9-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?', repository.strip())
    if not match or match[2] in ('.', '..'):
        raise ValueError('Enter a public GitHub repository as owner/name.')
    owner, repo = match.groups()
    # No credentials, redirects, extraction, or repository code execution.
    address = f'https://codeload.github.com/{owner}/{repo}/zip/HEAD'
    data = bytearray()
    started = time.monotonic()
    with httpx.Client(timeout=20, follow_redirects=False, headers={'User-Agent': 'DevPulse-AI'}) as client:
        with client.stream('GET', address) as response:
            if response.status_code == 404:
                raise ValueError('Repository not found, empty, or not public. Check owner/name.')
            if response.status_code in (403, 429):
                retry = response.headers.get('retry-after', '')
                wait = f' Retry after {retry} seconds.' if retry.isdigit() else ' Try again later.'
                raise ValueError('GitHub temporarily restricted public downloads.' + wait)
            if response.status_code != 200:
                raise ValueError('GitHub snapshot is unavailable. Check the repository name and retry.')
            length = response.headers.get('content-length', '')
            if length.isdigit() and int(length) > MAX_ARCHIVE_BYTES:
                raise ValueError('Repository snapshot exceeds the 8 MB download limit. Analyze a snippet from this repository.')
            for chunk in response.iter_bytes(chunk_size=65536):
                if len(data) + len(chunk) > MAX_ARCHIVE_BYTES:
                    raise ValueError('Repository snapshot exceeds the 8 MB download limit. Analyze a snippet from this repository.')
                if time.monotonic() - started > 60:
                    raise ValueError('GitHub snapshot download timed out. Try again later.')
                data.extend(chunk)
    try:
        return snapshot_files(data)
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError) as exc:
        raise ValueError('GitHub returned an unreadable repository snapshot. Retry later.') from exc


def snapshot_files(data):
    files, warnings = [], []
    total = 0
    inspected = 0
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        commit = archive.comment.decode('ascii', errors='replace')
        if not re.fullmatch(r'[0-9a-f]{40}', commit):
            raise ValueError('GitHub snapshot did not include a verifiable commit identifier.')
        entries = archive.infolist()
        if len(entries) > 10000:
            raise ValueError('Repository contains too many entries for the public preview. Analyze a snippet.')
        limited = False

        def add(path, language, content):
            nonlocal total, limited
            size = len(content.encode('utf-8'))
            if len(files) >= MAX_FILES or total + size > MAX_TOTAL_BYTES:
                limited = True
                return
            if size > MAX_BYTES:
                warnings.append(f'Skipped {path}: source exceeds 100 KB.')
                return
            files.append((path, language, content))
            total += size

        for entry in sorted(entries, key=lambda e: e.filename):
            path = PurePosixPath(entry.filename)
            mode = entry.external_attr >> 16
            if entry.is_dir() or stat.S_ISLNK(mode) or entry.flag_bits & 1:
                continue
            if path.is_absolute() or '..' in path.parts or '\\' in entry.filename or len(path.parts) < 2:
                continue
            path = PurePosixPath(*path.parts[1:])
            if any(part in EXCLUDED for part in path.parts):
                continue
            notebook = path.suffix == '.ipynb'
            if path.suffix not in LANGUAGES and not notebook:
                continue
            if len(files) >= MAX_FILES:
                limited = True
                break
            budget = MAX_NOTEBOOK_BYTES if notebook else MAX_BYTES
            if entry.file_size > budget:
                warnings.append(f'Skipped {path}: exceeds the {budget // 1000} KB file limit.')
                continue
            if inspected + entry.file_size > MAX_ARCHIVE_BYTES:
                warnings.append('Partial preview: reached the 8 MB decompressed inspection budget.')
                break
            with archive.open(entry) as stream:
                content = stream.read(budget + 1)
            inspected += len(content)
            if len(content) > budget:
                warnings.append(f'Skipped {path}: decompressed file exceeds its size limit.')
                continue
            if not notebook:
                add(str(path), LANGUAGES[path.suffix], content.decode('utf-8', errors='replace'))
                continue
            try:
                document = json.loads(content)
                metadata = document.get('metadata') or {}
                language = ((metadata.get('language_info') or {}).get('name')
                            or (metadata.get('kernelspec') or {}).get('language') or 'python')
                if str(language).lower() not in ('python', 'python3'):
                    warnings.append(f'Skipped {path}: only Python notebooks are supported.')
                    continue
                for number, cell in enumerate(document.get('cells', []), 1):
                    if len(files) >= MAX_FILES:
                        limited = True
                        break
                    if cell.get('cell_type') != 'code':
                        continue
                    source = cell.get('source', '')
                    if isinstance(source, list):
                        source = ''.join(source)
                    if not isinstance(source, str) or not source.strip():
                        continue
                    add(f'{path}::cell-{number}', 'python', source)
                warnings.append(f'{path}: analyzed code cells only; notebook outputs were excluded. IPython magics may be unsupported.')
            except (ValueError, TypeError, AttributeError):
                warnings.append(f'Skipped {path}: invalid notebook structure.')
        if limited:
            warnings.append('Partial preview: limited to 20 source files/notebook cells and 1 MB of source.')
        if not files:
            warnings.append('No supported source files or Python notebook code cells were found within the preview limits.')
    return files, commit, warnings
