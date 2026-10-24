"""Build and verify a source-only submission archive without modifying inputs."""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    files = [ROOT / 'README.md']
    for path in (ROOT / 'code').rglob('*'):
        if path.is_file() and path.suffix in {'.py', '.md'} and '__pycache__' not in path.parts:
            files.append(path)
    files.append(ROOT / 'code/requirements.txt')
    archive = ROOT / 'code.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as out:
        for path in sorted(files): out.write(path, path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(archive) as check:
        names = set(check.namelist())
        required = {'README.md', 'code/README.md', 'code/main.py', 'code/requirements.txt', 'code/evaluation/evaluation_report.md', 'code/evaluation/usage_report.md', 'code/evaluation/interview_notes.md'}
        if not required <= names: raise ValueError(f'Missing packaged deliverables: {required - names}')
        if check.testzip() is not None: raise ValueError('Archive integrity failure')
        if any(name.startswith('dataset/') or any(part in name for part in ('__pycache__', '.env', '.zip', '.deps', '.cache')) for name in names): raise ValueError('Forbidden archive entry')
    print(f'{archive}: {len(files)} files, {archive.stat().st_size} bytes, verified')


if __name__ == '__main__': main()
