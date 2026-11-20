"""Catálogo de clase. Cada hoja conserva la notación de su referencia.

Referencias por archivo y página en SOURCES. RK 3/8 usa expresamente la
expresión solicitada del PDF, no la reemplaza por la variante de otros textos.
"""
import math
from fractions import Fraction
from dataclasses import dataclass
from .engine import Problem, Field, Cell, Sheet, EquationSheet, number

SUB=str.maketrans('0123456789+-','₀₁₂₃₄₅₆₇₈₉₊₋')
def sub(n):return str(n).translate(SUB)
def fmt(x):return number(x,9)

# El primer sector introduce la consola; los sistemas directos no son mundos.
CATALOG=[
 ('lineal','Helios','Interpolación lineal',360,'Interpolación/InterpolaciónLineal.pdf',3),
 ('lagrange','Selene','Lagrange',600,'Interpolación/Lagrange.pdf',1),
 ('grafico','Atlas','Método gráfico',360,'EcuacionesNoLineales/EcNoLGráficoBisectriz.pdf',1),
 ('bisectriz','Ío','Bisectriz',720,'EcuacionesNoLineales/EcNoLGráficoBisectriz.pdf',2),
 ('nr','Ares','Newton-Raphson',720,'EcuacionesNoLineales/NR.pdf',2),
 ('divididas','Vesper','Newton con diferencias divididas',720,'Interpolación/NewtonconDiferenciasDivididas.pdf',2),
 ('adelante','Calisto','Newton hacia adelante',720,'Interpolación/NewtonHaciaAdelante.pdf',2),
 ('atras','Europa','Newton hacia atrás',720,'Interpolación/NewtonHaciaAtrás.pdf',2),
 ('falsa','Fobos','Falsa posición',900,'EcuacionesNoLineales/FPosición.pdf',2),
 ('fijo','Deimos','Punto fijo',900,'EcuacionesNoLineales/PFIJO.pdf',2),
 ('secante','Tritón','Secante',720,'EcuacionesNoLineales/Secante.pdf',2),
 ('jacobi','Ceres','Jacobi',1080,'EcuacionesLineales/Jacobi.pdf',1),
 ('seidel','Palas','Gauss-Seidel',1080,'EcuacionesLineales/Gauss-Seidel.pdf',1),
 ('recta','Juno','Mínimos cuadrados · línea recta',1080,'MCuadrados/LíneaRecta.pdf',1),
 ('cuadratica','Vesta','Mínimos cuadrados · cuadrática',1500,'MCuadrados/CuadráticaCúbica.pdf',1),
 ('cubica','Higia','Mínimos cuadrados · cúbica',1800,'MCuadrados/CuadráticaCúbica.pdf',1),
 ('lineal_funcion','Dione','Lineal con función',1500,'MCuadrados/LinealCuadráticaFunción.pdf',1),
 ('cuadratica_funcion','Rea','Cuadrática con función',1800,'MCuadrados/LinealCuadráticaFunción.pdf',1),
 ('trapecio','Tetis','Regla trapezoidal',600,'Integración/RTMN.pdf',2),
 ('simpson13','Nereida','Regla de 1/3 Simpson',600,'Integración/R1tercioSimpson.pdf',2),
 ('simpson38','Proteo','Regla de 3/8 Simpson',600,'Integración/R3octavosSimpson.pdf',1),
 ('cerradas','Oberón','Newton-Cotes cerradas',720,'Integración/RNewtonC-Cerradas.pdf',1),
 ('abiertas','Titania','Newton-Cotes abiertas',900,'Integración/TNewtonCotesAyC.pdf',2),
 ('euler','Miranda','Euler modificado',720,'EDO/EulerModificado.pdf',1),
 ('rk2','Ariel','Runge-Kutta de 2º orden',900,'EDO/R-K2doOrd.pdf',1),
 ('rk3','Umbriel','Runge-Kutta de 3er orden',1080,'EDO/R-K3erOrd.pdf',1),
 ('rk4','Encélado','Runge-Kutta de 4º orden · 1/3 de Simpson',1200,'EDO/R-K4toOrd1tercioS.pdf',1),
 ('rk38','Titán','Runge-Kutta de 4º orden · 3/8 de Simpson',1200,'EDO/R-K4toOrd3OctavosS.pdf',1),
 ('superior','Horizonte','Runge-Kutta de orden superior',1500,'EDO/R-KOrdenSuperior.pdf',1),
]
SOURCES={c[0]:{'file':c[4],'page':c[5]} for c in CATALOG}
COLORS=['#ffb861','#aa9eff','#60bcff','#55daba','#ff7a89']
WORLDS=[(c[1].upper(),c[2],c[2],COLORS[i%5],c[3]) for i,c in enumerate(CATALOG)]

@dataclass
class PlotSheet:
    title:str
    curves:list
    labels:list

