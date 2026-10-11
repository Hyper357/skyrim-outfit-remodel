"""Run a prepared BodySlide installation into a NEW isolated stage. Does not configure its input paths."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import time
from audit_bodyslide import relative
from audit_mesh import write


def build(exe,project,preset,stage,expected,trimorphs=False,timeout=180):
    exe=Path(exe).resolve();stage=Path(stage).resolve()
    if not exe.is_file(): raise ValueError('BodySlide executable not found')
    if stage.exists(): raise ValueError('Stage must not exist; refusing existing directory')
    if not expected: raise ValueError('Explicit expected output paths are required')
    outputs=[relative(p) for p in expected]
    stage.mkdir(parents=True);data=stage/'Data';data.mkdir()
    write(stage/'remodel-owner.json',{'purpose':'isolated_bodyslide_build','project':project})
    command=[str(exe),'--build',project,'--targetdir',str(data),'--preset',preset]
    if trimorphs: command.append('--trimorphs')
    started=time.time()
    try:
        run=subprocess.run(command,cwd=exe.parent,capture_output=True,timeout=timeout,check=False)
        (stage/'stdout.log').write_bytes(run.stdout);(stage/'stderr.log').write_bytes(run.stderr)
        code=run.returncode;failure=None
    except subprocess.TimeoutExpired as exc:
        (stage/'stdout.log').write_bytes(exc.stdout or b'');(stage/'stderr.log').write_bytes(exc.stderr or b'')
        code=None;failure='timeout; do not retry identical command without diagnosis'
    files=[];missing=[]
    for rel in outputs:
        target=data/rel
        if not target.is_file() or target.stat().st_size==0: missing.append(str(rel));continue
        files.append({'path':rel.as_posix(),'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
    result={'pass':code==0 and not missing,'command':command,'returncode':code,'failure':failure,
            'missing_or_empty':missing,'outputs':files,'duration_seconds':round(time.time()-started,3),
            'input_environment_verified':'caller_responsibility','mesh_validation':'not_run','game_test':'not_run'}
    write(stage/'build-report.json',result);return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe',required=True);p.add_argument('--project',required=True);p.add_argument('--preset',required=True)
    p.add_argument('--stage',required=True);p.add_argument('--expected',nargs='+',required=True)
    p.add_argument('--trimorphs',action='store_true');p.add_argument('--timeout',type=int,default=180)
    a=p.parse_args()
    if a.timeout<=0:p.error('timeout must be positive')
    try:result=build(a.exe,a.project,a.preset,a.stage,a.expected,a.trimorphs,a.timeout)
    except (ValueError,OSError) as exc:p.exit(2,str(exc)+'\n')
    print({'pass':result['pass'],'outputs':len(result['outputs'])});return 0 if result['pass'] else 2


if __name__=='__main__':
    raise SystemExit(main())
