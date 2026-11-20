"""Hojas revisadas contra las 53 páginas del material de clase.

Se conservan las tablas y las letras de cada referencia. Los números del
desarrollo se guardan exclusivamente en la solución de ADMIN, nunca como datos.
"""
import math
import re
from .engine import Problem,Field,Cell,Sheet,number
from .curriculum import CATALOG,SOURCES,PlotSheet,sub
from .procedure import Expression,Rich,numeric

FULL_NAMES={
 0:'Interpolación lineal',1:'Lagrange',2:'Método gráfico',3:'Método de la bisectriz',
 4:'Método Newton Raphson',5:'Newton con diferencias divididas',6:'Newton hacia adelante',
 7:'Newton hacia atrás',8:'Método de la falsa posición o Regula Falsi',
 9:'Punto fijo o sustituciones sucesivas',10:'Secante',11:'Jacobi',12:'Gauss-Seidel',
 13:'Línea recta',14:'Cuadrática',15:'Cúbica',16:'Lineal con función',17:'Cuadrática con función',
 18:'Regla trapezoidal',19:'Regla de 1/3 Simpson',20:'Regla de 3/8 Simpson',
 21:'Newton-Cotes cerradas',22:'Newton-Cotes abiertas',23:'Euler modificado',
 24:'Runge-Kutta de 2º orden',25:'Runge-Kutta de 3er. orden',
 26:'Runge-Kutta de 4to. orden por 1/3 de Simpson',
 27:'Runge-Kutta de 4to. orden por 3/8 de Simpson',28:'Runge-Kutta de orden superior'}
f=lambda x:number(x,9)
q=lambda x:'('+f(x)+')'

class Builder:
    def __init__(self,w,v,statement,formula,table=None):
        c=CATALOG[w]
        self.p=Problem(f'w{w}-{v}',FULL_NAMES[w],'Resuelve el problema con el procedimiento de clase.',
          statement,formula,[],[
          'Escribe la sustitución con los datos del enunciado y después calcula su resultado.',
          'Conserva los valores intermedios de tu calculadora. En las casillas de desarrollo se escribe la operación, no solo su resultado.',
          'Comprueba signos, paréntesis, índices y el criterio de terminación indicado.'],c[3],0,
          table or [['Dato','Valor']],[], 'table' if table else 'text','')
        self.p.source=SOURCES[c[0]]
    def cell(self,label,value):
        help=('Escribe la sustitución completa. Usa * para multiplicar, / para dividir, ^ para potencias y abs(...) para valor absoluto.'
              if isinstance(value,Expression) else 'Calcula este valor a partir de tu desarrollo; conserva por lo menos seis decimales si los necesita.')
        self.p.fields.append(Field(label,value,help));return Cell(len(self.p.fields)-1)
    def expr(self,label,expression,variables=()):return self.cell(label,Expression(expression,tuple(variables)))
    def result(self,label,expression,value=None):
        return Rich([('text',label+' ='),('input',self.expr(label+': sustitución',expression)),
                     ('label','=',self.cell(label,numeric(expression) if value is None else value))])
    def frac(self,label,num,den,value=None,left=None):
        blocks=[('text',label+' =')] if left is None else [('lead',label+' =',self.cell(label+': x anterior',left),'−')]
        blocks.append(('fraction',self.expr(label+': numerador',num),self.expr(label+': denominador',den)))
        blocks.append(('label','=',self.cell(label,numeric(num)/numeric(den) if value is None else value)))
        return Rich(blocks)
    def line(self,rich):self.p.sheets.append(rich)
    def calc(self,label,expression,value=None):
        self.line(self.result(label,expression,value));return numeric(expression) if value is None else value
    def note(self,text):self.line(Rich([('text',text)]))
    def finish(self,value):
        self.p.final=float(value)
        # El tiempo incluye escribir el desarrollo completo, no solo calcular.
        self.p.duration=max(self.p.duration,min(3600,180+len(self.p.fields)*20))
        self.p.hints[0]=self.p.formula
        width=max(.01,abs(value)*.01)
        self.p.hints[2]=f'El resultado final está entre {f(value-width)} y {f(value+width)}. Completa también el desarrollo.'
        return self.p