class Work:
    def __init__(self,world,v,statement,formula='',table=None):
        c=CATALOG[world]
        self.p=Problem(f'w{world}-{v}',c[2],f'Resuelve la misión de {c[1]}.',statement,formula,[],
          ['Identifica los datos y utiliza la fórmula mostrada.',
           'Sigue las sustituciones en el orden de la hoja; conserva los signos y la precisión de la calculadora.',
           'Revisa la última operación y comprueba el resultado con los datos del problema.'],c[3],0,table or [['Dato','Valor']])
    def cell(self,label,value):
        if not isinstance(value,str) and not math.isfinite(float(value)):raise ValueError(label)
        self.p.fields.append(Field(label,value if isinstance(value,str) else float(value),'Escribe +, − o 0 según el signo de f(x).' if isinstance(value,str) else 'Realiza la operación mostrada; conserva los signos y los datos intermedios.'))
        return Cell(len(self.p.fields)-1)
    def row(self,title,expression,label,value):
        self.p.sheets.append(Sheet(title,['Sustitución',label],[[expression,self.cell(label,value)]]))
    def equation(self,title,left,num,den,value,suffix=''):
        self.p.sheets.append(EquationSheet(title,left,num,den,suffix,self.cell(left,value)))
    def given(self,title,text):self.p.sheets.append(Sheet(title,['Desarrollo'],[[text]]))
    def finish(self,value):
        self.p.final=float(value)
        if self.p.formula:self.p.hints[0]=self.p.formula
        width=max(.01,abs(float(value))*.01)
        self.p.hints[2]=f'El resultado final está entre {fmt(float(value)-width)} y {fmt(float(value)+width)}. Revisa también los pasos intermedios.'
        # Referencia fuera del enunciado para conservar el flujo del juego.
        self.p.source=SOURCES[CATALOG[int(self.p.key.split('-')[0][1:])][0]]
        return self.p

def lagrange(w,v):
    xs=[2+v/10,3+v/10,4+v/10];ys=[x*x+1 for x in xs];x=xs[0]+.5
    b=Work(w,v,f'Obtener g(x) para x = {fmt(x)}. Utiliza los tres datos.',
      'g(x) = y₁[(x − x₂)(x − x₃)]/[(x₁ − x₂)(x₁ − x₃)] + y₂[(x − x₁)(x − x₃)]/[(x₂ − x₁)(x₂ − x₃)] + y₃[(x − x₁)(x − x₂)]/[(x₃ − x₁)(x₃ − x₂)]',
      [['xᵢ','yᵢ']]+[[fmt(a),fmt(c)] for a,c in zip(xs,ys)])
    terms=[]
    for i in range(3):
        js=[j for j in range(3) if j!=i];j,k=js
        n=(x-xs[j])*(x-xs[k]);d=(xs[i]-xs[j])*(xs[i]-xs[k]);t=ys[i]*n/d;terms.append(t)
        rows=[]
        for other in js:
            rows.append([f'x − x{sub(other+1)}',f'{fmt(x)} − {fmt(xs[other])}',b.cell(f'x − x{sub(other+1)} en término {i+1}',x-xs[other])])
            rows.append([f'x{sub(i+1)} − x{sub(other+1)}',f'{fmt(xs[i])} − {fmt(xs[other])}',b.cell(f'x{sub(i+1)} − x{sub(other+1)}',xs[i]-xs[other])])
        b.p.sheets.append(Sheet(f'Sustituciones del término {i+1}',['Factor','Sustitución','Resultado'],rows))
        b.row('Numerador',f'({fmt(x-xs[j])})({fmt(x-xs[k])})','Resultado',n)
        b.row('Denominador',f'({fmt(xs[i]-xs[j])})({fmt(xs[i]-xs[k])})','Resultado',d)
        b.equation(f'Término {i+1}',f'{fmt(ys[i])} ×',f'({fmt(x)} − {fmt(xs[j])})({fmt(x)} − {fmt(xs[k])})',
           f'({fmt(xs[i])} − {fmt(xs[j])})({fmt(xs[i])} − {fmt(xs[k])})',t,suffix='=')
    b.row('Suma',' + '.join(f'({fmt(t)})' for t in terms),'g(x)',sum(terms))
    return b.finish(sum(terms))

def newton_uniform(w,v,back=False):
    xs=[1,2,3];ys=[x*x+v/10 for x in xs];x=2.5;h=1
    b=Work(w,v,f'Obtener g(x) para x = {x}. Calcula h y verifica que los intervalos sean uniformes.',
      's = (x − xᵢ)/h; g(x) = yᵢ + ∇¹f(xᵢ)s + ∇²f(xᵢ)s(s+1)/2!' if back else
      's = (x − xᵢ)/h; g(x) = yᵢ + Δ¹f(xᵢ)s + Δ²f(xᵢ)s(s−1)/2!',
      [['xᵢ','yᵢ']]+list(map(list,zip(xs,ys))))
    for i in range(2):b.row('Intervalos',f'|{xs[i+1]} − {xs[i]}|',f'h{sub(i+1)}',h)
    symbol='∇' if back else 'Δ';d1=[ys[i+1]-ys[i] for i in range(2)];d2=d1[1]-d1[0]
    rows=[[f'{symbol}¹{sub(i+1)} = y{sub(i+2)} − y{sub(i+1)}',f'{fmt(ys[i+1])} − {fmt(ys[i])}',b.cell(f'{symbol}¹{sub(i+1)}',d1[i])] for i in range(2)]
    rows.append([f'{symbol}²₁',f'{fmt(d1[1])} − {fmt(d1[0])}',b.cell(f'{symbol}²₁',d2)])
    b.p.sheets.append(Sheet('Tabla de diferencias',['Diferencia','Sustitución','Resultado'],rows))
    ref=2 if back else 0;s=(x-xs[ref])/h;coef=s*(s+1 if back else s-1)/2
    b.equation('Factor binomial','s =',f'{x} − {xs[ref]}',str(h),s)
    b.row('Coeficientes binomiales','1','(s sobre 0)',1)
    b.row('Coeficientes binomiales',fmt(s),'(s sobre 1)',s)
    b.equation('Coeficientes binomiales','=',f'({fmt(s)})({fmt(s)} {"+" if back else "−"} 1)','2!',coef)
    d=d1[-1] if back else d1[0];g=ys[ref]+d*s+d2*coef
    b.row('Evaluación',f'{fmt(ys[ref])}(1) + ({fmt(d)})({fmt(s)}) + ({fmt(d2)})({fmt(coef)})','g(x)',g)
    return b.finish(g)

