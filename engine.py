"""Adaptador: estética y mapa recibidos; procedimientos del material de clase."""
import random
from friend_stories import STORIES
from dataclasses import dataclass
from classroom import engine as core
from classroom.engine import Cell,Sheet,EquationSheet,PlotSheet

from classroom import reviewed
from classroom.procedure import Expression,Rich,valid
from math_notation import Math,from_expression,boxes as math_boxes
core.primary=reviewed.primary
core.bonus=reviewed.bonus

VERSION='3.6.1'
@dataclass
class B:
    v:object
    index:int
    label:str
    help:str
    role:str='result'

def _box(c,p):
    f=p.fields[c.index]
    if isinstance(f.value,Expression):
        count=[0]
        def make(value):
            count[0]+=1
            return B(value,c.index,f.label+f': dato {count[0]}','Completa el valor dentro de la operación, respetando sus signos.','substitution')
        node=from_expression(f.value.reference,make)
        if p.method in ('Newton hacia adelante','Newton hacia atrás'):
            def factorials(n):
                for child in n.items:factorials(child)
                if n.kind=='fraction' and n.items[1].kind=='box' and n.items[1].box.v==2:
                    n.items[1]=Math('row',[n.items[1],Math('text',text='!')])
            factorials(node)
        return node
    return B(f.value,c.index,f.label,f.help)

def adapt(p):
    def convert(c):
        if isinstance(c,Cell):return _box(c,p)
        if isinstance(c,Rich):return Rich([tuple(convert(x) for x in block) for block in c.blocks])
        return core.number(c) if isinstance(c,(int,float)) else c
    steps=[]
    for s in p.sheets:
        if isinstance(s,Sheet):
            steps.append({'kind':'table','title':s.title,'headers':s.headers,
              'rows':[[convert(c) for c in row] for row in s.rows]})
        elif isinstance(s,Rich):steps.append({'kind':'rich','content':convert(s)})
        elif isinstance(s,EquationSheet):
            steps.append({'kind':'equation','title':s.title,'left':s.left,'numerator':s.numerator,
              'denominator':s.denominator,'suffix':s.suffix,
              'result':_box(s.result,p) if isinstance(s.result,Cell) else None})
        elif isinstance(s,PlotSheet):steps.append({'kind':'plot','title':s.title,'curves':s.curves,'labels':s.labels})
    data={'title':'','headers':p.table[0],'rows':p.table[1:]} if p.initial_layout=='table' else None
    result={'prompt':p.statement,'formula':p.formula,'data':data,'initial_text':p.initial_text,
            'formula_tables':[{'title':'Ecuaciones normales','headers':s.headers,'rows':s.rows} for s in getattr(p,'formula_tables',[])],
            'steps':steps,'hint1':p.hints[0],'hint2':p.hints[1],'hint3':p.hints[2],
            'answer':p.final,'key':p.key,'source':getattr(p,'source',None)}
    for i,b in enumerate(boxes(result)):b.index=i
    return result

def boxes(problem):
    def nested(c):
        if isinstance(c,B):yield c
        elif isinstance(c,Rich):
            for block in c.blocks:
                for item in block[1:]:yield from nested(item)
        elif isinstance(c,Math):yield from math_boxes(c)
    for step in problem['steps']:
        if step['kind']=='table':
            for row in step['rows']:
                for c in row:
                    yield from nested(c)
        elif step['kind']=='rich':yield from nested(step['content'])
        elif step['kind']=='equation' and step.get('result') is not None:yield step['result']

def check_answer(given,correct):return valid(str(given),correct) if isinstance(correct,Expression) else core.acceptable(str(given),correct)
def answer_text(v):return v.reference if isinstance(v,Expression) else v if isinstance(v,str) else core.number(v)
calculate=core.calculate
reward=core.reward

MINUTES={0:5,1:15,2:5,3:10,4:10,5:10,6:10,7:10,8:15,9:15,10:15,
 11:25,12:20,13:20,14:25,15:30,16:30,17:30,18:10,19:15,20:15,
 21:20,22:20,23:10,24:15,25:20,26:25,27:25,28:30,'b4':25,'b5':25,'b6':20}

def mission_time(pid):return MINUTES[SPECS[pid][0]]*60

