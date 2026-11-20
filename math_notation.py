"""Notación de cuaderno: fracciones, exponentes y barras, sin sintaxis de código.

Los nodos de entrada son casillas normales del juego. La expresión original se
conserva solo en el motor; cada número de la sustitución lo escribe el alumno.
"""
import ast
import re
import math
from dataclasses import dataclass,field
import pygame
import ui
from classroom.procedure import tree,normalize

@dataclass
class Math:
    kind:str
    items:list=field(default_factory=list)
    text:str=''
    box:object=None

def text(s):return Math('text',text=str(s))
def row(*items):return Math('row',list(items))
def fraction(a,b):return Math('fraction',[a,b])
def power(a,b):return Math('power',[a,b])
def paren(a):return Math('paren',[a])

def from_expression(expression,make_box=None):
    """Las constantes son casillas en el procedimiento y texto en fórmulas."""
    def atom(value):
        if make_box:return Math('box',box=make_box(float(value)))
        from classroom.engine import number
        return text(number(value))
    def build(n):
        if isinstance(n,ast.Expression):return build(n.body)
        if isinstance(n,ast.Constant):return atom(n.value)
        if isinstance(n,ast.Name):
            names={'f_a':'f(a)','f_b':'f(b)','f_x':'f(x)','g_x':'g(x)',
             'f_xi':'f(xᵢ)','df_xi':'f′(xᵢ)','f_prev':'f(xᵢ₋₁)','f_next':'f(xᵢ₊₁)',
             'x_i':'xᵢ','x_prev':'xᵢ₋₁','x_next':'xᵢ₊₁','y_i':'yᵢ',
             'a_i':'aᵢ','a_prev':'aᵢ₋₁','b_i':'bᵢ','b_prev':'bᵢ₋₁','c_i':'cᵢ','c_prev':'cᵢ₋₁',
             'y_n':'yₙ','y_next':'yₙ₊₁','t_n':'tₙ','t_next':'tₙ₊₁',
             'V_n':'Vₙ','U_n':'Uₙ','q_n':'qₙ','dy':'y′','D0':'D⁰','D11':'D¹₁','D21':'D²₁',
             'delta1':'Δ¹f(xᵢ)','delta2':'Δ²f(xᵢ)','nabla1':'∇¹f(xᵢ)','nabla2':'∇²f(xᵢ)',
             'EP':'E.P.','EA':'E.A.','ECFP':'E.C.F.P.','ECCP':'E.C.C.P.','PA':'P.A.'}
            label=names.get(n.id,n.id)
            label=re.sub(r'([A-Za-z]+)(\d+)$',lambda m:m[1]+m[2].translate(str.maketrans('0123456789','₀₁₂₃₄₅₆₇₈₉')),label)
            return text(label)
        if isinstance(n,ast.UnaryOp):
            if isinstance(n.operand,ast.Constant):return atom((-1 if isinstance(n.op,ast.USub) else 1)*n.operand.value)
            child=build(n.operand)
            if isinstance(n.operand,(ast.BinOp,ast.UnaryOp)):child=paren(child)
            return row(text('−' if isinstance(n.op,ast.USub) else '+'),child)
        if isinstance(n,ast.Call):
            name=n.func.id
            if name=='exp':return power(text('e'),build(n.args[0]))
            if name=='abs':return Math('absolute',[build(n.args[0])])
            if name=='sqrt':return Math('root',[build(n.args[0])])
            args=[]
            for arg in n.args:
                if args:args.append(text(','))
                args.append(build(arg))
            return row(text({'log':'ln','sen':'sen'}.get(name,name)),paren(row(*args)))
        if isinstance(n,ast.BinOp):
            a,b=build(n.left),build(n.right)
            if isinstance(n.op,ast.Div):return fraction(a,b)
            if isinstance(n.op,ast.Pow):
                if isinstance(n.left,(ast.BinOp,ast.UnaryOp)):a=paren(a)
                return power(a,b)
            op='+' if isinstance(n.op,ast.Add) else '−' if isinstance(n.op,ast.Sub) else '·'
            if isinstance(n.op,ast.Mult):
                if isinstance(n.left,ast.UnaryOp) or isinstance(n.left,ast.BinOp) and isinstance(n.left.op,(ast.Add,ast.Sub)):a=paren(a)
                if isinstance(n.right,ast.UnaryOp) or isinstance(n.right,ast.BinOp) and isinstance(n.right.op,(ast.Add,ast.Sub)):b=paren(b)
            elif isinstance(n.op,ast.Sub) and isinstance(n.right,ast.BinOp) and isinstance(n.right.op,(ast.Add,ast.Sub)):b=paren(b)
            elif isinstance(n.op,(ast.Add,ast.Sub)) and isinstance(n.right,ast.UnaryOp):b=paren(b)
            # Se permite continuar una suma/producto en otro renglón sin
            # descomponer un número ni convertir una fracción en una barra /.
            items=a.items[:] if a.kind=='row' and not isinstance(n.left,ast.UnaryOp) else [a]
            return row(*items,text(op),b)
        raise ValueError('Expresión no representable')
    source=tree(expression) if make_box else ast.parse(normalize(expression.replace(',','__COMMA__')).replace('__COMMA__',','),mode='eval')
    return build(source)