def roots(w,v,kind):
    C=2+v;x0=1.;x1=2.5
    if kind=='grafico':
        # La tabla y el cruce se representan en un plano real, no un índice de categorías.
        f=lambda x:x*x-C
        b=Work(w,v,f'Tabula y = x² − {C}. Identifica un intervalo positivo con cambio de signo y observa el cruce con el eje x.',
               'f(x) = 0', [['x'],[0],[1],[2],[3]])
        b.p.sheets.append(Sheet('Tabla',['x','y'],[[x,b.cell(f'y con x = {x}',f(x))] for x in range(4)]))
        lo=math.floor(math.sqrt(C));hi=lo+1
        b.row('Cambio de signo','Extremo izquierdo del intervalo positivo','a',lo)
        b.row('Cambio de signo','Extremo derecho del intervalo positivo','b',hi)
        points=[(i/20,f(i/20)) for i in range(61)]
        b.p.sheets.append(PlotSheet('Gráfica de la función',[points],['y = x² − '+str(C)]))
        return b.finish(math.sqrt(C))
    if kind=='fijo':
        initial=v/5
        b=Work(w,v,f'Localiza la raíz de f(x) = e⁻ˣ − x. Parte de x₀ = {fmt(initial)}. Termina cuando ε ≤ 0.0001.',
               'xᵢ₊₁ = g(xᵢ) = e^(−xᵢ); ε = |xᵢ₊₁ − xᵢ|', [['Dato','Valor'],['x₀',initial]])
        b.given('Despejar x','e⁻ˣ − x = 0; x = e⁻ˣ')
        old=initial;i=0;rows=[[0,'—',fmt(initial),'—']]
        while True:
            new=math.exp(-old);i+=1;err=abs(new-old)
            rows.append([i,f'e^(−({fmt(old)}))',b.cell(f'x{sub(i)}',new),b.cell(f'ε{sub(i)}',err)])
            if err<=.0001:break
            old=new
        b.p.sheets.append(Sheet('Iteraciones',['i','e⁻ˣ','xᵢ','ε = |xᵢ₊₁ − xᵢ|'],rows))
        b.row('Margen de error',f'|{fmt(new)} − {fmt(old)}|','ε',err)
        return b.finish(new)
    if kind=='nr':
        b=Work(w,v,f'Encuentre la raíz positiva de f(x) = x² − {C}; f′(x) = 2x. x₀ = 2. Termina cuando ε ≤ 0.0001.',
            'xᵢ₊₁ = xᵢ − f(xᵢ)/f′(xᵢ); ε = |xᵢ₊₁ − xᵢ|',[['Dato','Valor'],['x₀',2]])
        old=2.;i=0
        while True:
            new=old-(old*old-C)/(2*old);err=abs(new-old);i+=1
            b.equation(f'Iteración {i}',f'x{sub(i)} = {fmt(old)} −',f'({fmt(old)})² − {C}',f'2({fmt(old)})',new,suffix='=')
            b.row('Margen de error',f'|{fmt(new)} − {fmt(old)}|','ε',err)
            if err<=.0001:break
            old=new
        return b.finish(new)
    if kind=='secante':
        f=lambda x:x*x-C
        b=Work(w,v,f'Calcule la raíz positiva de f(x) = x² − {C}. x₀ = 1; x₁ = 3. Termina cuando ε ≤ 0.001.',
          'xᵢ₊₁ = xᵢ − f(xᵢ)(xᵢ − xᵢ₋₁)/[f(xᵢ) − f(xᵢ₋₁)]',[['Dato','Valor'],['x₀',1],['x₁',3]])
        old,new=1.,3.
        for i in range(2,30):
            b.row('Evaluación',f'({fmt(old)})² − {C}',f'f(x{sub(i-2)})',f(old))
            b.row('Evaluación',f'({fmt(new)})² − {C}',f'f(x{sub(i-1)})',f(new))
            nxt=new-f(new)*(new-old)/(f(new)-f(old));err=abs(nxt-new)
            b.equation(f'Iteración {i}',f'x{sub(i)} = {fmt(new)} −',f'({fmt(f(new))})({fmt(new)} − {fmt(old)})',
                 f'{fmt(f(new))} − ({fmt(f(old))})',nxt,suffix='=')
            b.row('Margen de error',f'|{fmt(nxt)} − {fmt(new)}|','ε',err)
            if err<=.001:break
            old,new=new,nxt
        return b.finish(nxt)
    a=1.;bb=3.;fa=lambda x:x*x-C
    if C==2:a=1.;bb=2.
    b=Work(w,v,f'Calcule la raíz positiva de f(x) = x² − {C}, con a = {fmt(a)}, b = {fmt(bb)}. Termina cuando ε ≤ 0.001.',
        'x = (a + b)/2; ε = |xᵢ₊₁ − xᵢ|' if kind=='bisectriz' else
        'x = a − f(a)(b − a)/[f(b) − f(a)]; ε = |xᵢ₊₁ − xᵢ|',[['x','f(x)'],[a,fmt(fa(a))],[bb,fmt(fa(bb))]])
    old=None;rows=[] if kind=='bisectriz' else [[0,fmt(bb),fmt(fa(bb)),fmt(a),'—',fmt(fa(a)),'—']]
    for i in range(1,101):
        x=(a+bb)/2 if kind=='bisectriz' else a-fa(a)*(bb-a)/(fa(bb)-fa(a))
        err=None if old is None else abs(x-old)
        if kind=='bisectriz':
            # El ejemplo de clase usa a, b, x y comportamiento, no f y derivadas adicionales.
            rows.append([fmt(a),fmt(bb),b.cell(f'x{sub(i)}',x),b.cell(f'Comportamiento, i={i}','+' if fa(x)>0 else '−' if fa(x)<0 else '0'),
                         '—' if err is None else b.cell(f'ε{sub(i)}',err)])
        else:
            rows.append([i,fmt(bb),fmt(fa(bb)),fmt(a),b.cell(f'x{sub(i)}',x),b.cell(f'f(a), i={i}',fa(a)),
                         '—' if err is None else b.cell(f'ε{sub(i)}',err)])
        if err is not None and err<=.001:break
        if fa(a)*fa(x)<=0:bb=x
        else:a=x
        old=x
    b.p.sheets.append(Sheet('Iteraciones',(['a','b','x','comportamiento','ε'] if kind=='bisectriz' else
                 ['i','b','f(b)','a','x','f(a)','ε = |xᵢ₊₁ − xᵢ|']),rows))
    return b.finish(x)

