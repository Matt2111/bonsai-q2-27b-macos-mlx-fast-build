#!/usr/bin/env python3
"""Package a built worker; fail closed on unresolved non-system Mach-O deps."""
import argparse, hashlib, json, os, shutil, subprocess
from pathlib import Path

def run(*args):
    return subprocess.check_output(args, text=True).strip()

def system(path):
    return path.startswith(('/usr/lib/', '/System/Library/'))

def deps(path):
    return [line.strip().split(' (', 1)[0] for line in run('otool', '-L', str(path)).splitlines()[1:]]

def rpaths(path):
    lines = run('otool', '-l', str(path)).splitlines()
    return [lines[i+2].strip().split(' (', 1)[0].removeprefix('path ')
            for i, line in enumerate(lines) if line.strip() == 'cmd LC_RPATH']

def expand(value, loader, executable):
    return value.replace('@loader_path', str(loader.parent)).replace('@executable_path', str(executable.parent))

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('products', type=Path)
p.add_argument('output', type=Path)
p.add_argument('docs', type=Path)
a = p.parse_args()
src, products, out = a.source.resolve(), a.products.resolve(), a.output.resolve()
if out.exists(): raise SystemExit('Output must not already exist')
out.mkdir(parents=True)
exe = products / 'bench-worker'
for name in ('bench-worker', 'mlx.metallib', 'mlx.metallib.fingerprint'):
    shutil.copy2(products / name, out / name)
for item in products.iterdir():
    if item.suffix == '.bundle': shutil.copytree(item, out / item.name, symlinks=False)
# Dependencies retain each original loader's context while traversing. No guessed
# Homebrew or Xcode fallback: unknown @rpath fails rather than making a bad archive.
queue = [(exe, out / 'bench-worker')]
seen = {exe.resolve(): out / 'bench-worker'}
name_owner = {}
for original, packaged in queue:
    for dep in deps(original):
        if system(dep): continue
        if original.suffix == '.dylib' and dep == run('otool', '-D', str(original)).splitlines()[-1]: continue
        if dep.startswith('@rpath/'):
            candidates = [Path(expand(r, original, exe)) / dep[7:] for r in rpaths(original) + rpaths(exe)]
        else:
            candidates = [Path(expand(dep, original, exe))]
        candidates = [c.resolve() for c in candidates if c.is_file()]
        if not candidates: raise SystemExit(f'Unresolved dependency {dep} in {original}')
        resolved = candidates[0]
        if system(str(resolved)):
            subprocess.run(['install_name_tool', '-change', dep, str(resolved), str(packaged)], check=True)
            continue
        if resolved not in seen:
            name = resolved.name
            if name in name_owner and name_owner[name] != resolved:
                raise SystemExit(f'Dylib basename collision: {name}')
            name_owner[name] = resolved
            dest = out / 'lib' / name
            dest.parent.mkdir(exist_ok=True)
            shutil.copy2(resolved, dest)
            seen[resolved] = dest
            queue.append((resolved, dest))
        dest = seen[resolved]
        relative = os.path.relpath(dest, packaged.parent)
        subprocess.run(['install_name_tool', '-change', dep, '@loader_path/' + relative, str(packaged)], check=True)
    if packaged.suffix == '.dylib':
        subprocess.run(['install_name_tool', '-id', '@rpath/' + packaged.name, str(packaged)], check=True)
    for r in rpaths(packaged):
        subprocess.run(['install_name_tool', '-delete_rpath', r, str(packaged)], check=True)
# Copy license/notice evidence with original relative paths, never entire caches.
licenses = out / 'licenses'
licenses.mkdir()
roots = [('source', src), ('dependencies', src / '.build-worker' / 'checkouts')]
for prefix, root in roots:
    for directory, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('reference_weights', 'weights', 'node_modules')]
        for name in files:
            if name.lower().startswith(('license', 'licence', 'notice', 'copying', 'copyright', 'third_party_notices')):
                path = Path(directory) / name
                if path.is_symlink(): continue
                target = licenses / prefix / path.relative_to(root)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
for name in ('Package.resolved', 'mtp-head.manifest.json'):
    shutil.copy2(src / name, out / name)
for name in ('LAUNCH.md', 'provenance.json'):
    shutil.copy2(a.docs / name, out / name)
# Include exact source without Git internals; allows license/source audit.
with (out / 'source.tar').open('wb') as f:
    subprocess.run(['git', '-C', str(src), 'archive', 'HEAD'], stdout=f, check=True)
meta = {'source_sha': run('git', '-C', str(src), 'rev-parse', 'HEAD'),
        'swift': run('swift', '--version'), 'xcode': run('xcodebuild', '-version'),
        'sdk': run('xcrun', '--sdk', 'macosx', '--show-sdk-version'),
        'deployment_target': os.environ.get('MACOSX_DEPLOYMENT_TARGET'),
        'signing': 'ad-hoc; not Developer-ID signed or notarized',
        'gpu_validation': 'NOT PERFORMED; no weights on CI'}
(out / 'BUILD.json').write_text(json.dumps(meta, indent=2) + '\n')
# Scan all Mach-O payload files, including resource contents, not just known libs.
audit = []
for path in sorted(out.rglob('*')):
    if not path.is_file() or path.is_symlink(): continue
    if 'Mach-O' not in run('file', '-b', str(path)): continue
    if 'arm64' not in run('lipo', '-archs', str(path)): raise SystemExit(f'Not arm64: {path}')
    for dep in deps(path):
        if system(dep): continue
        if path.suffix == '.dylib' and dep == '@rpath/' + path.name: continue
        if not dep.startswith('@loader_path/') or not Path(expand(dep, path, out / 'bench-worker')).is_file():
            raise SystemExit(f'Nonportable dependency: {path}: {dep}')
    if rpaths(path): raise SystemExit(f'Unexpected remaining rpaths: {path}')
    audit.append(str(path.relative_to(out)) + '\n' + run('otool', '-L', str(path)) + '\n' + run('otool', '-l', str(path)))
    subprocess.run(['codesign', '--force', '--sign', '-', str(path)], check=True)
    subprocess.run(['codesign', '--verify', '--strict', str(path)], check=True)
(out / 'MACHO-AUDIT.txt').write_text('\n'.join(audit))
# Hash after signing and all metadata writes.
if not (licenses / 'source' / 'LICENSE').is_file(): raise SystemExit('Missing upstream license')
for checkout in (src / '.build-worker' / 'checkouts').iterdir():
    if checkout.is_dir() and not (licenses / 'dependencies' / checkout.name).exists():
        raise SystemExit(f'Missing license evidence for {checkout.name}')
lines = []
for path in sorted(out.rglob('*')):
    if path.is_file():
        lines.append(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + str(path.relative_to(out)))
(out / 'SHA256SUMS').write_text('\n'.join(lines) + '\n')