def boxes(node):
    if node.kind=='box':yield node.box
    for child in node.items:yield from boxes(child)

@dataclass
class Layout:
    width:float
    height:float
    axis:float
    ops:list=field(default_factory=list)
    slots:list=field(default_factory=list)

def compose(children,positions,width,height,axis):
    out=Layout(width,height,axis)
    for child,(x,y) in zip(children,positions):
        for kind,rect,value in child.ops:out.ops.append((kind,rect.move(round(x),round(y)),value))
        for rect,size in child.slots:out.slots.append((rect.move(round(x),round(y)),size))
    return out

def layout(node,width,scale=1,interactive=True):
    scale=max(.65,scale);gap=max(5,round(7*scale));size=max(14,round(18*scale))
    if node.kind=='text':
        img=ui.font(size).render(node.text,True,ui.TEXT)
        return Layout(img.get_width(),img.get_height(),img.get_height()/2,[('image',img.get_rect(),img)])
    if node.kind=='box':
        from classroom.engine import number
        font=ui.font(max(14,round(20*scale)))
        label=number(node.box.v)
        compact=float(node.box.v).is_integer()
        minimum=52 if compact else 88
        w=max(round(minimum*scale),font.size(label)[0]+round(26*scale));h=max(30,round(40*scale))
        return Layout(w,h,h/2,[],[(pygame.Rect(0,0,w,h),max(14,round(20*scale)))])
    if node.kind in ('absolute','paren','root'):
        child=layout(node.items[0],max(80,width-30*scale),scale,interactive)
        pad=max(10,round(12*scale));out=compose([child],[(pad,5)],child.width+pad*2,child.height+10,child.axis+5)
        color=ui.TEXT
        if node.kind=='absolute':
            out.ops+=[('rect',pygame.Rect(2,2,2,out.height-4),color),('rect',pygame.Rect(out.width-4,2,2,out.height-4),color)]
        elif node.kind=='root':
            img=ui.font(size+6).render('√',True,color);out.ops.append(('image',img.get_rect(topleft=(0,max(0,round(out.axis-img.get_height()/2)))),img))
            out.ops.append(('rect',pygame.Rect(pad,0,child.width+pad,2),color))
        else:
            # Curvas suavizadas; no se estira un glifo de pocos píxeles.
            for label,x in [('(',0),(')',out.width-pad+2)]:
                pw=max(8,pad-3);ph=max(size,round(out.height-2));factor=4
                img=pygame.Surface((pw*factor,ph*factor),pygame.SRCALPHA)
                rect=pygame.Rect(0 if label=='(' else -pw*factor,0,2*pw*factor,ph*factor)
                pygame.draw.arc(img,color,rect,math.pi/2 if label=='(' else -math.pi/2,3*math.pi/2 if label=='(' else math.pi/2,max(4,round(scale*4)))
                img=pygame.transform.smoothscale(img,(pw,ph))
                out.ops.append(('image',img.get_rect(topleft=(round(x),1)),img))
        return out
    if node.kind=='fraction':
        a=layout(node.items[0],max(90,width-20),scale,interactive);b=layout(node.items[1],max(90,width-20),scale,interactive)
        w=max(a.width,b.width)+16;axis=a.height+gap
        out=compose([a,b],[((w-a.width)/2,0),((w-b.width)/2,axis+gap)],w,a.height+b.height+2*gap,axis)
        out.ops.append(('rect',pygame.Rect(0,round(axis),round(w),2),ui.TEXT));return out
    if node.kind=='power':
        a=layout(node.items[0],width,scale,interactive);b=layout(node.items[1],max(80,width-a.width-8),max(.65,scale*.78),interactive)
        rise=max(b.height*.7,10*scale)
        return compose([a,b],[(0,rise),(a.width+3,0)],a.width+b.width+3,max(a.height+rise,b.height),a.axis+rise)
    if node.kind=='row':
        children=[layout(n,width,scale,interactive) for n in node.items]
        # Un signo de continuación se mueve junto con su operando: nunca
        # queda un +, − o producto aislado al final de un renglón.
        grouped=[];i=0
        while i<len(children):
            if node.items[i].kind=='text' and node.items[i].text in ('+','−','·',',') and i+1<len(children):
                a,b=children[i:i+2];axis=max(a.axis,b.axis)
                grouped.append(compose([a,b],[(0,axis-a.axis),(a.width+gap,axis-b.axis)],a.width+gap+b.width,axis+max(a.height-a.axis,b.height-b.axis),axis));i+=2
            else:grouped.append(children[i]);i+=1
        children=grouped
        lines=[];line=[];used=0
        for child in children:
            if line and used+gap+child.width>width:
                lines.append(line);line=[];used=0
            line.append(child);used+=child.width+(gap if len(line)>1 else 0)
        if line:lines.append(line)
        allchildren=[];positions=[];y=0;maxwidth=0;firstaxis=0
        for line in lines:
            axis=max(c.axis for c in line);bottom=max(c.height-c.axis for c in line);x=0
            if not allchildren:firstaxis=axis
            for c in line:allchildren.append(c);positions.append((x,y+axis-c.axis));x+=c.width+gap
            maxwidth=max(maxwidth,x-gap);y+=axis+bottom+gap+5
        return compose(allchildren,positions,maxwidth,max(0,y-gap-5),firstaxis)
    raise ValueError(node.kind)