def iterative_system(w,v,seidel=False):
    # Datos del ejemplo de clase, trasladados en a para las cinco variantes.
    rhs=[7.85+3*v,-19.3+.1*v,71.4+.3*v]
    b=Work(w,v,f'Resuelve el sistema por {"Gauss-Seidel" if seidel else "Jacobi"}. Analiza la diagonal dominante. ε = 0.001.',
        f'a = ({fmt(rhs[0])} + 0.1b + 0.2c)/3; b = ({fmt(rhs[1])} − 0.1a + 0.3c)/7; c = ({fmt(rhs[2])} − 0.3a + 0.2b)/10',
        [['Ecuación'],[f'3a − 0.1b − 0.2c = {fmt(rhs[0])}'],[f'0.1a + 7b − 0.3c = {fmt(rhs[1])}'],[f'0.3a − 0.2b + 10c = {fmt(rhs[2])}']])
    b.given('Diagonal dominante','|3| > |−0.1| + |−0.2|; |7| > |0.1| + |−0.3|; |10| > |0.3| + |−0.2|')
    old=[0.,0.,0.] if seidel else [1.,1.,1.];history=[[0,*old]]
    b.given('Valores iniciales','; '.join(f'{s}₀ = {fmt(x)}' for s,x in zip('abc',old)))
    for i in range(1,30):
        a=(rhs[0]+.1*old[1]+.2*old[2])/3
        ba=a if seidel else old[0]
        bb=(rhs[1]-.1*ba+.3*old[2])/7
        ca=a if seidel else old[0];cb=bb if seidel else old[1]
        c=(rhs[2]-.3*ca+.2*cb)/10
        nums=[f'{fmt(rhs[0])} + 0.1({fmt(old[1])}) + 0.2({fmt(old[2])})',
              f'{fmt(rhs[1])} − 0.1({fmt(ba)}) + 0.3({fmt(old[2])})',
              f'{fmt(rhs[2])} − 0.3({fmt(ca)}) + 0.2({fmt(cb)})']
        new=[a,bb,c]
        for s,n,d,z in zip('abc',nums,[3,7,10],new):b.equation(f'Iteración {i}',f'{s}{sub(i)} =',n,str(d),z)
        history.append([i,*[fmt(x) for x in new]])
        errors=[abs(a-c) for a,c in zip(new,old)]
        if max(errors)<=.001:
            for s,x,y,e in zip('abc',new,old,errors):b.row('Margen de error',f'|{fmt(x)} − {fmt(y)}|','ε'+s,e)
            break
        old=new
    b.p.sheets.append(Sheet('Tabla de iteraciones',['i','a','b','c'],history))
    return b.finish(new[0])

