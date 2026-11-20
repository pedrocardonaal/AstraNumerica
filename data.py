"""Guardado local atómico; las revisiones ADMIN nunca llaman a save."""
import json,os,sys,datetime,tempfile,copy,hmac,hashlib
from pathlib import Path

BASE=Path(sys.executable).parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parent
SAVE_PATH=BASE/'astro_fusion_datos_v4.json'
DEFAULT={'records':[],'save':None,'format':'fusion-4'}
_KEY=bytes(b^0x5A for b in b'\x1b\x29\x2e\x28\x35\x77\x1f\x2c\x33\x2d\x34\x37\x23\x6b\x6c\x6b\x6f\x77\x29\x33\x3d\x34')

def _payload(d):
    return {k:v for k,v in d.items() if not k.startswith('_')}

def sign(d):
    """Firma HMAC-SHA256 del contenido (sin campos temporales). Protección básica contra edición manual."""
    raw=json.dumps(_payload(d),sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf-8')
    return hmac.new(_KEY,raw,hashlib.sha256).hexdigest()

def _quarantine(path):
    """El archivo alterado se conserva con otro nombre para no perder evidencia."""
    try:
        target=path.with_name(path.stem+'.alterado'+path.suffix);n=1
        while target.exists():target=path.with_name(f'{path.stem}.alterado{n}{path.suffix}');n+=1
        os.replace(path,target)
    except OSError:pass

def load():
    if sys.platform == 'emscripten':
        try:
            import platform
            raw = platform.window.localStorage.getItem('astronumerica_save_v4')
            if raw:
                d = json.loads(raw)
                sig = d.pop('_sig', None)
                if isinstance(d,dict) and isinstance(d.get('records',[]),list) and isinstance(sig,str) and hmac.compare_digest(sig,sign(d)):
                    d.setdefault('save',None)
                    return d
        except Exception:
            pass
        return copy.deepcopy(DEFAULT)
    try:
        if Path(SAVE_PATH).exists():
            d=json.loads(Path(SAVE_PATH).read_text(encoding='utf-8'))
            if not isinstance(d,dict) or not isinstance(d.get('records',[]),list):raise ValueError('Formato inválido')
            signature=d.pop('_sig',None)
            if not isinstance(signature,str) or not hmac.compare_digest(signature,sign(d)):
                _quarantine(Path(SAVE_PATH))
                fresh=copy.deepcopy(DEFAULT);fresh['_tampered']=True;return fresh
            d.setdefault('records',[]);d.setdefault('save',None);return d
    except (OSError,ValueError) as e:
        d=copy.deepcopy(DEFAULT);d['_load_error']=str(e);return d
    return copy.deepcopy(DEFAULT)
def save(d):
    if sys.platform == 'emscripten':
        try:
            import platform
            out = _payload(d)
            out['_sig'] = sign(d)
            platform.window.localStorage.setItem('astronumerica_save_v4',json.dumps(out,ensure_ascii=False))
            return True
        except Exception:
            return False
    if d.get('_load_error'):return False
    path=Path(SAVE_PATH);name=None
    try:
        path.parent.mkdir(parents=True,exist_ok=True)
        fd,name=tempfile.mkstemp(dir=path.parent,prefix='astro_',suffix='.tmp')
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            out=_payload(d);out['_sig']=sign(d)
            json.dump(out,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
        os.replace(name,path);return True
    except OSError:return False
    finally:
        if name:
            try:Path(name).unlink(missing_ok=True)
            except OSError:pass
def add_record(d,name,points,worlds_completed,hints_used,status,suspect=False):
    d['records'].append({'name':name,'points':points,'worlds':worlds_completed,'hints':hints_used,
         'date':datetime.date.today().isoformat(),'status':status,'suspect':bool(suspect)})
    d['records'].sort(key=lambda r:r['points'],reverse=True);d['records']=d['records'][:15]
def clear_game_save(d):d['save']=None