def interpolation(w,v):
    if w==0:
        a,b,x=[(1.5,3.5,2.3),(2,4.5,3.2),(1.8,4.2,2.7),(2.5,5,3.6),(3,6.5,4.1)][v]
        B=Builder(w,v,f'Estima ln({f(x)}) mediante interpolación lineal entre a = {f(a)} y b = {f(b)}. Calcula g(x) y ε.',
          'g(x) = [(f(b) − f(a))/(b − a)](x − a) + f(a)\nε = |f(x) − g(x)|; f(x) = ln(x)')
        fa=math.log(a);fb=math.log(b);true=math.log(x);g=(fb-fa)/(b-a)*(x-a)+fa
        B.calc('f(a)',f'ln({f(a)})',fa);B.calc('f(b)',f'ln({f(b)})',fb);B.calc('f(x)',f'ln({f(x)})',true)
        B.calc('g(x)',f'({q(fb)}-{q(fa)})/({f(b)}-{f(a)})*({f(x)}-{f(a)})+{q(fa)}',g)
        B.calc('ε',f'abs({q(true)}-{q(g)})',abs(true-g));return B.finish(g)
    if w==1:
        xs=[1.2,1.7,2.5,3.1];ys=[round(1+.8*x-.15*x*x+.07*x**3+v*.08,5) for x in xs];x=2.1+v*.1
        B=Builder(w,v,f'Obtener g(x) para x = {f(x)} con los cuatro datos. Los intervalos no son uniformes.',
          'g(x) = Σ yᵢ Πⱼ≠ᵢ [(x − xⱼ)/(xᵢ − xⱼ)]', [['xᵢ','yᵢ']]+list(map(list,zip(xs,ys))))
        # Desarrollo de la suma de productos de Lagrange, sin tablas de factores ajenas al PDF.
        terms=[]
        for i in range(4):
            num=f(ys[i])+'*'+'*'.join(f'({f(x)}-{f(xs[j])})' for j in range(4) if j!=i)
            den='*'.join(f'({f(xs[i])}-{f(xs[j])})' for j in range(4) if j!=i)
            z=numeric(num)/numeric(den);terms.append(z)
            factors='*'.join(f'({f(x)}-{f(xs[j])})' for j in range(4) if j!=i)
            B.calc(f'g(x): término con y{sub(i+1)}',f'{q(ys[i])}*(({factors})/({den}))',z)
        g=sum(terms);B.calc('g(x)','+'.join(q(z) for z in terms),g);return B.finish(g)
    divided=w==5;back=w==7
    # Se mantienen tres puntos como los ejemplos; se evita la parábola elemental x².
    xs=[7.3,6.5,6.1] if divided else [1.7,2.4,3.1]
    ys=([-.28+v*.06,-1.35+v*.04,-1.96+v*.09] if divided else [.35+v*.07,.87+v*.03,1.03+v*.08])
    x=7-v*.05 if divided else 2.85-v*.08
    symbol='D' if divided else '∇' if back else 'Δ'
    formula=('D⁰ + D¹₁(x − x₁) + D²₁(x − x₁)(x − x₂)' if divided else
       f'yᵢ + {symbol}¹f(xᵢ)s + {symbol}²f(xᵢ)s(s{"+" if back else "−"}1)/2!')
    B=Builder(w,v,f'Obtener g(x) para x = {f(x)}. Obtén h y verifica los intervalos antes de aplicar el método.',
      'h = |xᵢ₊₁ − xᵢ|\ng(x) = '+formula+('' if divided else '\ns = (x − xᵢ)/h'),
      [['xᵢ','yᵢ']]+[[f(xx),f(yy)] for xx,yy in zip(xs,ys)])
    for i in range(2):B.calc('h'+sub(i+1),f'abs({f(xs[i+1])}-{f(xs[i])})')
    d1=[(ys[i+1]-ys[i])/(xs[i+1]-xs[i]) if divided else ys[i+1]-ys[i] for i in range(2)]
    d2=(d1[1]-d1[0])/(xs[2]-xs[0]) if divided else d1[1]-d1[0]
    rows=[]
    for i in range(3):
        row=[f'x{sub(i+1)} = {f(xs[i])}',f'y{sub(i+1)} = {f(ys[i])}']
        index=i-1 if back else i
        if 0<=index<2:
            n=f'{q(ys[index+1])}-{q(ys[index])}'
            rich=B.frac(f'D¹{sub(index+1)}',n,f'{f(xs[index+1])}-{f(xs[index])}',d1[index]) if divided else B.result(f'{symbol}¹{sub(index+1)}',n,d1[index])
            row.append(rich)
        else:row.append('')
        if i==(2 if back else 0):
            n=f'{q(d1[1])}-{q(d1[0])}'
            row.append(B.frac('D²₁',n,f'{f(xs[2])}-{f(xs[0])}',d2) if divided else B.result(f'{symbol}²₁',n,d2))
        else:row.append('')
        rows.append(row)
    B.p.sheets.append(Sheet('', ['xᵢ','yᵢ; D⁰' if divided else 'yᵢ',f'{symbol}¹f(xᵢ)',f'{symbol}²f(xᵢ)'],rows))
    if divided:
        expr=f'{q(ys[0])}+{q(d1[0])}*({f(x)}-{f(xs[0])})+{q(d2)}*({f(x)}-{f(xs[0])})*({f(x)}-{f(xs[1])})'
    else:
        ref=2 if back else 0;h=xs[1]-xs[0];s=(x-xs[ref])/h
        B.line(B.frac('s',f'{f(x)}-{f(xs[ref])}',f(h),s))
        B.line(Rich([('binomial','s','0','= 1'),('binomial','s','1','= s')]))
        coef=f'{q(s)}*({q(s)}{"+" if back else "-"}1)/2'
        B.line(Rich([('binomial','s','2','='),('input',B.expr('Coeficiente binomial: sustitución',coef)),('label','=',B.cell('Coeficiente binomial',numeric(coef)))]))
        expr=f'{q(ys[ref])}*1+{q(d1[-1] if back else d1[0])}*{q(s)}+{q(d2)}*{q(s)}*({q(s)}{"+" if back else "-"}1)/2'
    g=numeric(expr);B.calc('g(x)',expr,g);return B.finish(g)