def integration(w,v,kind):
    a=0.;end=1.;n=3 if kind=='simpson38' else 4;C=1+v/10
    f=lambda x:C-x*x
    opened=kind=='abiertas';h=(end-a)/(n+2 if opened else n)
    xs=[i*h for i in range(n+3 if opened else n+1)];ys=[f(x) for x in xs]
    if kind=='trapecio':weights=[1,2,2,2,1];alpha=.5
    elif kind=='simpson13':weights=[1,4,2,4,1];alpha=1/3
    elif kind=='simpson38':weights=[1,3,3,1];alpha=3/8
    elif kind=='cerradas':weights=[7,32,12,32,7];alpha=2/45
    else:weights=[0,11,-14,26,-14,11,0];alpha=6/20
    formulas={'trapecio':'h = (b − a)/n; I = (h/2)[f(a) + 2Σf(a + ih) + f(b)]',
       'simpson13':'h = (b − a)/n; I = (h/3)[f(a) + 4Σf(a + ih) + 2Σf(a + ih) + f(b)]',
       'simpson38':'h = (b − a)/n; I = (3h/8)[f(a) + 3Σf(a + ih) + f(b)]',
       'cerradas':'h = (b − a)/n; I = αh Σ wᵢf(a + ih)',
       'abiertas':'h = (b − a)/(n + 2); I = αh Σ wᵢf(a + ih)'}
    b=Work(w,v,f'Integra f(x) = {fmt(C)} − x² desde a = 0 hasta b = 1; n = {n}.',formulas[kind],
      [['Dato','Valor'],['a',0],['b',1],['n',n]])
    b.equation('Solución','h =','1 − 0',f'{n} + 2' if opened else str(n),h)
    if kind in ('cerradas','abiertas'):
        b.given('Constantes de Newton-Cotes',f'n = {n}; α = {"6/20" if opened else "2/45"}; wᵢ = '+', '.join(map(str,weights)))
    for i,(x,y) in enumerate(zip(xs,ys)):
        b.row('Se incrementa x = a + ih',f'0 + {i}({fmt(h)})','x',x)
        b.row('Considerar la función de la integral',f'{fmt(C)} − ({fmt(x)})²','f(x)',y)
    coef={'trapecio':('h','2'),'simpson13':('h','3'),'simpson38':('3h','8'),
          'cerradas':('2h','45'),'abiertas':('6h','20')}[kind]
    b.given('Sustitución','I = ('+coef[0]+'/'+coef[1]+')['+' + '.join(f'{c}({fmt(y)})' for c,y in zip(weights,ys))+']')
    terms=[]
    for c,y in zip(weights,ys):
        val=c*y;terms.append(val);b.row('Operaciones',f'{c}({fmt(y)})','Resultado',val)
    b.row('Suma',' + '.join(f'({fmt(t)})' for t in terms),'Resultado',sum(terms))
    result=alpha*h*sum(terms)
    multiple={'trapecio':1,'simpson13':1,'simpson38':3,'cerradas':2,'abiertas':6}[kind]
    b.equation('Integral','I =',f'{fmt(multiple*h)}({fmt(sum(terms))})',coef[1],result)
    return b.finish(result)

def normal_solve(b,A,r):
    """Desarrollo de las ecuaciones normales y eliminación por filas, sin fórmula abreviada de a₁."""
    n=len(r);m=[list(map(float,row))+[float(y)] for row,y in zip(A,r)]
    headers=[f'a{sub(i)}' for i in range(n)]+['g(x)']
    b.p.sheets.append(Sheet('Sistema de ecuaciones normales',headers,[[b.cell('Coeficiente del sistema',z) for z in row] for row in m]))
    for k in range(n-1):
        for i in range(k+1,n):
            factor=-m[i][k]/m[k][k];old=m[i][:]
            b.equation('Multiplicar la ecuación',f'Factor de la ecuación {k+1} =',f'−({fmt(m[i][k])})',fmt(m[k][k]),factor)
            for j in range(k,n+1):
                m[i][j]=old[j]+factor*m[k][j]
                b.row(f'Sumar las ecuaciones {i+1} y la ecuación multiplicada',f'{fmt(old[j])} + ({fmt(factor)})({fmt(m[k][j])})','Resultado',m[i][j])
    sol=[0.]*n
    for i in reversed(range(n)):
        numerator=m[i][-1]-sum(m[i][j]*sol[j] for j in range(i+1,n));sol[i]=numerator/m[i][i]
        expression=fmt(m[i][-1])+''.join(f' − ({fmt(m[i][j])})({fmt(sol[j])})' for j in range(i+1,n))
        b.equation('Sustituir los coeficientes',f'a{sub(i)} =',expression,fmt(m[i][i]),sol[i])
    return sol