# Los identificadores de los planetas se conservan para reutilizar sus escenas y sprites.
SPECS={
 'helios':(0,'Helios · El primer salto'), 'selene':(1,'Selene · La cámara orbital'),
 'dif_div':(5,'Faros desiguales'), 'luna':(6,'La luna escondida'), 'newton_atras':(7,'Señal del faro'),
 'ares':(4,'Ares · Corregir la órbita'),'grafico':(2,'Radar de aterrizaje'),
 'bisectriz':(3,'Acotar la distancia'),'meteorito':(8,'Alerta de meteorito'),
 'punto_fijo':(9,'Punto de equilibrio'),'secante':(10,'Distancia segura'),
 'vesper':(11,'Vesper · Equilibrar las turbinas'),'gauss_seidel':(12,'Presión en cadena'),
 'jacobi':(11,'Turbinas gemelas'),
 'nereida':(19,'Nereida · Atravesar el océano'),'triton':(18,'Tritón · Escudo saturado'),
 'io':(20,'Ío · Reactor inestable'),'europa':(21,'Europa · Campo magnético'),'titan':(22,'Titán · Niebla densa'),
 'sonda':(23,'Encélado · Recuperar la señal'),'ganimedes':(26,'Ganímedes · Cometa errante'),
 'euler_mod':(23,'Baliza moribunda'),
 'encelado':(24,'Encélado · Sonda sin energía'),'calisto':(25,'Calisto · Sobrecalentamiento'),
 'mimas':(27,'Mimas · Luna inestable'),'rea':(28,'Rea · Acoplamiento'),
 'baliza':(13,'Oberón · Una baliza desconocida'),'oberon':(14,'Oberón · Trayectoria curva'),
 'mc_cubica':(15,'Cometa ruidoso'),'mc_linfun':(16,'Señal con pulso'),'mc_cuadfun':(17,'Pulsar misteriosa'),
 'montante3':('b4','Frenado triple'),'gauss_jordan':('b5','Cámaras conectadas'),'gauss':('b6','Válvulas del reactor'),
}
FAMILIES=[
 ('helios','Interpolación',['selene','dif_div','luna','newton_atras']),
 ('ares','Ecuaciones no lineales',['grafico','bisectriz','meteorito','punto_fijo','secante']),
 ('vesper','Ecuaciones lineales',['montante3','gauss_jordan','gauss','gauss_seidel','jacobi']),
 ('nereida','Integración',['triton','io','europa','titan']),
 ('sonda','Ecuaciones diferenciales ordinarias',['euler_mod']),
 ('ganimedes','Ecuaciones diferenciales ordinarias',['encelado','calisto','mimas','rea']),
 ('baliza','Mínimos cuadrados',['oberon','mc_cubica','mc_linfun','mc_cuadfun']),
]
PARENT={m:p for p,_,moons in FAMILIES for m in moons}
def destination_name(pid):return _ALL[pid]['name'].split(' · ')[0]
def category_for(pid):
    parent=PARENT.get(pid,pid)
    return next(title for key,title,_ in FAMILIES if key==parent)
def destination_title(pid):return destination_name(pid)+' — '+category_for(pid)
LATE_EVENTS=frozenset({'montante3','gauss_jordan','gauss'})

def problem_for(pid,variant):
    method=SPECS[pid][0]
    if not 0<=variant<5:raise ValueError('Variante fuera del catálogo.')
    if pid in ('euler_mod','euler_revision'):
        from classroom.reviewed import edo
        p=edo(23,variant+(5 if pid=='euler_mod' else 10),'euler')
    elif pid=='jacobi':
        from classroom.reviewed import iterative_system
        p=iterative_system(11,variant+5,False)
    else:p=core.bonus(int(method[1:]),variant) if isinstance(method,str) else core.primary(method,variant)
    if pid in ('euler_mod','euler_revision','jacobi'):
        p.initial_layout='text'
        if pid=='jacobi' and not p.initial_text:p.initial_text='\n'.join(row[0] for row in p.table[1:])
    result=adapt(p);result['variant']=variant;result['mission_id']=pid;return result

def definition(pid):
    method,name=SPECS[pid]
    reference=core.bonus(int(method[1:]),0) if isinstance(method,str) else core.primary(method,0)
    return {'id':pid,'name':name,'method':reference.method,'time':MINUTES[method]*60,
       'story':STORIES.get('jacobi' if pid=='vesper' else 'euler_mod' if pid=='sonda' else pid,reference.story),
       'gen':lambda pid=pid:problem_for(pid,random.randrange(5))}

_ALL={pid:definition(pid) for pid in SPECS}
WORLDS=[_ALL[p] for p,_,_ in FAMILIES]
EVENTS=[_ALL[m] for _,_,moons in FAMILIES for m in moons]
ORDER=[pid for p,_,moons in FAMILIES for pid in [p,*moons]]
assert len(WORLDS)==7 and len(EVENTS)==27 and len(ORDER)==len(set(ORDER))==34

def unlocked(pid,completed):return True