def roots(w,v,kind):
    if kind in ('fijo','secante'):
        c=1+v*.1
        fx=lambda x:math.exp(-x)-c*x
        function='exp(-x)-x' if c==1 else f'exp(-x)-{f(c)}*x'
        shown='e⁻ˣ − x' if c==1 else f'e⁻ˣ − {f(c)}x'
    elif kind=='bisectriz':
        c=6.5+v*.25
        fx=lambda x:x**3-c*x+2
        function=f'x^3-{f(c)}*x+2'
        shown=f'x³ − {f(c)}x + 2'
    else:
        c=3+v
        fx=lambda x:x**3+2*x*x+10*x-(17+v*3)
        function=f'x^3+2*x^2+10*x-{17+v*3}'
        shown=f'x³ + 2x² + 10x − {17+v*3}'
    tol=.00001 if kind in ('nr','fijo') else .001
    generic={'grafico':'f(x) = 0; el cambio de signo permite localizar un cruce del eje x.',
      'bisectriz':'x = (a + b)/2; ε = |xᵢ₊₁ − xᵢ|',
      'nr':'xᵢ₊₁ = xᵢ − f(xᵢ)/f′(xᵢ); ε = |xᵢ₊₁ − xᵢ|',
      'fijo':f'xᵢ₊₁ = g(xᵢ) = e^(−xᵢ)/{f(c)}; ε = |xᵢ₊₁ − xᵢ|',
      'secante':'xᵢ₊₂ = xᵢ₊₁ − f(xᵢ₊₁)(xᵢ₊₁ − xᵢ)/[f(xᵢ₊₁) − f(xᵢ)]; ε = |xᵢ₊₁ − xᵢ|',
      'falsa':'x = a − f(a)(b − a)/[f(b) − f(a)]; ε = |xᵢ₊₁ − xᵢ|'}[kind]
    statement=f'Encuentra una raíz positiva de f(x) = {shown}.'
    if kind in ('nr','fijo'):statement+=' Continúa hasta que el error comience con 0.00000… (ε < 0.00001).'
    elif kind!='grafico':statement+=f' Termina cuando ε ≤ {f(tol)}.'
    if kind=='nr':statement+=' Usa x₀ = 1 como aproximación inicial, como en el ejemplo de clase. Calcula primero f′(x).'
    elif kind=='fijo':statement+=' Usa x₀ = 0, como valor inicial de la sucesión. Primero despeja x.'
    elif kind=='secante':statement+=' Usa los dos valores iniciales x₀ = 0 y x₁ = 1.'
    elif kind=='bisectriz':statement+=' Usa a = 0 y b = 1. Localiza la raíz de este intervalo y verifica el cambio de signo.'
    elif kind=='falsa':statement+=' Usa a = 1 y b = 2. Verifica el cambio de signo.'
    B=Builder(w,v,statement,generic)
    at=lambda x:re.sub(r'\bx\b',q(x),function)
    if kind=='grafico':
        rows=[[x,B.result('y',at(x),fx(x))] for x in (0,1,2,3)]
        B.p.sheets.append(Sheet('', ['x','y'],rows))
        B.line(Rich([('label','a =',B.cell('a',1)),('label','b =',B.cell('b',2))]))
        B.p.sheets.append(PlotSheet('Gráfica de la función',[[(i/40,fx(i/40)) for i in range(121)]],['f(x)']))
        left,right=1.,2.
        for _ in range(60):
            middle=(left+right)/2
            if fx(middle)>0:right=middle
            else:left=middle
        return B.finish((left+right)/2)
    if kind=='nr':
        B.line(Rich([('text','f′(x) ='),('input',B.expr('f′(x)','3*x^2+4*x+10',('x',)))]))
        rows=[[0,'x₀ = 1','—']];old=1.
        for i in range(1,20):
            new=old-fx(old)/(3*old*old+4*old+10);err=abs(new-old)
            development=B.frac(f'x{sub(i)}',at(old),f'3*{q(old)}^2+4*{q(old)}+10',new,left=old)
            previous='x'+sub(i-1)
            development.blocks[:0]=[('text',f'x{sub(i)} = {previous} −'),
                ('mathfraction',f'f({previous})',f'f′({previous})')]
            rows.append([i,development,B.result(f'|x{sub(i)} − x{sub(i-1)}|',f'abs({q(new)}-{q(old)})',err)])
            if err<tol:break
            old=new
        B.p.sheets.append(Sheet('', ['i','xᵢ₊₁','ε = |xᵢ₊₁ − xᵢ|'],rows));return B.finish(new)
    if kind=='fijo':
        B.line(Rich([('text','Despejar x: x ='),('input',B.expr('Despeje de x','exp(-x)' if c==1 else f'exp(-x)/{f(c)}',('x',)))]))
        rows=[[0,'—',0,'—']];old=0.
        for i in range(1,80):
            new=math.exp(-old)/c;err=abs(new-old)
            rows.append([i,B.expr(f'e⁻ˣ; i={i}',f'exp(-{q(old)})'+('' if c==1 else f'/{f(c)}')),B.cell('x'+sub(i),new),
               '—' if i==1 else B.result('ε',f'abs({q(new)}-{q(old)})',err)])
            if err<tol:break
            old=new
        B.p.sheets.append(Sheet('', ['i','e⁻ˣ'+('' if c==1 else f'/{f(c)}'),'xᵢ','ε = |xᵢ₊₁ − xᵢ|'],rows));return B.finish(new)
    if kind=='secante':
        old=0.;now=1.;evalrows=[[f'x₀ = 0',B.result('f(x₀)',at(old),fx(old))],[f'x₁ = 1',B.result('f(x₁)',at(now),fx(now))]]
        B.p.sheets.append(Sheet('', ['x','f(x)'],evalrows))
        rows=[[0,'x₀ = 0','—'],[1,'x₁ = 1',B.result('ε','abs(1-0)',1)]]
        for i in range(2,25):
            new=now-fx(now)*(now-old)/(fx(now)-fx(old));err=abs(new-now)
            rows.append([i,B.frac('x'+sub(i),f'{q(fx(now))}*({q(now)}-{q(old)})',f'{q(fx(now))}-{q(fx(old))}',new,left=now),B.result('ε',f'abs({q(new)}-{q(now)})',err)])
            if err<=tol:break
            evalrows.append([Rich([('label','x'+sub(i)+' =',B.cell('x'+sub(i)+' en f(x)',new))]),B.result('f(x'+sub(i)+')',at(new),fx(new))])
            old,now=now,new
        B.p.sheets.append(Sheet('', ['i','xᵢ₊₁','|xᵢ₊₁ − xᵢ|'],rows));return B.finish(new)
    # La falsa posición conserva b en estos problemas (f creciente y convexa).
    a=0. if kind=='bisectriz' else 1.;b=1. if kind=='bisectriz' else 2.;old=None;rows=[]
    B.p.sheets.append(Sheet('', ['x','f(x)'],[[a,B.result('f(a)',at(a),fx(a))],[b,B.result('f(b)',at(b),fx(b))]]))
    if kind=='falsa':rows.append([0,2,B.cell('f(b)',fx(2)),1,'—',B.cell('f(a)',fx(1)),'—'])
    for i in range(1,80):
        new=(a+b)/2 if kind=='bisectriz' else a-fx(a)*(b-a)/(fx(b)-fx(a))
        err=None if old is None else abs(new-old)
        if kind=='bisectriz':
            rows.append([B.cell('a',a),B.cell('b',b),B.result('x',f'({q(a)}+{q(b)})/2',new),B.cell('comportamiento','+' if fx(new)>0 else '−' if fx(new)<0 else '0')])
        else:
            rows.append([i,B.cell('b',b),B.cell('f(b)',fx(b)),B.cell('a',a),
               B.frac('x',f'{q(fx(a))}*({q(b)}-{q(a)})',f'{q(fx(b))}-{q(fx(a))}',new,left=a),
               B.result('f(a)',at(a),fx(a)), '—' if err is None else B.result('ε',f'abs({q(new)}-{q(old)})',err)])
        if err is not None and err<=tol:break
        if fx(a)*fx(new)<=0:b=new
        else:a=new
        old=new
    B.p.sheets.append(Sheet('', ['a','b','x','comportamiento'] if kind=='bisectriz' else ['i','b','f(b)','a','x','f(a)','ε = |xᵢ₊₁ − xᵢ|'],rows))
    if kind=='bisectriz':B.calc('ε',f'abs({q(new)}-{q(old)})',err)
    return B.finish(new)

