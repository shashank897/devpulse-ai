import io
import json
import stat
import zipfile
import httpx
import pytest
from backend import github

COMMIT = 'a' * 40


def archive(entries, comment=COMMIT):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as zipped:
        zipped.comment = comment.encode()
        for name, content in entries:
            zipped.writestr(name, content)
    return output.getvalue()


def mock_download(monkeypatch, content=b'', status=200, headers=None):
    requests = []
    def handle(request):
        requests.append(request)
        return httpx.Response(status, content=content, headers=headers)
    original = httpx.Client
    monkeypatch.setattr(github.httpx, 'Client', lambda **kwargs: original(transport=httpx.MockTransport(handle), **kwargs))
    return requests


def test_public_snapshot_uses_no_rest_quota_or_credentials(monkeypatch):
    requests = mock_download(monkeypatch, archive([('repo-HEAD/main.py', 'eval(user)')]))
    monkeypatch.setenv('GITHUB_TOKEN', 'must-not-send-this')
    files, commit, warnings = github.repository_files('https://github.com/owner/repo.git')
    assert files == [('main.py', 'python', 'eval(user)')]
    assert commit == COMMIT and not warnings
    assert len(requests) == 1
    assert str(requests[0].url) == 'https://codeload.github.com/owner/repo/zip/HEAD'
    assert 'authorization' not in requests[0].headers


def test_notebook_cells_exclude_outputs_and_mark_partial_preview():
    notebook = {'cells': [{'cell_type': 'markdown', 'source': ['ignore']}]
                + [{'cell_type': 'code', 'source': ['eval(user)'], 'outputs': [{'text': 'SECRET OUTPUT'}]} for _ in range(25)]}
    files, commit, warnings = github.snapshot_files(archive([('root/model.ipynb', json.dumps(notebook))]))
    assert len(files) == 20 and files[0] == ('model.ipynb::cell-2', 'python', 'eval(user)')
    assert all('SECRET OUTPUT' not in f[2] for f in files)
    assert any('Partial preview' in w for w in warnings)


def test_unsafe_paths_and_links_are_ignored():
    link = zipfile.ZipInfo('root/link.py')
    link.create_system = 3
    link.external_attr = (stat.S_IFLNK | 0o777) << 16
    data = archive([('root/../escape.py', 'bad'), ('/absolute.py', 'bad'),
                    ('root/vendor/a.py', 'bad'), (link, '../secret.py'),
                    ('root/main.py', 'print(1)')])
    files, _, _ = github.snapshot_files(data)
    assert [f[0] for f in files] == ['main.py']


def test_commit_is_required():
    with pytest.raises(ValueError, match='commit identifier'):
        github.snapshot_files(archive([('root/a.py', '')], comment=''))


@pytest.mark.parametrize('status,expected', [(404, 'not public'), (403, 'temporarily restricted'), (429, 'Retry after 60 seconds'), (302, 'unavailable')])
def test_download_errors_are_actionable(monkeypatch, status, expected):
    requests = mock_download(monkeypatch, status=status, headers={'retry-after': '60'})
    with pytest.raises(ValueError, match=expected):
        github.repository_files('owner/repo')
    assert len(requests) == 1


def test_download_budget_is_enforced(monkeypatch):
    mock_download(monkeypatch, b'x' * 101)
    monkeypatch.setattr(github, 'MAX_ARCHIVE_BYTES', 100)
    with pytest.raises(ValueError, match='download limit'):
        github.repository_files('owner/repo')


def test_oversize_source_and_foreign_notebook_are_skipped():
    foreign = json.dumps({'metadata': {'language_info': {'name': 'julia'}}, 'cells': []})
    files, _, warnings = github.snapshot_files(archive([
        ('root/large.py', 'x' * (github.MAX_BYTES + 1)), ('root/model.ipynb', foreign)]))
    assert not files
    assert any('only Python' in w for w in warnings)


@pytest.mark.parametrize('repository', ['https://evil.test/owner/repo', 'owner/..', 'owner/repo?x=1', 'owner/repo/branch'])
def test_repository_validation(repository):
    with pytest.raises(ValueError, match='owner/name'):
        github.repository_files(repository)
