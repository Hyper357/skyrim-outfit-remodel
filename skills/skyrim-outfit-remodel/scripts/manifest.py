"""Make or verify file hashes under an explicit root; never delete or deploy files."""
import argparse
import hashlib
from pathlib import Path
from audit_mesh import read,write
from audit_bodyslide import relative


IGNORED={'.git','__pycache__','.pytest_cache','.local-validation'}


def files(root,exclude=None):
    root=Path(root).resolve();result={}
    exclude=Path(exclude).resolve() if exclude is not None else None
    for path in sorted(root.rglob('*')):
        rel=path.relative_to(root)
        if any(p in IGNORED for p in rel.parts) or (exclude and path.resolve()==exclude):continue
        if path.is_symlink():raise ValueError('Symlinks need separate ownership review: '+str(rel))
        if not path.is_file():continue
        if not path.resolve().is_relative_to(root):raise ValueError('Resource escapes root')
        result[rel.as_posix()]={'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    return result


def verify(root,manifest,exclude=None):
    expected=manifest['files']
    for name in expected:relative(name)
    actual=files(root,exclude)
    changed=[p for p in expected if p in actual and expected[p]!=actual[p]]
    missing=sorted(set(expected)-set(actual));extra=sorted(set(actual)-set(expected))
    return {'pass':not changed and not missing and not extra,'changed':changed,'missing':missing,'extra':extra}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['make','verify']);p.add_argument('root');p.add_argument('manifest')
    a=p.parse_args();root=Path(a.root).resolve();target=Path(a.manifest).resolve()
    if not root.is_dir():p.error('root must be an existing directory')
    try:
        if a.mode=='make':
            data={'schema':1,'files':files(root,target),'excluded_directory_names':sorted(IGNORED)}
            write(target,data);print({'files':len(data['files'])});return 0
        result=verify(root,read(target),target);print(result);return 0 if result['pass'] else 2
    except (ValueError,OSError,KeyError) as exc:p.exit(2,str(exc)+'\n')


if __name__=='__main__':
    raise SystemExit(main())