def iterative_system(w,v,seidel=False):
    # Datos del ejemplo de clase (PDF de la profe), trasladados en a para las cinco variantes.
    # 3a - 0.1b - 0.2c = rhs[0]; 0.1a + 7b - 0.3c = rhs[1]; 0.3a - 0.2b + 10c = rhs[2]
    rhs=[7.85+3*v, -19.3+.1*v, 71.4+.3*v]
    B=Builder(w,v,'Resuelve el sistema. Analiza la diagonal dominante y despeja a, b y c. Termina cuando los tres errores sean ≤ 0.001.',
      f'a = ({f(rhs[0])} + 0.1b + 0.2c)/3; b = ({f(rhs[1])} − 0.1a + 0.3c)/7; c = ({f(rhs[2])} − 0.3a + 0.2b)/10\nεa = |aᵢ − aᵢ₋₁|; εb = |bᵢ − bᵢ₋₁|; εc = |cᵢ − cᵢ₋₁|')
    B.p.initial_text=f'3a − 0.1b − 0.2c = {f(rhs[0])}\n0.1a + 7b − 0.3c = {f(rhs[1])}\n0.3a − 0.2b + 10c = {f(rhs[2])}'
    # Diagonal dominance check exactly as in professor's PDF
    B.note('Diagonal dominante: |3| > |−0.1| + |−0.2|; |7| > |0.1| + |−0.3|; |10| > |0.3| + |−0.2|')
    old=[0.,0.,0.] if seidel else [1.,1.,1.]
    B.note('Valores iniciales: '+', '.join(f'{s}₀ = {f(z)}' for s,z in zip('abc',old))+'. Se utilizan '+('los valores nuevos en cuanto se obtienen.' if seidel else 'los tres valores de la iteración anterior.'))
    history=[[0,*old]]
    for i in range(1,30):
        a=(rhs[0]+.1*old[1]+.2*old[2])/3
        ba=a if seidel else old[0]
        bb=(rhs[1]-.1*ba+.3*old[2])/7
        ca=a if seidel else old[0]; cb=bb if seidel else old[1]
        c=(rhs[2]-.3*ca+.2*cb)/10
        new=[a,bb,c]
        B.note(f'{i}a. iteración')
        # Desarrollo de cada variable con su sustitución completa
        nums=[f'{f(rhs[0])} + 0.1({f(old[1])}) + 0.2({f(old[2])})',
              f'{f(rhs[1])} − 0.1({f(ba)}) + 0.3({f(old[2])})',
              f'{f(rhs[2])} − 0.3({f(ca)}) + 0.2({f(cb)})']
        for s,n,d,z in zip('abc',nums,[3,7,10],new):
            B.line(B.frac(s+sub(i),n,str(d),z))
        history.append([i,*[B.cell(s+sub(i),z) for s,z in zip('abc',new)]])
        errors=[abs(x-y) for x,y in zip(new,old)]
        if max(errors)<=.001:break
        old=new
    B.p.sheets.append(Sheet('', ['i','a','b','c'],history))
    for s,x,y,e in zip('abc',new,old,errors):B.calc('ε'+s,f'abs({q(x)}-{q(y)})',e)
    return B.finish(new[0])