def least_squares(w,v,kind):
    degree={'recta':1,'cuadratica':2,'cubica':3,'lineal_funcion':1,'cuadratica_funcion':2}[kind]
    extra='funcion' in kind;n=6
    xs=[i/2 for i in range(n)]
    basis=lambda x:[x**k for k in range(degree+1)]+([math.exp(x)] if extra else [])
    coeff=[1+v/10]+[1/(i+1) for i in range(1,degree+1)]+([.5] if extra else [])
    # El dato usado por el validador es exactamente el dato que ve el jugador.
    noise=[.08,-.05,.04,-.09,.06,-.03]
    ys=[round(sum(a*c for a,c in zip(coeff,basis(x)))+noise[i]*(1+v*.1),4) for i,x in enumerate(xs)]
    supers=str.maketrans('0123456789','⁰¹²³⁴⁵⁶⁷⁸⁹')
    label='g(x) = '+' + '.join(f'a{sub(i)}'+('' if i==0 else 'x' if i==1 else 'x'+str(i).translate(supers)) for i in range(degree+1))+(' + a'+sub(degree+1)+'eˣ' if extra else '')
    b=Work(w,v,f'Ajusta los datos. n = {n}. '+('Usa función (x) = eˣ. ' if extra else '')+'Completa las sumatorias, el sistema y g(x) para cada dato.',label,[['x','y']]+[[fmt(x),fmt(y)] for x,y in zip(xs,ys)])
    columns=[('x',lambda x,y:x),('y',lambda x,y:y)]
    columns += [(f'x{str(k).translate(str.maketrans("0123456789","⁰¹²³⁴⁵⁶⁷⁸⁹"))}',lambda x,y,k=k:x**k) for k in range(2,2*degree+1)]
    columns += [('xy' if k==1 else 'x'+str(k).translate(supers)+'y',lambda x,y,k=k:x**k*y) for k in range(1,degree+1)]
    if extra:columns += [('f(x)',lambda x,y:math.exp(x)),('xf(x)',lambda x,y:x*math.exp(x)),('f(x)²',lambda x,y:math.exp(x)**2),('yf(x)',lambda x,y:y*math.exp(x))]+([('x²f(x)',lambda x,y:x*x*math.exp(x))] if degree==2 else [])
    rows=[]
    for x,y in zip(xs,ys):rows.append([fmt(x),fmt(y)]+[b.cell(name,fn(x,y)) for name,fn in columns[2:]])
    rows.append([b.cell('Σx',sum(xs)),b.cell('Σy',sum(ys))]+[b.cell('Σ'+name,sum(fn(x,y) for x,y in zip(xs,ys))) for name,fn in columns[2:]])
    b.p.sheets.append(Sheet('Productos y sumatorias',[c[0] for c in columns],rows))
    vec=[basis(x) for x in xs];d=len(coeff)
    A=[[sum(row[i]*row[j] for row in vec) for j in range(d)] for i in range(d)]
    r=[sum(row[i]*y for row,y in zip(vec,ys)) for i in range(d)]
    def power(k):return '' if k==0 else 'x' if k==1 else 'x'+str(k).translate(supers)
    symbolic=[]
    for i in range(d):
        row=[]
        for j in range(d):
            if extra and i==d-1 and j==d-1:term='Σf(x)²'
            elif extra and (i==d-1 or j==d-1):term='Σ'+power(j if i==d-1 else i)+'f(x)'
            elif i+j==0:term='n'
            else:term='Σ'+power(i+j)
            row.append(term)
        row.append('Σyf(x)' if extra and i==d-1 else 'Σ'+power(i)+'y')
        symbolic.append(row)
    b.p.sheets.append(Sheet('Formar el sistema con las sumatorias',[f'a{sub(i)}' for i in range(d)]+['g(x)'],symbolic))
    sol=normal_solve(b,A,r)
    curve=[]
    for x in xs:
        z=sum(a*c for a,c in zip(sol,basis(x)));curve.append((x,z))
        expression=fmt(sol[0])+''.join(f' + ({fmt(sol[i])})*({fmt(x)})'+('' if i==1 else f'^{i}') for i in range(1,degree+1))
        if extra:expression+=f' + ({fmt(sol[-1])})*exp({fmt(x)})'
        b.row('Encontrar g(x)',expression,f'g({fmt(x)})',z)
    b.p.sheets.append(PlotSheet('Gráfica [x, y] y [x, g(x)]',[list(zip(xs,ys)),curve],['[x, y]','[x, g(x)]']))
    return b.finish(sol[0])

