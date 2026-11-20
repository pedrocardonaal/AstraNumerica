"""Hojas de clase dibujadas dentro de la interfaz recibida, sin ventanas externas."""
import math
import pygame
import ui,engine
from classroom.procedure import Rich,Expression
from math_notation import Math,layout as math_layout,row as math_row,text as math_text
from formula_notation import formulas

def align_decimals(tb):
    """Columnas numéricas con la misma cantidad de decimales (1.5000, 2.1077, 3.0000)."""
    rows=[list(r) for r in tb['rows']]
    for j in range(len(tb['headers'])):
        vals=[]
        for r in rows:
            c=r[j] if j<len(r) else None
            if isinstance(c,bool) or c is None:vals=None;break
            try:vals.append(float(str(c).replace('−','-')))
            except ValueError:vals=None;break
        if not vals:continue
        # Conservar el valor presentado y los enteros sin ceros de relleno.
        for r,v in zip(rows,vals):r[j]=string(v)
    out=dict(tb);out['rows']=rows;return out

def string(v):return engine.core.number(v) if isinstance(v,(int,float)) else str(v)

def plot_surface(s,width,height=250):
    image=pygame.Surface((width,height));image.fill(ui.BG)
    points=[p for curve in s['curves'] for p in curve]
    xmin=min(0,min(p[0] for p in points));xmax=max(p[0] for p in points)
    ymin=min(0,min(p[1] for p in points));ymax=max(p[1] for p in points)
    dx=max(.1,xmax-xmin);dy=max(.1,ymax-ymin);xmin-=dx*.08;xmax+=dx*.08;ymin-=dy*.1;ymax+=dy*.1
    def pos(x,y):return (45+(x-xmin)/(xmax-xmin)*(width-70),height-32-(y-ymin)/(ymax-ymin)*(height-55))
    ax,ay=pos(0,0);pygame.draw.line(image,ui.TEXT_DIM,(35,ay),(width-15,ay));pygame.draw.line(image,ui.TEXT_DIM,(ax,15),(ax,height-25))
    for i in range(5):
        xx=xmin+(xmax-xmin)*i/4;yy=ymin+(ymax-ymin)*i/4
        img=ui.font(12).render(engine.core.number(xx,2),True,ui.TEXT_DIM);image.blit(img,(pos(xx,0)[0]-10,height-18))
        img=ui.font(12).render(engine.core.number(yy,2),True,ui.TEXT_DIM);image.blit(img,(3,pos(0,yy)[1]-6))
    for k,curve in enumerate(s['curves']):
        color=[ui.ACCENT,ui.WARN][k%2];pts=[pos(*p) for p in curve]
        if len(pts)>1:pygame.draw.lines(image,color,False,pts,2)
        if len(pts)<15:
            for pt in pts:pygame.draw.circle(image,color,pt,3)
        text=ui.font(13).render(s['labels'][k],True,color);image.blit(text,(width-text.get_width()-12,12+k*18))
    return image