def integration(w,v,kind):
    a=0.;end=1.2+v*.1;n=3 if kind=='simpson38' else 4
    opened=kind=='abiertas';h=(end-a)/(n+2 if opened else n)
    fx=lambda x:math.exp(-x)+x*x/(1+x)
    B=Builder(w,v,f'Calcula I = ∫₀^{f(end)} [e⁻ˣ + x²/(1 + x)] dx, con n = {n}.',
      'h = (b − a)/'+('(n + 2)' if opened else 'n')+'; x = a + ih\n'+{
        'trapecio':'I = (h/2)[f(a) + 2Σf(a + ih) + f(b)]',
        'simpson13':'I = (h/3)[f(a) + 4Σᵢ impar f(a + ih) + 2Σᵢ par f(a + ih) + f(b)]',
        'simpson38':'I = (3h/8)[f(a) + 3Σf(a + ih) + f(b)]',
        'cerradas':'I = αh Σ wᵢ f(a + ih)', 'abiertas':'I = αh Σ wᵢ f(a + ih)'}[kind])
    B.line(B.frac('h',f'{f(end)}-0',f'{n}+2' if opened else str(n),h))
    if kind=='trapecio':weights=[1]+[2]*(n-1)+[1];alpha=.5;factor=f'{q(h)}/2'
    elif kind=='simpson13':weights=[1]+[4 if i%2 else 2 for i in range(1,n)]+[1];alpha=1/3;factor=f'{q(h)}/3'
    elif kind=='simpson38':weights=[1]+[2 if i%3==0 else 3 for i in range(1,n)]+[1];alpha=3/8;factor=f'3*{q(h)}/8'
    elif kind=='cerradas':weights=[7,32,12,32,7];alpha=2/45;factor=f'2*{q(h)}/45';B.note('Constantes para n = 4: α = 2/45; wᵢ = 7, 32, 12, 32, 7.')
    else:weights=[0,11,-14,26,-14,11,0];alpha=6/20;factor=f'6*{q(h)}/20';B.note('Constantes para n = 4: α = 6/20; wᵢ = 0, 11, −14, 26, −14, 11, 0.')
    ys=[]
    for i in range(len(weights)):
        x=a+i*h;ys.append(fx(x))
        B.calc('x = a + '+str(i)+'h',f'0+{i}*{q(h)}',x)
    # Como en el PDF: la sustitución de f se hace en la integral, sin crear
    # una tabla inicial o columnas de productos que no contiene la referencia.
    expression=f'({factor})*('+'+'.join(('' if weight==1 else f'{weight}*')+f'(exp(-{q(i*h)})+{q(i*h)}^2/(1+{q(i*h)}))' for i,weight in enumerate(weights))+')'
    result=alpha*h*sum(c*y for c,y in zip(weights,ys))
    B.calc('I: sustituir la función en cada punto',expression,result)
    B.calc('I: operar los valores de la función',f'({factor})*('+'+'.join(q(y) if c==1 else f'{c}*{q(y)}' for c,y in zip(weights,ys))+')',result)
    return B.finish(result)

