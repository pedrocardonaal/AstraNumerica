"""Eventos de sistemas: desarrollo del libro, capítulos 3.1–3.3.

Las importaciones del motor son diferidas para evitar dependencias circulares.
Se usa aritmética racional durante todas las transformaciones.
"""
from fractions import Fraction as F


def linear_event(kind, variant):
    from .engine import Problem, Field, Cell, Sheet, EquationSheet, number
    matrices=[[[2,5,-2],[-1,2,3],[3,-3,2]],
              [[3,-2,2],[4,2,2],[3,-3,3]],
              [[2,1,-3],[-1,3,2],[3,1,-3]]]
    original_rhs=[[1,2,3],[1,2,3],[-1,12,0]][kind]
    A=matrices[kind]
    rhs=[F(r)+variant*sum(row) for row,r in zip(A,original_rhs)]
    original=[[F(v) for v in row]+[r] for row,r in zip(A,rhs)]
    names=['Montante','Gauss-Jordán','Eliminación gaussiana']
    variables=['a','b','c'] if kind<2 else ['x₁','x₂','x₃']
    p=Problem(f'b{kind+4}-{variant}',names[kind],
       'Resuelve el sistema para recuperar un módulo de la estación.',
       'Resuelve el sistema. Completa cada transformación de la matriz, las incógnitas y la comprobación.',
       'N.E. = [(E.P.)(E.A.) − (E.C.F.P.)(E.C.C.P.)] ÷ P.A.' if kind==0 else '',[],
       ['Identifica el pivote y conserva los signos de la matriz anterior.',
        'En Montante se conserva la fila pivote; en Gauss-Jordán se divide entre el pivote; en eliminación se obtiene una matriz triangular.',
        'Sustituye las incógnitas en las tres ecuaciones originales para comprobar las igualdades.'],
       1200,0,[['',*variables,'']]+[[f'{i+1}',*[number(v) for v in row]] for i,row in enumerate(original)])
    def text(v):
        v=F(v)
        return str(v.numerator) if v.denominator==1 else number(v)
    def field(label,value,help='Desarrolla la operación mostrada sin descartar los datos intermedios.'):
        p.fields.append(Field(label,float(value),help));return Cell(len(p.fields)-1)
    def equation(label,numerator,denominator,value,suffix=''):
        p.sheets.append(EquationSheet('',label,numerator,denominator,suffix,field(label,value)))
    def matrix(title,m,changed):
        rows=[]
        for i,row in enumerate(m):
            rows.append([str(i+1)]+[field(f'{title}: fila {i+1}, {variables[j] if j<3 else "término independiente"}',v)
                         if (i,j) in changed else text(v) for j,v in enumerate(row)])
        p.sheets.append(Sheet(title,['',*variables,''],rows))
    m=[row[:] for row in original]
    if kind==0:
        previous=F(1)
        for k in range(3):
            old=[row[:] for row in m];pivot=old[k][k]
            p.sheets.append(Sheet(f'Pivote {text(pivot)}',['E.P.','P.A.'],[[text(pivot),text(previous)]]))
            changed=set()
            for i in range(3):
                if i==k:continue
                for j in range(4):
                    if j==k:m[i][j]=F(0);continue
                    m[i][j]=(pivot*old[i][j]-old[k][j]*old[i][k])/previous
                    equation('N.E. =',f'({text(pivot)})({text(old[i][j])}) − ({text(old[k][j])})({text(old[i][k])})',text(previous),m[i][j])
                    changed.add((i,j))
            matrix(f'Matriz después del pivote {k+1}',m,changed)
            previous=pivot
        solution=[m[i][3]/m[i][i] for i in range(3)]
        for i in range(3):equation(variables[i]+' =',text(m[i][3]),text(m[i][i]),solution[i])
    elif kind==1:
        for k in range(3):
            pivot=m[k][k];old=[row[:] for row in m]
            for j in range(4):
                m[k][j]=old[k][j]/pivot
                if j!=k:equation('=',text(old[k][j]),text(pivot),m[k][j])
            for i in range(3):
                if i==k:continue
                for j in range(4):
                    m[i][j]=old[i][j]-old[i][k]*m[k][j]
                    if j!=k:equation('=', '', '',m[i][j],f'{text(old[i][j])} − ({text(old[i][k])})({text(m[k][j])}) =')
            matrix(f'Matriz después del pivote {k+1}',m,{(i,j) for i in range(3) for j in range(4) if j!=k})
        solution=[m[i][3] for i in range(3)]
        p.sheets.append(Sheet('Incógnitas',variables,[[field(v,s) for v,s in zip(variables,solution)]]))
    else:
        for k in range(2):
            for i in range(k+1,3):
                factor=m[i][k]/m[k][k]
                p.sheets.append(Sheet(f'Renglón {k+1} multiplicado por {text(factor)}',variables+[''],
                    [[field(f'Producto del renglón {k+1}',v*factor) for v in m[k]]]))
                old=m[i][:]
                for j in range(4):
                    m[i][j]=old[j]-factor*m[k][j]
                    if j>k:equation('=','','',m[i][j],f'{text(old[j])} − ({text(factor)})({text(m[k][j])}) =')
                matrix(f'Renglón {i+1} menos el renglón multiplicado',m,{(i,j) for j in range(k+1,4)})
        solution=[F(0)]*3
        for i in reversed(range(3)):
            numerator=m[i][3]-sum(m[i][j]*solution[j] for j in range(i+1,3))
            solution[i]=numerator/m[i][i]
            expression=text(m[i][3])+''.join(f' − ({text(m[i][j])})({text(solution[j])})' for j in range(i+1,3))
            equation(variables[i]+' =',expression,text(m[i][i]),solution[i])
    rows=[]
    for i,row in enumerate(A):
        expression=' + '.join(f'({v})({text(s)})' for v,s in zip(row,solution))
        lhs=sum(v*s for v,s in zip(row,solution))
        assert lhs==rhs[i]
        rows.append([expression,field(f'Comprobación {i+1}',lhs),text(rhs[i])])
    p.sheets.append(Sheet('Comprobación',['Sustitución','Resultado','Igualdad'],rows))
    p.final=float(solution[0])
    return p