def edo(w,v,kind):
    h=.2;initial=2+v/10
    if kind=='euler':
        # La y₁ inicial es un dato proporcionado, como en el PDF; no se introduce un predictor ajeno.
        y0=1.2+v/10;y1=2+v/10;t0=0.;t1=h
        b=Work(w,v,f'3y′ − 5yt + 1 = 0; y₀ = {fmt(y0)}, y₁ = {fmt(y1)}, h = 0.2. Obtén y′₁ y y′₂ siguiendo el ejemplo.',
          'y′ₙ₊₁ = yₙ + (h/2)[f(yₙ,tₙ) + f(yₙ₊₁,tₙ₊₁)]',
          [['Dato','Valor'],['y₀',fmt(y0)],['y₁',fmt(y1)],['h',h]])
        b.given('Despejar y′','y′ = (5yt − 1)/3')
        for i in range(1,3):
            f0=(5*y0*t0-1)/3;f1=(5*y1*t1-1)/3;value=y0+h/2*(f0+f1)
            b.row('Considerar t',f'{fmt(t0)} + {fmt(h)}',f't{sub(i)}',t1)
            b.equation('Sustitución','f(y₀,t₀) =',f'5({fmt(y0)})({fmt(t0)}) − 1','3',f0)
            b.equation('Sustitución','f(y₁,t₁) =',f'5({fmt(y1)})({fmt(t1)}) − 1','3',f1)
            b.row('Euler modificado',f'{fmt(y0)} + ({fmt(h)}/2)[({fmt(f0)}) + ({fmt(f1)})]',f'y′{sub(i)}',value)
            y0,y1,t0,t1=y1,value,t1,t1+h
        return b.finish(value)
    if kind=='superior':
        y=1+v/10;dy=2+v/10;t=0.;h=.5
        b=Work(w,v,f'y″ − y′t − y = 0; y₀ = {fmt(y)}, y′₀ = {fmt(dy)}, h = 0.5. Obtén y₁, y′₁, y₂ y y′₂.',
             'Vₙ = y′; Uₙ = y; qₙ = t; k₁ = hVₙ; m₁ = h(Vₙqₙ + Uₙ); k₂ = h(Vₙ + m₁); m₂ = h[(Vₙ + m₁)(qₙ + h) + (Uₙ + k₁)]',
             [['Dato','Valor'],['y₀',fmt(y)],['y′₀',fmt(dy)],['h',h]])
        for i in range(2):
            k1=h*dy;m1=h*(dy*t+y);k2=h*(dy+m1);m2=h*((dy+m1)*(t+h)+(y+k1))
            for name,expression,z in [('k₁',f'{h}({fmt(dy)})',k1),('m₁',f'{h}[({fmt(dy)})({fmt(t)}) + {fmt(y)}]',m1),('k₂',f'{h}({fmt(dy)} + {fmt(m1)})',k2),('m₂',f'{h}[({fmt(dy)} + {fmt(m1)})({fmt(t)} + {h}) + ({fmt(y)} + {fmt(k1)})]',m2)]:b.row(f'Paso {i+1}',expression,name,z)
            new=y+(k1+k2)/2;newdy=dy+(m1+m2)/2
            b.row('Solución',f'{fmt(y)} + ½({fmt(k1)} + {fmt(k2)})',f'y{sub(i+1)}',new)
            b.row('Solución',f'{fmt(dy)} + ½({fmt(m1)} + {fmt(m2)})',f'y′{sub(i+1)}',newdy)
            y,dy,t=new,newdy,t+h
        return b.finish(y)
    b=Work(w,v,f'y′ − 5yt + 1 = 0; y₀ = {fmt(initial)}; h = 0.2; t₀ = 0. Encuentra los k de cada paso, y₁ y y₂.',
       'Despejar y′: y′ = 5yt − 1', [['Dato','Valor'],['y₀',fmt(initial)],['h',h],['t₀',0]])
    y=initial;t=0.;f=lambda y,t:5*y*t-1
    formulas={
      'rk2':['k₁ = h f(yₙ,tₙ)','k₂ = h f(yₙ + k₁,tₙ + h)','yₙ₊₁ = yₙ + ½(k₁ + k₂)'],
      'rk3':['k₁ = h f(yₙ,tₙ)','k₂ = h f(yₙ + k₁/2,tₙ + h/2)','k₃ = h f(yₙ − k₁ + 2k₂,tₙ + h)','yₙ₊₁ = yₙ + ⅙(k₁ + 4k₂ + k₃)'],
      'rk4':['k₁ = h f(yₙ,tₙ)','k₂ = h f(yₙ + k₁/2,tₙ + h/2)','k₃ = h f(yₙ + k₂/2,tₙ + h/2)','k₄ = h f(yₙ + k₃,tₙ + h)','yₙ₊₁ = yₙ + ⅙(k₁ + 2k₂ + 2k₃ + k₄)'],
      'rk38':['k₁ = h f(yₙ,tₙ)','k₂ = h f(yₙ + k₁/3,tₙ + h/3)','k₃ = h f(yₙ + k₁/3 + k₂/3,tₙ + ⅔h)','k₄ = h f(yₙ + k₁ − k₂ + k₃,tₙ + h)','yₙ₊₁ = yₙ + ⅛(k₁ + 3k₂ + 3k₃ + k₄)']}
    for formula in formulas[kind]:b.given('Fórmula',formula)
    for step in range(2):
        args=[(y,t)];ks=[h*f(y,t)]
        if kind=='rk2':args.append((y+ks[0],t+h))
        elif kind in ('rk3','rk4'):args.append((y+ks[0]/2,t+h/2))
        else:args.append((y+ks[0]/3,t+h/3))
        ks.append(h*f(*args[-1]))
        if kind=='rk3':args.append((y-ks[0]+2*ks[1],t+h))
        elif kind=='rk4':args.append((y+ks[1]/2,t+h/2))
        elif kind=='rk38':args.append((y+ks[0]/3+ks[1]/3,t+2*h/3))
        if kind!='rk2':ks.append(h*f(*args[-1]))
        if kind in ('rk4','rk38'):
            args.append((y+ks[2] if kind=='rk4' else y+ks[0]-ks[1]+ks[2],t+h));ks.append(h*f(*args[-1]))
        for j,((yy,tt),kk) in enumerate(zip(args,ks),1):
            if j>1:
                if j==2:
                    den=1 if kind=='rk2' else 3 if kind=='rk38' else 2
                    ye=f'{fmt(y)} + ({fmt(ks[0])})'+('' if den==1 else f'/{den}')
                    te=f'{fmt(t)} + {h}'+('' if den==1 else f'/{den}')
                elif j==3:
                    if kind=='rk3':ye=f'{fmt(y)} − ({fmt(ks[0])}) + 2({fmt(ks[1])})';te=f'{fmt(t)} + {h}'
                    elif kind=='rk4':ye=f'{fmt(y)} + ({fmt(ks[1])})/2';te=f'{fmt(t)} + {h}/2'
                    else:ye=f'{fmt(y)} + ({fmt(ks[0])})/3 + ({fmt(ks[1])})/3';te=f'{fmt(t)} + ⅔({h})'
                else:
                    ye=f'{fmt(y)} + ({fmt(ks[2])})' if kind=='rk4' else f'{fmt(y)} + ({fmt(ks[0])}) − ({fmt(ks[1])}) + ({fmt(ks[2])})'
                    te=f'{fmt(t)} + {h}'
                b.given('Sustitución',f'k{sub(j)} = {h}[5({ye})({te}) − 1]')
            b.row(f'Paso {step+1}: k{sub(j)}',f'{h}[5({fmt(yy)})({fmt(tt)}) − 1]',f'k{sub(j)}',kk)
        weights={'rk2':[1,1],'rk3':[1,4,1],'rk4':[1,2,2,1],'rk38':[1,3,3,1]}[kind];den=sum(weights)
        new=y+sum(a*k for a,k in zip(weights,ks))/den
        b.equation('Solución',f'y{sub(step+1)} = {fmt(y)} +',' + '.join(f'{a}({fmt(k)})' for a,k in zip(weights,ks)),str(den),new,suffix='=')
        b.row('Para el siguiente paso',f'{fmt(t)} + {h}',f't{sub(step+1)}',t+h)
        y,t=new,t+h
    return b.finish(y)

