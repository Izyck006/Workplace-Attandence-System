"""Create a server-only archive from an explicit allowlist, without private files."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parents[1]
files = ['Dockerfile', '.dockerignore', 'compose.yaml', 'Caddyfile', 'render.yaml',
         'requirements-server.txt', '.env.example', 'DEPLOYMENT.md', 'start_server.bat',
         'scripts/check_database.py', 'scripts/restore_snapshot.py', 'src/offices.py',
         'src/data/database.py', 'src/data/initial_schema.py', 'src/services/fingerprint.py']
files += [str(path.relative_to(root)) for path in (root / 'src/server').glob('*.py')]
target = root / 'release/server-package.zip'
target.parent.mkdir(exist_ok=True)
with ZipFile(target, 'w', ZIP_DEFLATED) as archive:
    for name in files:
        archive.write(root / name, name)
print(f'Created {target.name}: {len(files)} source/configuration files; no database credentials.')
