"""Campos de desarrollo: se valida la operación escrita, además de su valor.

No ejecuta código del usuario. Las expresiones se interpretan con un AST cerrado.
"""
import ast
import math
import re
from dataclasses import dataclass

@dataclass(frozen=True)
class Expression:
    reference: str
    variables: tuple = ()

@dataclass
class Rich:
    blocks: list

FUNCTIONS={'exp':math.exp,'ln':math.log,'log':math.log,'sqrt':math.sqrt,
           'sin':math.sin,'sen':math.sin,'cos':math.cos,'tan':math.tan,'abs':abs}

def normalize(text):
    s=str(text).strip().replace('−','-').replace('×','*').replace('·','*').replace('÷','/').replace(',','.')
    s=s.replace('[','(').replace(']',')').replace('{','(').replace('}',')')
    s=s.replace('π','pi').replace('²','^2').replace('³','^3').replace('⁴','^4').replace('⁵','^5').replace('⁶','^6')
    s=s.replace('½','(1/2)').replace('⅙','(1/6)').replace('⅛','(1/8)').replace('⅔','(2/3)')
    # |a-b| es la notación de los PDF para valor absoluto.
    if s.count('|')==2:
        a,b=s.index('|'),s.rindex('|');s=s[:a]+'abs('+s[a+1:b]+')'+s[b+1:]
    s=re.sub(r'(\d+)\s*!',lambda m:str(math.factorial(int(m[1]))) if int(m[1])<=10 else 'INVALID',s)
    s=s.replace('^','**')
    # Multiplicación implícita habitual: 2(3), (2)(3), 2x, 2exp(x).
    s=re.sub(r'(?<=[\d)])\s*(?=[(a-zA-Z])','*',s)
    s=re.sub(r'\)\s*(?=\d)',')*',s)
    return s

def tree(text):
    if len(str(text))>600:raise ValueError('Expresión demasiado larga')
    n=ast.parse(normalize(text),mode='eval')
    if len(list(ast.walk(n)))>220:raise ValueError('Expresión demasiado extensa')
    return n

def evaluate(node,values=None,depth=0):
    if depth>35:raise ValueError('Expresión demasiado profunda')
    values=values or {}
    ev=lambda n:evaluate(n,values,depth+1)
    if isinstance(node,ast.Expression):v=ev(node.body)
    elif isinstance(node,ast.Constant) and type(node.value) in (int,float):v=float(node.value)
    elif isinstance(node,ast.Name):
        if node.id in values:v=values[node.id]
        elif node.id=='e':v=math.e
        elif node.id=='pi':v=math.pi
        else:raise ValueError('Variable no permitida')
    elif isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
        v=ev(node.operand)*(1 if isinstance(node.op,ast.UAdd) else -1)
    elif isinstance(node,ast.BinOp):
        a,b=ev(node.left),ev(node.right)
        if isinstance(node.op,ast.Add):v=a+b
        elif isinstance(node.op,ast.Sub):v=a-b
        elif isinstance(node.op,ast.Mult):v=a*b
        elif isinstance(node.op,ast.Div):v=a/b
        elif isinstance(node.op,ast.Pow):
            if abs(b)>12 or abs(a)>1e12:raise ValueError('Potencia fuera de rango')
            v=a**b
        else:raise ValueError('Operador no permitido')
    elif isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in FUNCTIONS and len(node.args)==1 and not node.keywords:
        v=FUNCTIONS[node.func.id](ev(node.args[0]))
    else:raise ValueError('Sintaxis no permitida')
    if not isinstance(v,(int,float)) or not math.isfinite(v) or abs(v)>1e100:raise ValueError('Valor fuera de rango')
    return v

def numeric(text):return evaluate(tree(text))

def valid(text,expected):
    try:
        actual=tree(text);reference=tree(expected.reference)
        if expected.variables:
            # Comparación funcional en varios puntos; no se acepta una constante.
            names={n.id for n in ast.walk(actual) if isinstance(n,ast.Name)}
            if not set(expected.variables)<=names:return False
            for point in (.23,.61,1.13,1.79,2.37):
                values={name:point+.17*i for i,name in enumerate(expected.variables)}
                a,b=evaluate(actual,values),evaluate(reference,values)
                if abs(a-b)>max(2e-7,abs(b)*2e-7):return False
            return True
        a,b=evaluate(actual),evaluate(reference)
        if abs(a-b)>max(3e-6,abs(b)*3e-6):return False
        # Un resultado aislado no demuestra la sustitución. Se requieren los
        # operandos de la referencia, sin imponer espacios u orden textual.
        def operands(n):return sorted(float(v.value) for v in ast.walk(n) if isinstance(v,ast.Constant) and type(v.value) in (int,float))
        required=operands(reference);got=operands(actual)
        operations=lambda n:sum(isinstance(v,(ast.BinOp,ast.Call)) for v in ast.walk(n))
        if operations(reference) and not operations(actual):return False
        for value in required:
            match=next((i for i,z in enumerate(got) if abs(z-value)<=max(7e-7,abs(value)*2e-7)),None)
            if match is None:return False
            got.pop(match)
        return True
    except (ValueError,SyntaxError,TypeError,OverflowError,ZeroDivisionError,RecursionError):return False
