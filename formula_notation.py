"""Fórmulas de clase compuestas como matemáticas, no como código."""
from math_notation import from_expression,row,text,fraction

def formulas(problem,method):
    v=problem.get('variant',0);items=[]
    def add(label,expression):items.append((label,from_expression(expression)))
    def error():add('ε =','abs(x_next-x_i)')
    if method==0:
        add('g(x) =','(f_b-f_a)/(b-a)*(x-a)+f_a');add('ε =','abs(f_x-g_x)')
    elif method==1:
        # Expansión de cuatro términos, como la fórmula desarrollada del PDF.
        for i in range(1,5):
            num='*'.join(f'(x-x{j})' for j in range(1,5) if j!=i)
            den='*'.join(f'(x{i}-x{j})' for j in range(1,5) if j!=i)
            add('g(x) =' if i==1 else '+',f'y{i}*(({num})/({den}))')
    elif method==5:
        add('h =','abs(x_next-x_i)');add('g(x) =','D0+D11*(x-x1)+D21*(x-x1)*(x-x2)')
    elif method in (6,7):
        add('h =','abs(x_next-x_i)');add('s =','(x-x_i)/h')
        d='nabla' if method==7 else 'delta';sign='+' if method==7 else '-'
        numerator=from_expression(f'{d}2*s*(s{sign}1)')
        items.append(('g(x) =',row(from_expression(f'y_i+{d}1*s'),text('+'),fraction(numerator,text('2!')))))
    elif method==2:add('f(x) =','0')
    elif method==3:add('x =','(a+b)/2');error()
    elif method==4:add('xᵢ₊₁ =','x_i-f_xi/df_xi');error()
    elif method==8:add('x =','a-f_a*(b-a)/(f_b-f_a)');error()
    elif method==9:add('xᵢ₊₁ =','exp(-x_i)'+('' if v==0 else f'/{1+v*.1:g}'));error()
    elif method==10:add('xᵢ₊₂ =','x_next-f_next*(x_next-x_i)/(f_next-f_xi)');error()
    elif method in (11,12):
        for equation in problem['formula'].split('\n')[0].split(';'):
            left,right=equation.split('=',1);add(left.strip()+' =',right.strip())
        for name in 'abc':add('ε'+name+' =',f'abs({name}_i-{name}_prev)')
    elif method in (13,14,15,16,17):
        degree={13:1,14:2,15:3,16:1,17:2}[method]
        expr='+'.join('a'+str(i)+('' if i==0 else '*x' if i==1 else '*x^'+str(i)) for i in range(degree+1))
        if method in (16,17):expr+=f'+a{degree+1}*exp(x)'
        add('g(x) =',expr)
    elif method in (18,19,20,21,22):
        add('h =','(b-a)/(n+2)' if method==22 else '(b-a)/n');add('x =','a+i*h')
        weights={18:[1,2,2,2,1],19:[1,4,2,4,1],20:[1,3,3,1],21:[7,32,12,32,7],22:[0,11,-14,26,-14,11,0]}[method]
        factor={18:'h/2',19:'h/3',20:'3*h/8',21:'2*h/45',22:'6*h/20'}[method]
        terms=[]
        for i,c in enumerate(weights):
            arg='a' if i==0 else 'b' if i==len(weights)-1 else f'a+{i}*h'
            terms.append(('' if c==1 else f'({c})*')+f'f({arg})')
        add('I =',f'({factor})*('+'+'.join(terms)+')')
    elif method==23:add('y′ₙ₊₁ =','y_n+h/2*(f(y_n,t_n)+f(y_next,t_next))')
    elif method in (24,25,26,27):
        add('k₁ =','h*f(y_n,t_n)')
        if method==24:add('k₂ =','h*f(y_n+k1,t_n+h)');add('yₙ₊₁ =','y_n+(k1+k2)/2')
        else:
            d=3 if method==27 else 2
            add('k₂ =',f'h*f(y_n+k1/{d},t_n+h/{d})')
            if method==25:add('k₃ =','h*f(y_n-k1+2*k2,t_n+h)');add('yₙ₊₁ =','y_n+(k1+4*k2+k3)/6')
            elif method==26:
                add('k₃ =','h*f(y_n+k2/2,t_n+h/2)');add('k₄ =','h*f(y_n+k3,t_n+h)');add('yₙ₊₁ =','y_n+(k1+2*k2+2*k3+k4)/6')
            else:
                add('k₃ =','h*f(y_n+k1/3+k2/3,t_n+2*h/3)');add('k₄ =','h*f(y_n+k1-k2+k3,t_n+h)');add('yₙ₊₁ =','y_n+(k1+3*k2+3*k3+k4)/8')
    elif method==28:
        for label,expr in [('Vₙ =','dy'),('Uₙ =','y'),('qₙ =','t'),('k₁ =','h*V_n'),('m₁ =','h*(a*V_n*q_n+b*U_n)'),('k₂ =','h*(V_n+m1)'),('m₂ =','h*(a*(V_n+m1)*(q_n+h)+b*(U_n+k1))'),('yₙ₊₁ =','y_n+(k1+k2)/2'),('y′ₙ₊₁ =','dy+(m1+m2)/2')]:add(label,expr)
    elif method=='b4':add('N.E. =','(EP*EA-ECFP*ECCP)/PA')
    return items