class Worksheet:
    def __init__(self,problem,width=680,scale=1,hints=0,hint_texts=None,reveal=True):
        self.reveal=reveal;self.width=width;self.scale=scale;self.ops=[];self.slots=[];self.slot_sizes=[];self.focus_groups=[];self.sections=[(8,'Datos del problema')];self.tables=[];self.horizontal_regions=[];self.y=8;self.max_width=width
        self.problem=problem
        self.text(problem['prompt'],18)
        if problem.get('data'):self.table(align_decimals(problem['data']),False)
        elif problem.get('initial_text'):self.text(problem['initial_text'],18)
        if problem.get('formula'):
            self.text('Fórmulas',21,bold=True)
            method=engine.SPECS.get(problem.get('mission_id'),(None,))[0]
            formal=formulas(problem,method)
            if formal:
                for label,node in formal:
                    self.y+=self.math(math_row(math_text(label),node),12,self.y,self.width-24)+18
            else:self.text(problem['formula'],18,ui.TEXT)
            for table in problem.get('formula_tables',[]):self.table(table,False)
        for i in range(hints):self.text(f'Pista {i+1}: '+((hint_texts[i] if hint_texts and hint_texts[i] else None) or ('Consulta las fórmulas de la parte superior.' if i==0 else problem[f'hint{i+1}'])),16,ui.WARN)
        self.text('Procedimiento',21,bold=True)
        self.text('Completa las casillas de cada sustitución y después su resultado. Las potencias se llenan arriba, las fracciones arriba y abajo, y el valor absoluto entre barras. Tab: siguiente casilla.',15)
        for step in problem['steps']:
            if step['kind']=='table':self.table(step,True)
            elif step['kind']=='equation':self.equation(step)
            elif step['kind']=='plot':self.plot(step)
            elif step['kind']=='rich':self.rich(step['content'],0,self.y,self.width)
        self.height=self.y+16

    def size(self,n):return max(12,round(n*self.scale))
    def image(self,text,size,color=None,bold=False):return ui.font(self.size(size),bold).render(string(text),True,color or ui.TEXT)
    def op_image(self,image,x,y):
        self.ops.append(('image',pygame.Rect(x,y,image.get_width(),image.get_height()),image))
        self.max_width=max(self.max_width,x+image.get_width()+6)
    def text(self,text,size=17,color=None,bold=False,width=None,x=0):
        color=color or ui.TEXT
        if bold and size>=18:self.sections.append((self.y,string(text)))
        font=ui.font(self.size(size),bold)
        for line in ui.wrap_lines(string(text),font,width or self.width):
            image=font.render(line,True,color)
            self.ops.append(('fixed_image',pygame.Rect(x,self.y,image.get_width(),image.get_height()),image));self.y+=font.get_linesize()
        self.y+=9
    def rect(self,rect,color):self.ops.append(('rect',pygame.Rect(rect),color))
    def slot(self,x,y,width,height,font_size=None):
        self.slots.append(pygame.Rect(round(x),round(y),round(width),round(height)))
        self.slot_sizes.append(font_size or self.size(20))
        self.max_width=max(self.max_width,x+width+8)
    def math(self,node,x,y,width):
        result=math_layout(node,width,self.scale)
        first=len(self.slots)
        for kind,rect,value in result.ops:
            rect=rect.move(round(x),round(y))
            if kind=='image':self.op_image(value,rect.x,rect.y)
            else:self.rect(rect,value)
        for rect,size in result.slots:
            rect=rect.move(round(x),round(y));self.slot(rect.x,rect.y,rect.width,rect.height,size)
        if len(self.slots)>first:self.focus_groups.append((first,len(self.slots),pygame.Rect(round(x-5),round(y-5),round(result.width+10),round(result.height+10))))
        self.max_width=max(self.max_width,x+result.width+8)
        return result.height
    def input_height(self,c,width):
        if isinstance(c,Math):return math_layout(c,max(80,width),self.scale).height
        if isinstance(c.v,Expression):
            text=engine.answer_text(c.v)
            return max(self.size(58),len(ui.wrap_lines(text,ui.font(self.size(18)),max(50,width-24)))*ui.font(self.size(18)).get_linesize()+26)
        return self.size(42)

    def rich_height(self,c,width):
        height=12
        for block in c.blocks:
            if block[0]=='text':height+=ui.text_height(block[1],self.size(17),False,max(60,width-24))+12
            elif block[0]=='input':height+=self.input_height(block[1],width-24)+12
            elif block[0] in ('label','lead'):height+=max(self.size(42),self.input_height(block[2],width-100))+12
            elif block[0]=='fraction':height+=sum(self.input_height(b,width-36) for b in block[1:])+24
            elif block[0]=='mathfraction':height+=sum(ui.text_height(s,self.size(17),False,width-24) for s in block[1:])+30
            elif block[0]=='binomial':height+=self.size(60)
        return height+8

    def rich(self,c,x,top,width,advance=True):
        y=top+10
        for block in c.blocks:
            if block[0]=='text':
                font=ui.font(self.size(17))
                for line in ui.wrap_lines(block[1],font,width-24):
                    img=font.render(line,True,ui.TEXT);self.op_image(img,x+12,y);y+=font.get_linesize()
                y+=12
            elif block[0]=='input':
                h=self.input_height(block[1],width-24)
                if isinstance(block[1],Math):self.math(block[1],x+12,y,width-24)
                else:self.slot(x+12,y,width-24,h)
                y+=h+12
            elif block[0] in ('label','lead'):
                label=self.image(block[1],17);lw=min(width//2,label.get_width()+18)
                trailing=36 if block[0]=='lead' else 0
                h=self.input_height(block[2],width-lw-24-trailing)
                bw=min(width-lw-12-trailing,max(self.size(136),self.image(engine.answer_text(block[2].v),20).get_width()+self.size(26)))
                self.op_image(label,x+12,y+(h-label.get_height())/2);self.slot(x+lw,y,bw,h)
                if trailing:self.op_image(self.image(block[3],20),x+lw+bw+10,y+8)
                y+=h+12
            elif block[0]=='fraction':
                for i,b in enumerate(block[1:]):
                    h=self.input_height(b,width-36)
                    if isinstance(b,Math):self.math(b,x+18,y,width-36)
                    else:self.slot(x+18,y,width-36,h)
                    y+=h+8
                    if i==0:self.rect((x+12,y-2,width-24,2),ui.TEXT);y+=8
            elif block[0]=='mathfraction':
                font=ui.font(self.size(17))
                for i,text in enumerate(block[1:]):
                    for line in ui.wrap_lines(text,font,width-24):
                        img=font.render(line,True,ui.TEXT);self.op_image(img,x+(width-img.get_width())/2,y);y+=font.get_linesize()
                    y+=8
                    if i==0:self.rect((x+12,y-3,width-24,2),ui.TEXT);y+=8
                y+=6
            elif block[0]=='binomial':
                h=self.size(48);parenthesis=ui.font(h)
                self.op_image(parenthesis.render('(',True,ui.TEXT),x+12,y-6)
                self.op_image(self.image(block[1],17),x+32,y)
                self.op_image(self.image(block[2],17),x+32,y+self.size(22))
                self.op_image(parenthesis.render(')',True,ui.TEXT),x+52,y-6)
                self.op_image(self.image(block[3],18),x+78,y+self.size(10));y+=self.size(60)
        if advance:self.y=y+20
    def table(self,tb,interactive):
        if tb.get('title'):self.text(tb['title'],18,ui.ACCENT,True)
        headers,rows=tb['headers'],tb['rows'];cols=len(headers)
        widths=[]
        for j,h in enumerate(headers):
            desired=ui.font(self.size(16),True).size(string(h))[0]+24
            for row in rows:
                c=row[j] if j<len(row) else ''
                if isinstance(c,Math):measure=math_layout(c,round(280*self.scale),self.scale).width+24
                elif isinstance(c,Rich):
                    measure=round(182*self.scale)
                    for block in c.blocks:
                        if block[0] in ('fraction','mathfraction'):measure=max(measure,round(330*self.scale))
                        elif block[0]=='input' and isinstance(block[1],Math):measure=max(measure,math_layout(block[1],round(260*self.scale),self.scale).width+24)
                elif isinstance(c,engine.B):measure=round((320 if isinstance(c.v,Expression) else 130)*self.scale)
                else:measure=min(round(340*self.scale),ui.font(self.size(17)).size(string(c))[0]+24)
                desired=max(desired,measure)
            widths.append(max(round(80*self.scale),min(desired,round(360*self.scale))))
        narrow=bool(headers and headers[0] in ('i',''))
        if narrow:widths[0]=self.size(50)
        if sum(widths)<self.width:
            indices=list(range(1 if narrow else 0,cols))
            add=(self.width-sum(widths))/max(1,len(indices));widths=[int(w+add) if j in indices else w for j,w in enumerate(widths)]
        if cols==3 and headers[0]=='i' and headers[1] in ('xᵢ','xᵢ₊₁') and self.width>=850 and self.scale<=1.25:
            # En la referencia, el desarrollo ocupa la mayor parte de la tabla;
            # el índice y el error son columnas auxiliares estrechas.
            remainder=self.width-widths[0];widths[1]=round(remainder*.77);widths[2]=remainder-widths[1]
        total=sum(widths);self.max_width=max(self.max_width,total)
        header_y=self.y;header_op=len(self.ops)
        if interactive:self.sections.append((self.y,tb.get('title') or 'Tabla · '+' / '.join(map(string,headers))))
        font=ui.font(self.size(15),True)
        hh=max(ui.text_height(string(h),self.size(15),True,widths[j]-16) for j,h in enumerate(headers))+16
        self.rect((0,self.y,total,hh),ui.TABLE_HEAD)
        x=0
        for j,h in enumerate(headers):
            yy=self.y+7
            for line in ui.wrap_lines(string(h),font,widths[j]-16):
                image=font.render(line,True,ui.TEXT);self.op_image(image,x+(widths[j]-image.get_width())/2,yy);yy+=font.get_linesize()
            x+=widths[j]
        self.y+=hh;header_ops=self.ops[header_op:].copy()
        for ri,row in enumerate(rows):
            row_first=len(self.slots)
            rh=round(48*self.scale) if interactive else round(34*self.scale)
            for j,c in enumerate(row):
                if isinstance(c,Math):rh=max(rh,self.input_height(c,widths[j]-16)+20)
                elif isinstance(c,Rich):rh=max(rh,self.rich_height(c,widths[j]))
                elif isinstance(c,engine.B):rh=max(rh,self.input_height(c,widths[j]-16)+12)
                else:rh=max(rh,ui.text_height(string(c),self.size(17),False,widths[j]-18)+16)
            self.rect((0,self.y,total,rh),ui.TABLE_ROW if ri%2==0 else ui.TABLE_ALT)
            x=0
            for j,c in enumerate(row):
                if isinstance(c,Math):self.math(c,x+8,self.y+10,widths[j]-16)
                elif isinstance(c,Rich):self.rich(c,x,self.y,widths[j],False)
                elif isinstance(c,engine.B):
                    bw=min(widths[j]-16,max(self.size(136),self.image(engine.answer_text(c.v),20).get_width()+self.size(26)))
                    self.slot(x+(widths[j]-bw)/2,self.y+6,bw,min(rh-12,self.input_height(c,widths[j]-16)))
                else:
                    font=ui.font(self.size(17));lines=ui.wrap_lines(string(c),font,widths[j]-18)
                    yy=self.y+(rh-len(lines)*font.get_linesize())/2
                    for line in lines:
                        img=font.render(line,True,ui.TEXT);self.op_image(img,x+(widths[j]-img.get_width())/2,yy);yy+=font.get_linesize()
                x+=widths[j]
            if len(self.slots)>row_first:self.focus_groups.append((row_first,len(self.slots),pygame.Rect(0,self.y,total,rh)))
            self.y+=rh
        self.tables.append((header_y,self.y,hh,header_ops));self.horizontal_regions.append((header_y,self.y,total));self.y+=20

    def visible_width(self,scroll,height):
        widths=[width for start,end,width in self.horizontal_regions if min(end,scroll+height)-max(start,scroll)>28]
        return max([self.width,*widths])

    def section_at(self,scroll):
        result='Datos del problema'
        for y,title in self.sections:
            if y<=scroll+35:result=title
        return result

    def sticky_height(self,scroll):
        return next((height+8 for start,end,height,ops in self.tables if start<scroll and scroll+height<end),0)

    def draw_sticky(self,surface,view,x,scroll,hscroll):
        for start,end,height,ops in self.tables:
            if start<scroll and scroll+height<end:
                for kind,rect,content in ops:
                    dest=rect.move(x-hscroll,view.y+6-start)
                    if kind=='rect':pygame.draw.rect(surface,content,dest)
                    else:surface.blit(content,dest)
                return

    def equation(self,s):
        if s.get('title'):self.text(s['title'],18,ui.ACCENT,True)
        left=self.image(s.get('left',''),18);num=self.image(s.get('numerator',''),18)
        den=self.image(s.get('denominator',''),18);suffix=self.image(s.get('suffix',''),18)
        has_fraction=bool(s.get('denominator'));fh=num.get_height()+den.get_height()+12 if has_fraction else left.get_height()
        h=max(round(58*self.scale),fh+18);x=10;top=self.y
        self.op_image(left,x,top+(h-left.get_height())/2);x+=left.get_width()+10
        if has_fraction:
            fw=max(num.get_width(),den.get_width())+16
            self.op_image(num,x+(fw-num.get_width())/2,top+8)
            self.rect((x,top+num.get_height()+13,fw,2),ui.TEXT)
            self.op_image(den,x+(fw-den.get_width())/2,top+num.get_height()+19);x+=fw+12
        if suffix.get_width():self.op_image(suffix,x,top+(h-suffix.get_height())/2);x+=suffix.get_width()+12
        if s.get('result') is not None:self.slot(x,top+(h-round(38*self.scale))/2,round(145*self.scale),round(38*self.scale));x+=round(155*self.scale)
        # El fondo se inserta antes de los glifos para mantener las fracciones visibles.
        bg=('rect',pygame.Rect(0,top,max(self.width,x),h),(22,34,58))
        first=len(self.ops)
        while first>0 and self.ops[first-1][1].top>=top:first-=1
        self.ops.insert(first,bg);self.max_width=max(self.max_width,x);self.y+=h+20

    def plot(self,s):
        self.text(s['title'],18,ui.ACCENT,True);height=250
        if not self.reveal and len(s['curves'])>1:
            image=pygame.Surface((self.width,height));image.fill(ui.PANEL_LIGHT)
            pygame.draw.rect(image,ui.ACCENT_SOFT,image.get_rect(),2,border_radius=10)
            font=ui.font(self.size(17))
            lines=ui.wrap_lines('La gráfica se revela al completar correctamente el problema.',font,self.width-40)
            for i,line in enumerate(lines):
                msg=font.render(line,True,ui.TEXT_DIM)
                image.blit(msg,msg.get_rect(center=(self.width//2,height//2+(i-(len(lines)-1)/2)*font.get_linesize())))
        else:image=plot_surface(s,self.width,height)
        self.op_image(image,0,self.y);self.y+=height+20



    def draw(self,surface,view,x,scroll,hscroll,inputs,draw=True):
        for i,slot in enumerate(self.slots):
            inp=inputs[i];inp.cy=slot.y;inp.cx=slot.x;inp.rect=slot.move(x-hscroll,view.y-scroll);inp.font_size=self.slot_sizes[i]
        if not draw:return
        old=surface.get_clip();surface.set_clip(view.inflate(-6,-6))
        for kind,rect,content in self.ops:
            dest=rect.move(x if kind=='fixed_image' else x-hscroll,view.y-scroll)
            if not view.colliderect(dest):continue
            if kind=='rect':pygame.draw.rect(surface,content,dest)
            else:surface.blit(content,dest)
        active=next((i for i,inp in enumerate(inputs) if inp.active),None)
        if active is not None:
            candidates=[rect for first,last,rect in self.focus_groups if first<=active<last]
            rect=min(candidates,key=lambda r:r.width*r.height) if candidates else self.slots[active].inflate(10,10)
            rect=rect.move(x-hscroll,view.y-scroll).clip(view.inflate(-12,-12))
            if rect.width>0 and rect.height>0:
                tint=pygame.Surface(rect.size,pygame.SRCALPHA);tint.fill((*ui.ACCENT,14));surface.blit(tint,rect)
                pygame.draw.line(surface,ui.ACCENT,rect.topleft,(rect.left,rect.bottom),2)
        surface.set_clip(old)
