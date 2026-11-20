"""Texto suavizado, glifos matemáticos y exponentes elevados."""
from pathlib import Path
import os
import re
import pygame

_NEG=re.compile(r'(?<![\w.)\]])-(?=[\d.])|(?<=\s)-(?=\s)')

def normalize_minus(text):
    """Signo menos tipográfico uniforme (−) en números negativos y restas."""
    return _NEG.sub('−',str(text))

class MathFont:
    def __init__(self,size,bold=False):
        self.point_size=size;self.bold=bold;self._exponent=None
        folder=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'
        self.fonts=[]
        for name in (('segoeuib.ttf' if bold else 'segoeui.ttf'),('arialbd.ttf' if bold else 'arial.ttf'),'seguisym.ttf','cambria.ttc'):
            if (folder/name).exists():self.fonts.append(pygame.font.Font(str(folder/name),size))
        if not self.fonts:self.fonts=[pygame.font.SysFont('segoeui',size,bold=bold)]
        self.missing=[f.metrics('\U0010ffff')[0] for f in self.fonts]
        self.choices={};self.ascent=max(f.get_ascent() for f in self.fonts)
        self.height=self.ascent+max(abs(f.get_descent()) for f in self.fonts)
    def select(self,ch):
        if ch not in self.choices:
            selected=0
            for i,f in enumerate(self.fonts):
                m=f.metrics(ch)[0]
                if m is not None and m!=self.missing[i]:selected=i;break
            self.choices[ch]=selected
        return self.choices[ch]
    def runs(self,text):
        runs=[]
        for ch in normalize_minus(text):
            index=self.select(ch)
            if runs and runs[-1][0]==index:runs[-1]=(index,runs[-1][1]+ch)
            else:runs.append((index,ch))
        return runs
    def parts(self,text):
        """Dibuja cualquier potencia con exponente elevado, sin mostrar ^."""
        text=normalize_minus(text);parts=[];start=0;cursor=0
        while cursor<len(text):
            begin=text.find('^',cursor)
            if begin<0:break
            if begin+1<len(text) and text[begin+1]=='(':
                depth=1;end=begin+2
                while end<len(text) and depth:
                    if text[end]=='(':depth+=1
                    elif text[end]==')':depth-=1
                    end+=1
                if depth:break
                exponent=text[begin+2:end-1]
            else:
                match=re.match(r'[+−-]?(?:\d+(?:\.\d+)?|[A-Za-z][A-Za-z0-9]*)',text[begin+1:])
                if not match:cursor=begin+1;continue
                exponent=match[0];end=begin+1+len(match[0])
            parts.append((False,text[start:begin]))
            parts.append((True,exponent));start=end;cursor=end
        parts.append((False,text[start:]));return parts
    def exponent_font(self):
        if self._exponent is None:self._exponent=MathFont(max(10,round(self.point_size*.73)),self.bold)
        return self._exponent
    def plain_width(self,text):return sum(self.fonts[i].size(s)[0] for i,s in self.runs(text))
    def size(self,text):
        return sum((self.exponent_font() if raised else self).plain_width(s) for raised,s in self.parts(text)),self.height
    def get_linesize(self):return self.height
    def render(self,text,antialias,color,background=None):
        width,_=self.size(text);image=pygame.Surface((max(1,width),self.height),pygame.SRCALPHA)
        if background is not None:image.fill(background)
        x=0
        for raised,part in self.parts(text):
            owner=self.exponent_font() if raised else self
            for i,s in owner.runs(part):
                f=owner.fonts[i];glyphs=f.render(s,antialias,color)
                y=max(0,self.ascent-f.get_ascent()-round(self.point_size*.35)) if raised else self.ascent-f.get_ascent()
                image.blit(glyphs,(x,y));x+=glyphs.get_width()
        return image