def _make_primary(world,variant):
    if not 0<=world<len(CATALOG) or not 0<=variant<5:raise ValueError('Problema fuera del catálogo.')
    method=CATALOG[world][0]
    if method in ('lineal','divididas'):
        from .engine import classroom_linear,classroom_divided
        p=classroom_linear(variant) if method=='lineal' else classroom_divided(variant)
        p.key=f'w{world}-{variant}';p.duration=CATALOG[world][3];p.source=SOURCES[method]
        return p
    if method=='lagrange':return lagrange(world,variant)
    if method in ('adelante','atras'):return newton_uniform(world,variant,method=='atras')
    if method in ('grafico','bisectriz','nr','fijo','secante','falsa'):return roots(world,variant,method)
    if method in ('jacobi','seidel'):return iterative_system(world,variant,method=='seidel')
    if method in ('recta','cuadratica','cubica','lineal_funcion','cuadratica_funcion'):return least_squares(world,variant,method)
    if method in ('trapecio','simpson13','simpson38','cerradas','abiertas'):return integration(world,variant,method)
    return edo(world,variant,method)

# Solo los datos que se presentan tabulados en clase usan una tabla inicial.
# Las tablas de diferencias, iteraciones, matrices y productos del procedimiento
# permanecen intactas; este criterio solo afecta la introducción del ejercicio.
INITIAL_TABLE_METHODS=frozenset({
    'lagrange','divididas','adelante','atras','falsa',
    'recta','cuadratica','cubica','lineal_funcion','cuadratica_funcion',
})

def primary(world,variant):
    p=_make_primary(world,variant)
    method=CATALOG[world][0]
    if method not in INITIAL_TABLE_METHODS:
        p.initial_layout='text'
        if method=='lineal':
            p.initial_text='\n'.join(f'{row[0]} = {fmt(row[1]) if isinstance(row[1],(int,float)) else row[1]}' for row in p.table[1:])
        elif method in ('jacobi','seidel'):
            p.initial_text='\n'.join(row[0] for row in p.table[1:])
        # En los demás métodos los datos ya figuran completos en el enunciado.
    return p

# Los códigos de evento son independientes de los mundos y no reutilizan sus índices.
def bonus(kind,variant):
    if not 0<=variant<5:raise ValueError('Evento fuera del catálogo.')
    if kind in (4,5,6):
        from .linear_events import linear_event
        return linear_event(kind-4,variant)
    if 100<=kind<100+len(CATALOG):
        p=primary(kind-100,variant);p.key=f'b{kind}-{variant}';return p
    # Compatibilidad de guardados: los antiguos eventos se mapean a hojas de clase.
    mapping={0:'falsa',1:'recta',2:'euler',3:'adelante'}
    if kind not in mapping:raise ValueError('Evento fuera del catálogo.')
    w=next(i for i,c in enumerate(CATALOG) if c[0]==mapping[kind]);p=primary(w,variant);p.key=f'b{kind}-{variant}'
    return p

def event_options(world):
    # Un método ya presentado puede reaparecer como evento, nunca uno futuro.
    options=[100+i for i in range(max(1,world+1))]
    if world>=len(CATALOG)-6:options.extend([4,5,6])
    return options

def event_name(kind):
    if kind in (4,5,6):return {4:'Montante',5:'Gauss-Jordán',6:'Eliminación gaussiana'}[kind]
    if kind>=100:return CATALOG[kind-100][2]
    return {0:'Falsa posición',1:'Línea recta',2:'Euler modificado',3:'Newton hacia adelante'}[kind]
