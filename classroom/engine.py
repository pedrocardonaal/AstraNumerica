"""Motor numérico y persistencia de Astro Numérica, edición del semestre."""

from dataclasses import dataclass, asdict, field as datafield

from fractions import Fraction

from pathlib import Path

import ast, math, operator, json, os, tempfile


def number(v, digits=9):
    text = f'{float(v):.{digits}f}'.rstrip('0').rstrip('.')
    return '0' if text in ('', '-0') else text



def parse_number(text):
    text = text.strip().replace('−', '-').replace(',', '.')
    if not text or len(text) > 80: raise ValueError('Escribe un número.')
    result = float(Fraction(text))
    if not math.isfinite(result) or abs(result) > 1e100: raise ValueError('Número fuera de rango.')
    return result



def acceptable(text, expected):
    if isinstance(expected,str):return text.strip().replace('−','-')==expected.replace('−','-')
    try: return abs(parse_number(text)-float(expected)) <= max(0.0000005, abs(float(expected))*0.00000001)+1e-12
    except (ValueError, ZeroDivisionError, OverflowError): return False



@dataclass
class Field:
    label: str
    value: float
    help: str



@dataclass
class Cell:
    index: int



@dataclass
class Sheet:
    title: str
    headers: list
    rows: list



@dataclass
class EquationSheet:
    """Sustitución con fracción vertical; sin introducir variables auxiliares."""
    title: str
    left: str
    numerator: str
    denominator: str
    suffix: str
    result: object = None



@dataclass
class Problem:
    key: str
    method: str
    story: str
    statement: str
    formula: str
    fields: list
    hints: list
    duration: int
    final: float
    table: list
    sheets: list = datafield(default_factory=list)
    initial_layout: str = 'table'
    initial_text: str = ''



def classroom_linear(variant):
    # InterpolaciónLineal.pdf pp. 1–3: datos, sustitución directa, g(x), error.
    # Las dos primeras variantes reproducen los intervalos del ejemplo de Ln 3.
    a,b,x=[(2,5,3),(2,4,3),(3,6,4),(3,5,4),(4,7,5)][variant]
    fa,fb,fx=math.log(a),math.log(b),math.log(x)
    gx=(fb-fa)/(b-a)*(x-a)+fa
    error=abs(fx-gx)
    p=Problem(f'w0-{variant}','Interpolación lineal',
        'Calibra el sensor del motor para abrir la ruta a Helios.',
        f'Estimar el Ln de {x} mediante interpolación lineal entre Ln {a} y Ln {b}. '
        'Sustituye directamente en g(x) y calcula el margen de error ε, como en el ejemplo de clase. '
        'Conserva la precisión de la calculadora; se muestran nueve decimales.',
        '',
        [Field('g(x)',gx,'Sustituye f(b), f(a), b, a y x en la expresión mostrada, respetando los paréntesis.'),
         Field('ε',error,'Calcula el valor absoluto de f(x) − g(x); usa el valor real de Ln x.')],
        ['Identifica a, b, f(a), f(b), x y f(x) en los datos.',
         'Sustituye en g(x) = [(f(b) − f(a)) ÷ (b − a)](x − a) + f(a).',
         f'g(x) está entre {number(gx-.01)} y {number(gx+.01)}. Después calcula ε = |f(x) − g(x)|.'],
        180,gx,[['Dato','Valor'],['a',a],['b',b],
                   [f'f(a) = Ln {a}',number(fa)],[f'f(b) = Ln {b}',number(fb)],
                   ['x',x],[f'f(x) = Ln {x}',number(fx)]])
    p.sheets=[
        EquationSheet('Fórmula','g(x) =','f(b) − f(a)','b − a','(x − a) + f(a)'),
        EquationSheet('Sustitución','g(x) =',f'{number(fb)} − {number(fa)}',
                      f'{b} − {a}',f'({x} − {a}) + {number(fa)}'),
        Sheet('Resultado',['g(x)'],[[Cell(0)]]),
        EquationSheet('Margen de error','ε = |f(x) − g(x)|','','',''),
        Sheet(f'ε = |{number(fx)} − g(x)|',['ε'],[[Cell(1)]])]
    return p