def edo(w,v,kind):
    h=.2;initial=2+v*.2
    if kind=='euler':
        y0=1.2+v*.1;y1=2+v*.1;t0=0.;t1=h
        B=Builder(w,v,f'3y′ − 5yt + 1 = 0; y₀ = {f(y0)}; y₁ = {f(y1)}; h = 0.2; t₀ = 0. Obtén y′₁ y y′₂. El valor y₁ inicial es un dato proporcionado, como en el ejemplo.',
          'y′ₙ₊₁ = yₙ + (h/2)[f(yₙ,tₙ) + f(yₙ₊₁,tₙ₊₁)]')
        B.line(Rich([('text','Despejar y′: f(y,t) ='),('input',B.expr('f(y,t)','(5*y*t-1)/3',('y','t')))]))
        for i in (1,2):
            B.calc('t'+sub(i),f'{f(t0)}+{f(h)}',t1)
            expr=f'{q(y0)}+({f(h)}/2)*((5*{q(y0)}*{q(t0)}-1)/3+(5*{q(y1)}*{q(t1)}-1)/3)'
            z=numeric(expr);B.calc('y′'+sub(i),expr,z)
            y0,y1,t0,t1=y1,z,t1,t1+h
        return B.finish(z)
    if kind=='superior':
        y=1+v*.2;dy=2+v*.2;t=0.;h=.25
        B=Builder(w,v,f'y″ − y′t − y = 0; y₀ = {f(y)}; y′₀ = {f(dy)}; t₀ = 0; h = 0.25. Obtén y₁, y′₁, y₂ y y′₂.',
          'Vₙ = y′; Uₙ = y; qₙ = t\nk₁ = hVₙ; m₁ = h(aVₙqₙ + bUₙ); k₂ = h(Vₙ + m₁)\nm₂ = h[a(Vₙ + m₁)(qₙ + h) + b(Uₙ + k₁)]\nyₙ₊₁ = yₙ + (k₁ + k₂)/2; y′ₙ₊₁ = y′ₙ + (m₁ + m₂)/2')
        B.note('Despejar: y″ = y′t + y')
        B.line(Rich([('label','a =',B.cell('a',1)),('label','b =',B.cell('b',1))]))
        for i in range(2):
            B.note(f'Para y{sub(i+1)} y y′{sub(i+1)}:')
            B.line(Rich([('label','Vₙ =',B.cell('Vₙ',dy)),('label','Uₙ =',B.cell('Uₙ',y)),('label','qₙ =',B.cell('qₙ',t))]))
            k1=h*dy;m1=h*(dy*t+y);k2=h*(dy+m1);m2=h*((dy+m1)*(t+h)+y+k1)
            for name,expr,z in [('k₁',f'{h}*{q(dy)}',k1),('m₁',f'{h}*(1*{q(dy)}*{q(t)}+1*{q(y)})',m1),('k₂',f'{h}*({q(dy)}+{q(m1)})',k2),('m₂',f'{h}*(1*({q(dy)}+{q(m1)})*({q(t)}+{h})+1*({q(y)}+{q(k1)}))',m2)]:B.calc(name,expr,z)
            new=y+(k1+k2)/2;newdy=dy+(m1+m2)/2
            B.calc('y'+sub(i+1),f'{q(y)}+({q(k1)}+{q(k2)})/2',new)
            B.calc('y′'+sub(i+1),f'{q(dy)}+({q(m1)}+{q(m2)})/2',newdy)
            y,dy,t=new,newdy,t+h
        return B.finish(y)
    formulas={
      'rk2':'k₁ = hf(yₙ,tₙ); k₂ = hf(yₙ + k₁,tₙ + h)\nyₙ₊₁ = yₙ + (k₁ + k₂)/2',
      'rk3':'k₁ = hf(yₙ,tₙ); k₂ = hf(yₙ + k₁/2,tₙ + h/2)\nk₃ = hf(yₙ − k₁ + 2k₂,tₙ + h)\nyₙ₊₁ = yₙ + (k₁ + 4k₂ + k₃)/6',
      'rk4':'k₁ = hf(yₙ,tₙ); k₂ = hf(yₙ + k₁/2,tₙ + h/2)\nk₃ = hf(yₙ + k₂/2,tₙ + h/2); k₄ = hf(yₙ + k₃,tₙ + h)\nyₙ₊₁ = yₙ + (k₁ + 2k₂ + 2k₃ + k₄)/6',
      'rk38':'k₁ = hf(yₙ,tₙ); k₂ = hf(yₙ + k₁/3,tₙ + h/3)\nk₃ = hf(yₙ + k₁/3 + k₂/3,tₙ + 2h/3)\nk₄ = hf(yₙ + k₁ − k₂ + k₃,tₙ + h)\nyₙ₊₁ = yₙ + (k₁ + 3k₂ + 3k₃ + k₄)/8'}
    B=Builder(w,v,f'y′ − 5yt + 1 = 0; y₀ = {f(initial)}; h = 0.2; t₀ = 0. Encuentra todos los k, y₁ y y₂.',formulas[kind])
    B.line(Rich([('text','Despejar y′: f(y,t) ='),('input',B.expr('f(y,t)','5*y*t-1',('y','t')))]))
    y=initial;t=0.
    for i in range(2):
        B.note('Encontrar y'+sub(i+1))
        args=[(f(y),f(t))];ks=[]
        def stage(ye,te):
            expr=f'{h}*(5*({ye})*({te})-1)';z=numeric(expr);ks.append(z);B.calc('k'+sub(len(ks)),expr,z)
        stage(*args[0]);k1=ks[0]
        den=1 if kind=='rk2' else 3 if kind=='rk38' else 2
        stage(f'{q(y)}+{q(k1)}'+('' if den==1 else f'/{den}'),f'{q(t)}+{h}'+('' if den==1 else f'/{den}'))
        if kind=='rk3':stage(f'{q(y)}-{q(k1)}+2*{q(ks[1])}',f'{q(t)}+{h}')
        elif kind=='rk4':stage(f'{q(y)}+{q(ks[1])}/2',f'{q(t)}+{h}/2')
        elif kind=='rk38':stage(f'{q(y)}+{q(k1)}/3+{q(ks[1])}/3',f'{q(t)}+2*{h}/3')
        if kind=='rk4':stage(f'{q(y)}+{q(ks[2])}',f'{q(t)}+{h}')
        elif kind=='rk38':stage(f'{q(y)}+{q(k1)}-{q(ks[1])}+{q(ks[2])}',f'{q(t)}+{h}')
        weights={'rk2':[1,1],'rk3':[1,4,1],'rk4':[1,2,2,1],'rk38':[1,3,3,1]}[kind]
        expr=f'{q(y)}+('+'+'.join(q(z) if c==1 else f'{c}*{q(z)}' for c,z in zip(weights,ks))+f')/{sum(weights)}'
        new=numeric(expr);B.calc('y'+sub(i+1),expr,new);B.calc('t'+sub(i+1),f'{q(t)}+{h}',t+h)
        y,t=new,t+h
    return B.finish(y)

