"""Lista desplegable desplazable, integrada en el estilo del juego."""
import time
import pygame
import ui

class Dropdown:
    def __init__(self,rect,options,index=0):
        self.rect=pygame.Rect(rect);self.options=list(options);self.index=index
        self.open=False;self.scroll=0;self.cursor=index;self.search='';self.search_time=0
        self.row_height=34;self.max_rows=10
    def popup(self,height):
        rows=min(self.max_rows,len(self.options));h=rows*self.row_height
        y=self.rect.bottom+3 if height-self.rect.bottom>=h+8 else self.rect.top-h-3
        return pygame.Rect(self.rect.x,max(5,y),self.rect.width,h)
    def reveal(self):
        rows=min(self.max_rows,len(self.options))
        if self.cursor<self.scroll:self.scroll=self.cursor
        if self.cursor>=self.scroll+rows:self.scroll=self.cursor-rows+1
        self.scroll=max(0,min(self.scroll,max(0,len(self.options)-rows)))
    def collapse(self):self.open=False
    def draw(self,surf,popup_only=False):
        if not popup_only:
            ui.panel(surf,self.rect,glow=ui.ACCENT if self.open else ui.ACCENT_SOFT,radius=9,fill=ui.PANEL_LIGHT)
            text=self.options[self.index];font=ui.font(19)
            while text and font.size(text)[0]>self.rect.width-48:text=text[:-2]+'…' if not text.endswith('…') else text[:-2]+'…'
            img=font.render(text,True,ui.TEXT);surf.blit(img,img.get_rect(midleft=(self.rect.x+12,self.rect.centery)))
            x=self.rect.right-22;y=self.rect.centery
            pygame.draw.polygon(surf,ui.ACCENT,[(x-6,y-3),(x+6,y-3),(x,y+4)])
            return
        if not self.open:return
        rect=self.popup(surf.get_height());ui.panel(surf,rect,glow=ui.ACCENT,radius=6,fill=ui.PANEL)
        mouse=pygame.mouse.get_pos();rows=min(self.max_rows,len(self.options))
        for row in range(rows):
            i=self.scroll+row;r=pygame.Rect(rect.x+3,rect.y+row*self.row_height+2,rect.width-15,self.row_height-2)
            if r.collidepoint(mouse) or i==self.cursor:pygame.draw.rect(surf,ui.TABLE_HEAD,r,border_radius=4)
            text=self.options[i];font=ui.font(18)
            while text and font.size(text)[0]>r.width-20:text=text[:-2]+'…'
            img=font.render(text,True,ui.ACCENT if i==self.index else ui.TEXT);surf.blit(img,img.get_rect(midleft=(r.x+8,r.centery)))
        if len(self.options)>rows:
            track=pygame.Rect(rect.right-9,rect.y+4,4,rect.height-8);pygame.draw.rect(surf,ui.ACCENT_SOFT,track)
            h=max(20,track.height*rows/len(self.options));y=track.y+(track.height-h)*self.scroll/(len(self.options)-rows)
            pygame.draw.rect(surf,ui.ACCENT,(track.x,y,4,h))
    def handle(self,event,height):
        """True consume el evento para que no pulse un botón situado detrás."""
        if not self.open:
            if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and self.rect.collidepoint(event.pos):
                self.open=True;self.cursor=self.index;self.search='';self.reveal();return True
            return False
        rect=self.popup(height);rows=min(self.max_rows,len(self.options))
        if event.type==pygame.MOUSEWHEEL:
            self.scroll=max(0,min(len(self.options)-rows,self.scroll-event.y*3))
            self.cursor=max(self.scroll,min(self.scroll+rows-1,self.cursor));return True
        if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            if rect.collidepoint(event.pos):
                # La barra también se puede pulsar para saltar por la lista.
                if event.pos[0]>=rect.right-13 and len(self.options)>rows:
                    fraction=(event.pos[1]-rect.y)/rect.height
                    self.scroll=round(fraction*(len(self.options)-rows));self.cursor=self.scroll;return True
                self.index=min(len(self.options)-1,self.scroll+(event.pos[1]-rect.y)//self.row_height)
            self.open=False;return True
        if event.type==pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE,pygame.K_TAB):self.open=False
            elif event.key in (pygame.K_RETURN,pygame.K_KP_ENTER):self.index=self.cursor;self.open=False
            elif event.key in (pygame.K_DOWN,pygame.K_UP,pygame.K_PAGEDOWN,pygame.K_PAGEUP,pygame.K_HOME,pygame.K_END):
                if event.key==pygame.K_HOME:self.cursor=0
                elif event.key==pygame.K_END:self.cursor=len(self.options)-1
                else:self.cursor=max(0,min(len(self.options)-1,self.cursor+{pygame.K_DOWN:1,pygame.K_UP:-1,pygame.K_PAGEDOWN:rows,pygame.K_PAGEUP:-rows}[event.key]))
                self.reveal()
            elif getattr(event,'unicode','').isprintable() and event.unicode:
                now=time.monotonic();self.search=(self.search if now-self.search_time<1 else '')+event.unicode.casefold();self.search_time=now
                matches=[i for i,t in enumerate(self.options) if self.search in t.casefold()]
                if matches:self.cursor=matches[0];self.reveal()
            return True
        return False