def classroom_divided(variant):
    # NewtonconDiferenciasDivididas.pdf pp. 1–2. Se conservan sus índices y orden.
    xs=[7.3,6.5,6.1];ys=[-.28+variant/10,-1.35+variant/10,-1.96+variant/10];x=7
    h1,h2=abs(xs[1]-xs[0]),abs(xs[2]-xs[1])
    d11=(ys[1]-ys[0])/(xs[1]-xs[0]);d12=(ys[2]-ys[1])/(xs[2]-xs[1])
    d21=(d12-d11)/(xs[2]-xs[0]);g=ys[0]+d11*(x-xs[0])+d21*(x-xs[0])*(x-xs[1])
    p=Problem(f'w3-{variant}','Newton con diferencias divididas',
        'Reconstruye la señal de Vesper a partir de mediciones con intervalos no uniformes.',
        'Encuentre g(x) para x = 7. Obtén h₁ y h₂; construye D¹₁, D¹₂ y D²₁ antes de sustituir en g(x).',
        'g(x) = D⁰ + D¹₁(x − x₁) + D²₁(x − x₁)(x − x₂)',[],
        ['h = |xᵢ₊₁ − xᵢ|. Compara h₁ con h₂: los intervalos no son uniformes.',
         'D¹₁ = (y₂ − y₁) ÷ (x₂ − x₁); D¹₂ = (y₃ − y₂) ÷ (x₃ − x₂).',
         'D²₁ = (D¹₂ − D¹₁) ÷ (x₃ − x₁). D⁰ es y₁. Sustituye después en g(x).'],480,g,
        [['xᵢ','yᵢ']]+[[number(a),number(b)] for a,b in zip(xs,ys)])
    def cell(label,value,help='Realiza la sustitución mostrada y conserva los signos.'):
        p.fields.append(Field(label,value,help));return Cell(len(p.fields)-1)
    p.sheets=[Sheet('Intervalos',['Operación','Resultado'],[
        ['h₁ = |x₂ − x₁| = |6.5 − 7.3|',cell('h₁',h1)],
        ['h₂ = |x₃ − x₂| = |6.1 − 6.5|',cell('h₂',h2)]])]
    for label,num,den,result in [
        ('D¹₁',f'{number(ys[1])} − ({number(ys[0])})','6.5 − 7.3',d11),
        ('D¹₂',f'{number(ys[2])} − ({number(ys[1])})','6.1 − 6.5',d12),
        ('D²₁',f'{number(d12)} − {number(d11)}','6.1 − 7.3',d21)]:
        p.sheets.extend([EquationSheet(label,label+' =',num,den,''),Sheet('Resultado de '+label,[label],[[cell(label,result)]])])
    p.sheets.extend([
        Sheet('Sustitución en g(x)',['Expresión'],[[f'g(x) = ({number(ys[0])}) + ({number(d11)})(7 − 7.3) + ({number(d21)})(7 − 7.3)(7 − 6.5)']]),
        Sheet('Operaciones',['Expresión','Resultado'],[
            ['D¹₁(x − x₁)',cell('D¹₁(x − x₁)',d11*(x-xs[0]))],
            ['D²₁(x − x₁)(x − x₂)',cell('D²₁(x − x₁)(x − x₂)',d21*(x-xs[0])*(x-xs[1]))],
            ['g(x)',cell('g(x)',g)]])])
    return p



def from_key(key):
    family,v=key.split('-');return primary(int(family[1:]),int(v)) if family.startswith('w') else bonus(int(family[1:]),int(v))



def reward(seconds, duration, extra=False, streak=0, penalty=0):
    base=450 if extra else 1000
    speed=round((200 if extra else 400)*max(0,min(1,seconds/duration)))
    combo=min(150,max(0,streak-1)*30)
    return max(0,base+speed+combo-penalty),base,speed,combo



class Storage:
    def __init__(self,directory):
        self.directory=Path(directory);self.path=self.directory/'astro_datos.json';self.error=''
        self.data={'scores':[],'run':None,'sound':True}
        try:
            if self.path.exists():
                raw=json.loads(self.path.read_text(encoding='utf-8'))
                if not isinstance(raw,dict) or not isinstance(raw.get('scores',[]),list):raise ValueError('Formato desconocido')
                self.data.update(raw)
        except (ValueError,OSError) as e:self.error=f'No se pudo leer el guardado: {e}. Se conserva el archivo y no se sobrescribirá hasta confirmar.'
    def save(self):
        if self.error:raise OSError(self.error)
        self.directory.mkdir(parents=True,exist_ok=True)
        fd,name=tempfile.mkstemp(prefix='astro_',suffix='.tmp',dir=self.directory)
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as stream:json.dump(self.data,stream,ensure_ascii=False,indent=2);stream.flush();os.fsync(stream.fileno())
            os.replace(name,self.path)
        finally:
            if os.path.exists(name):os.unlink(name)



def calculate(expression):
    if len(expression)>120:raise ValueError('Expresión demasiado larga.')
    tree=ast.parse(expression.replace('^','**').replace(',','.'),mode='eval')
    ops={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.Pow:operator.pow}
    funcs={'sqrt':math.sqrt,'exp':math.exp,'ln':math.log,'sin':math.sin,'cos':math.cos,'abs':abs}
    def visit(n,depth=0):
        if depth>16:raise ValueError('Expresión demasiado compleja.')
        if isinstance(n,ast.Expression):return visit(n.body,depth+1)
        if isinstance(n,ast.Constant) and type(n.value) in (int,float):v=n.value
        elif isinstance(n,ast.Name) and n.id in ('pi','e'):v=getattr(math,n.id)
        elif isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.UAdd,ast.USub)):v=visit(n.operand,depth+1)*(1 if isinstance(n.op,ast.UAdd) else -1)
        elif isinstance(n,ast.BinOp) and type(n.op) in ops:
            a,b=visit(n.left,depth+1),visit(n.right,depth+1)
            if isinstance(n.op,ast.Pow) and (abs(b)>12 or abs(a)>1e12):raise ValueError('Potencia fuera de rango.')
            v=ops[type(n.op)](a,b)
        elif isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in funcs and len(n.args)==1 and not n.keywords:v=funcs[n.func.id](visit(n.args[0],depth+1))
        else:raise ValueError('Usa números, + − * / ^, sqrt(), exp(), ln(), sin(), cos().')
        if not isinstance(v,(int,float)) or not math.isfinite(v) or abs(v)>1e100:raise ValueError('Resultado fuera de rango.')
        return v
    return visit(tree)



from .curriculum import WORLDS, primary, bonus, event_options, event_name, CATALOG, PlotSheet
VERSION='1.1.0'