def transform_legacy(p):
    """Sistemas directos: sustituye operaciones resueltas por desarrollo editable.

    La lista/matriz original y su orden no se alteran. Se usa también para las
    operaciones de reducción del sistema de mínimos cuadrados.
    """
    from .engine import EquationSheet
    def expr(label,text):
        numeric(text)  # No crear casillas de expresión para rótulos.
        p.fields.append(Field(label,Expression(text),'Escribe la operación completa con sus datos.'))
        return Cell(len(p.fields)-1)
    new=[]
    for s in p.sheets:
        if isinstance(s,EquationSheet):
            blocks=[('text',s.left)]
            if s.denominator:
                blocks.append(('fraction',expr(s.left+': numerador',s.numerator),expr(s.left+': denominador',s.denominator)))
            elif s.suffix:
                text=s.suffix.rstrip(' =')
                try:blocks.append(('input',expr('Sustitución',text)))
                except (SyntaxError,ValueError):blocks.append(('text',s.suffix))
            if s.result is not None:blocks.append(('label','=',s.result))
            new.append(Rich(blocks))
        elif isinstance(s,Sheet):
            if 'Sustitución' in s.headers:
                j=s.headers.index('Sustitución')
                for row in s.rows:
                    try:row[j]=expr('Sustitución',row[j])
                    except (SyntaxError,ValueError):pass
            new.append(s)
        else:new.append(s)
    p.sheets=new;return p

def direct_event(kind,v):
    from .linear_events import linear_event
    p=transform_legacy(linear_event(kind-4,v))
    original=p.table
    variables=original[0][1:-1]
    p.initial_layout='text'
    p.initial_text='\n'.join(' + '.join(f'({row[j+1]}){name}' for j,name in enumerate(variables))+' = '+row[-1] for row in original[1:])
    matrix=[]
    for row in original[1:]:
        cells=[]
        for value in row[1:]:
            p.fields.append(Field('Matriz aumentada inicial',float(value),'Coloca el coeficiente o el término independiente del sistema.'))
            cells.append(Cell(len(p.fields)-1))
        matrix.append(cells)
    p.sheets.insert(0,Sheet('Matriz aumentada',variables+[''],matrix))
    formula={4:'N.E. = [(E.P.)(E.A.) − (E.C.F.P.)(E.C.C.P.)]/P.A.\nN.E.: nuevo elemento; E.P.: elemento pivote; E.A.: elemento actual; E.C.F.P.: elemento correspondiente a la fila del pivote; E.C.C.P.: elemento correspondiente a la columna del pivote; P.A.: pivote anterior.',
             5:'Dividir la fila pivote entre el elemento pivote.\nNuevo elemento = elemento actual − (elemento de la columna pivote)(elemento correspondiente de la fila pivote nueva).',
             6:'Multiplicar una fila por una constante distinta de cero. Sumar o restar un múltiplo de una ecuación a otra hasta obtener una forma triangular; después, sustituir hacia atrás.'}[kind]
    p.formula=formula
    for sheet in p.sheets:
        if not isinstance(sheet,Sheet):continue
        # El factor, el pivote y las entradas de las matrices intermedias
        # también los escribe el alumno; los títulos no anticipan su valor.
        if sheet.title.startswith('Pivote '):sheet.title='Pivote'
        if 'multiplicado por' in sheet.title:sheet.title=sheet.title.split(' multiplicado por')[0]+' multiplicado'
        for row in sheet.rows:
            for j,c in enumerate(row):
                if isinstance(c,str) and not (j==0 and len(row)==5):
                    try:z=float(c)
                    except ValueError:continue
                    p.fields.append(Field('Entrada de '+sheet.title,z,'Obtén el valor a partir de la matriz anterior.'))
                    row[j]=Cell(len(p.fields)-1)
    p.duration=max(p.duration,min(3600,180+len(p.fields)*20));return p

def least_squares(w,v,kind):
    # Se conservan las tablas de productos y matrices normales de las hojas.
    from . import curriculum as old
    p=old.least_squares(w,v,kind)
    p.method=FULL_NAMES[w]
    p.statement+=' En las sumatorias, suma los valores de cada columna.'
    if 'funcion' in kind:p.statement+=' En los productos, sustituye f(x) por eˣ y escribe la operación completa.'
    p=transform_legacy(p)
    # Los productos, así como cada sumatoria, requieren su operación escrita
    # en la misma celda de la tabla de clase, encima del resultado.
    table=next(s for s in p.sheets if isinstance(s,Sheet) and s.title=='Productos y sumatorias')
    system=next(s for s in p.sheets if isinstance(s,Sheet) and s.title=='Formar el sistema con las sumatorias')
    degree={'recta':1,'cuadratica':2,'cubica':3,'lineal_funcion':1,'cuadratica_funcion':2}[kind]
    powers=['','x','x²','x³']
    headers=['a'+sub(i)+powers[i] for i in range(degree+1)]
    if 'funcion' in kind:headers+=['a'+sub(degree+1)+'f(x)']
    headers+=['g(x)']
    for s in p.sheets:
        if isinstance(s,Sheet) and s.title in ('Formar el sistema con las sumatorias','Sistema de ecuaciones normales'):s.headers=headers
    p.formula_tables=[system]
    p.sheets=[s for s in p.sheets if not isinstance(s,PlotSheet) and s is not system]
    values=[]
    trans=str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹','0123456789')
    def expression(name,x,y):
        if name=='x':return f(x)
        if name=='y':return f(y)
        if name=='f(x)':return f'exp({q(x)})'
        if name=='xf(x)':return f'{q(x)}*exp({q(x)})'
        if name=='x²f(x)':return f'{q(x)}^2*exp({q(x)})'
        if name=='f(x)²':return f'exp({q(x)})^2'
        if name=='yf(x)':return f'{q(y)}*exp({q(x)})'
        power=name.translate(trans).replace('x','').replace('y','') or '1'
        return q(x)+('' if power=='1' else '^'+power)+('*'+q(y) if name.endswith('y') else '')
    def cell(label,expr,value):
        p.fields.append(Field(label+': sustitución',Expression(expr),'Escribe la operación completa, no solo el resultado.'));e=Cell(len(p.fields)-1)
        return Rich(([('text',label+' =')] if label.startswith('Σ') else [])+[('input',e),('label','=',value)])
    for row in table.rows[:-1]:
        x,y=float(row[0]),float(row[1]);values.append([x,y]+[numeric(expression(name,x,y)) for name in table.headers[2:]])
        for j in range(2,len(row)):row[j]=cell(table.headers[j],expression(table.headers[j],x,y),row[j])
    for j,c in enumerate(table.rows[-1]):table.rows[-1][j]=cell('Σ'+table.headers[j],'+'.join(q(row[j]) for row in values),c)
    # La vista muestra el ajuste cuando el alumno completa sus valores de g(x).
    xs=[float(row[0]) for row in p.table[1:]];ys=[float(row[1]) for row in p.table[1:]]
    fitted=[float(field.value) for field in p.fields if field.label.startswith('g(') and not isinstance(field.value,Expression)]
    if len(fitted)!=len(xs):raise ValueError('Faltan valores de g(x) para la gráfica del ajuste.')
    p.sheets.append(PlotSheet('Gráfica [x, y] y [x, g(x)]',[list(zip(xs,ys)),list(zip(xs,fitted))],['[x, y]','[x, g(x)]']))
    p.duration=max(p.duration,min(3600,180+len(p.fields)*20))
    return p

def primary(w,v):
    if not 0<=v<5:raise ValueError('Variante fuera del catálogo')
    kind=CATALOG[w][0]
    if w in (0,1,5,6,7):return interpolation(w,v)
    if kind in ('grafico','bisectriz','nr','fijo','secante','falsa'):return roots(w,v,kind)
    if kind in ('jacobi','seidel'):return iterative_system(w,v,kind=='seidel')
    if kind in ('recta','cuadratica','cubica','lineal_funcion','cuadratica_funcion'):return least_squares(w,v,kind)
    if kind in ('trapecio','simpson13','simpson38','cerradas','abiertas'):return integration(w,v,kind)
    return edo(w,v,kind)

def bonus(kind,v):
    if kind in (4,5,6):
        return direct_event(kind,v)
    if kind>=100:return primary(kind-100,v)
    return primary({0:8,1:13,2:23,3:6}[kind],v)
