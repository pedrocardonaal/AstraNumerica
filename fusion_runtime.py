"""Integra el motor de clase sin sustituir los sprites, escenas y mapa recibidos."""
import copy,math,random,time
from pathlib import Path
import pygame
import engine,data,ui
from worksheet import Worksheet
from dropdown import Dropdown

ENV={}

class IntegratedGame:
    min_cell_seconds=1.0      # tiempo mínimo creíble por casilla
    def init_integration(self):
        self.real_used=0.0;self._real_last=time.monotonic();self.mission_suspect=False;self.suspect_run=False
        self.map_selection=None
        self.theme=self.store.get('theme','dark');ui.set_theme(self.theme)
        self.admin=False;self.admin_variant=0;self.admin_filter='Todos';self.admin_page=0
        self.password_input=ui.TextInput((360,260,280,46),numeric=False,max_len=32)
        self.password_input.secret=True
        self.text_scale=max(1,min(1.75,float(self.store.get('text_scale',1.0))))
        self.used_variants={};self.hints_total=0;self.wrong_total=0;self.recorded=False
        self.hscroll=0;self._layout=None;self.admin_return=None
        self.fx_particles=[];self.fx_flash=None;self.summary=None;self.save_dirty=False;self.hint_texts=['','','']
        self.drag=None;self.scroll_goal=0;self.hscroll_goal=0;self._sp=0;self._hp=0
        self.admin_planets=[d['id'] for d in engine.WORLDS]
        self.admin_moons=[d['id'] for d in engine.EVENTS]
        label=lambda pid:engine._ALL[pid]['name'].split(' · ')[0]+' · '+engine._ALL[pid]['method']
        self.admin_selectors={
            'variant':Dropdown((140,162,720,42),[f'Variante {i+1}' for i in range(5)]),
            'planet':Dropdown((140,286,720,42),[label(pid) for pid in self.admin_planets]),
            'moon':Dropdown((140,452,720,42),[label(pid) for pid in self.admin_moons])}

    def start_mission(self):
        d=self.current_entry()['def'];pid=d['id'];res=self.resume if self.resume and self.resume.get('id')==pid else None
        self.resume=None
        if self.admin:variant=self.admin_variant
        elif res:variant=res.get('variant',res.get('seed',0)%5)
        else:
            used=self.used_variants.setdefault(pid,[]);options=[v for v in range(5) if v not in used]
            if not options:used.clear();options=list(range(5))
            variant=random.choice(options);used.append(variant)
        self.seed=variant;self.variant=variant;self.problem=engine.problem_for(pid,variant)
        self.fields=list(engine.boxes(self.problem));self.inputs=[]
        for field in self.fields:
            expression=isinstance(field.v,engine.Expression)
            inp=ui.TextInput((0,0,130,38),numeric=not expression,max_len=600 if expression else 40)
            inp.procedure=expression;inp.placeholder='' if field.role=='substitution' else 'Sustitución' if expression else 'x anterior' if ': x anterior' in field.label else 'Resultado';self.inputs.append(inp)
        self.focus=0;self.inputs[0].active=True;self.hints_unlocked=0;self.hint_paid=0
        self.wrong_attempts=0;self.time_total=d['time'];self.time_left=self.time_total
        self.mission_active=True;self.feedback=None;self.result_status=None;self.show_calc=False;self.calc_expr=''
        self.scroll=0;self.hscroll=0;self.ensure_visible=False;self._layout=None;self.expanded=None;self.tool_menu=None
        self.hint_texts=['','','']
        self.real_used=float(res.get('real_used',0.0)) if res else 0.0;self._real_last=time.monotonic();self.mission_suspect=False
        self.fx_particles=[];self.fx_flash=None;self.summary=None;self.save_dirty=False
        self.drag=None;self.scroll_goal=0;self.hscroll_goal=0;self._sp=0;self._hp=0
        if self.admin:
            for inp,f in zip(self.inputs,self.fields):inp.text=engine.answer_text(f.v)
        elif res:
            self.time_left=float(res['time_left']);self.hints_unlocked=res.get('hints_unlocked',0)
            self.wrong_attempts=res.get('wrong_attempts',0)
            self.hint_texts=(list(res.get('hint_texts',[]))+['','',''])[:3]
            for i,(inp,text) in enumerate(zip(self.inputs,res.get('texts',[]))):
                inp.text=text;inp.locked=i in res.get('locked',[]);inp.status='ok' if inp.locked else None
            self.focus=min(res.get('focus',0),len(self.inputs)-1);self.ensure_visible=True

    FX_COLORS={'ok':[(110,230,150),(170,255,190),(60,200,120)],'bad':[(240,100,110),(255,150,140),(200,60,80)]}

    def spawn_fx(self,kind,origin=(877,536),n=70):
        """Partículas y destello de pantalla: verdes al acertar, rojos al fallar."""
        for _ in range(n):
            a=random.uniform(0,2*math.pi) if kind=='bad' else random.uniform(-math.pi*.95,-math.pi*.05)
            speed=random.uniform(120,420)
            self.fx_particles.append([origin[0],origin[1],math.cos(a)*speed,math.sin(a)*speed,
               random.uniform(.6,1.3),random.choice(self.FX_COLORS[kind]),random.randint(3,6)])
        self.fx_flash=(kind,.35)

    def update_fx(self,dt):
        for p in self.fx_particles:
            p[0]+=p[2]*dt;p[1]+=p[3]*dt;p[3]+=520*dt;p[4]-=dt
        self.fx_particles=[p for p in self.fx_particles if p[4]>0]
        if self.fx_flash:
            kind,left=self.fx_flash;left-=dt;self.fx_flash=(kind,left) if left>0 else None

    def check_fields(self):
        count=0
        for inp,f in zip(self.inputs,self.fields):
            good=engine.check_answer(inp.text,f.v);inp.status='ok' if good else 'bad'
            if good:inp.locked=True
            count+=good
        return count

    def submit(self):
        good=self.check_fields()
        if good==len(self.fields):
            if self.admin:
                self.mission_active=False;self.feedback=('ok','ADMIN: procedimiento completo, sin estadísticas.')
                self.spawn_fx('ok',n=40);self.flash=70;self.result_status='admin';return
            self.streak+=1
            penalty=self.hint_cost()+max(0,self.wrong_attempts-1)*15
            elapsed=max(0,self.time_total-self.time_left);real=self.real_used+(time.monotonic()-self._real_last)
            fast=min(elapsed,real)<len(self.fields)*self.min_cell_seconds
            frozen=real>elapsed*1.5+15           # el cronómetro del juego fue frenado o alterado
            self.mission_suspect=fast or frozen
            if self.mission_suspect:self.suspect_run=True
            points,*_=engine.reward(0 if self.mission_suspect else self.time_left,self.time_total,self.current_entry()['type']=='event',self.streak,penalty)
            self.score+=points;self.mission_active=False;self.feedback=('ok',f'¡Correcto! +{points} puntos')
            self.summary={'points':points,'total':self.score,'streak':self.streak,
               'time':max(0,self.time_total-self.time_left),'hints':self.hints_unlocked,'wrong':self.wrong_attempts,
               'cells':good,'cells_total':len(self.fields),'variant':self.variant+1,
               'kind':'Planeta' if self.current_entry()['type']=='world' else 'Luna',
               'method':self.current_entry()['def']['method'],'suspect':self.mission_suspect}
            self.spawn_fx('ok');self.save_dirty=False
            self.summary['plots']=[s for s in self.problem['steps'] if s['kind']=='plot'];self.summary['page']=0
            self.flash=70;self.result_status='advance';return
        if self.admin:
            self.feedback=('bad','Respuestas modificadas. Pulsa Llenar para restaurarlas.');self.feedback_t=180;return
        missing=any(not inp.text.strip() for inp in self.inputs)
        if not missing:self.wrong_attempts+=1;self.wrong_total+=1;self.streak=0
        bad=next((f for inp,f in zip(self.inputs,self.fields) if inp.status=='bad'),None)
        detail=('Escribe la operación, no solo su resultado.' if bad and isinstance(bad.v,engine.Expression) else 'Revisa signos y operaciones.')
        self.shake_t=.5
        if any(inp.status=='bad' for inp in self.inputs):self.spawn_fx('bad')
        self.feedback=('bad',f'{good} de {len(self.fields)} casillas correctas. '+('Completa las restantes; sin descuento.' if missing else detail))
        self.feedback_t=180

    def use_hint(self):
        if self.admin:
            for inp,f in zip(self.inputs,self.fields):inp.text=engine.answer_text(f.v);inp.locked=False;inp.status=None
            self.feedback=('ok','Respuestas completas restauradas.');self.feedback_t=180;return
        if self.hints_unlocked<3:
            level=self.hints_unlocked;cost=[50,100,150][level]
            self.hint_texts[level]=self.hint_text(level);self.hints_unlocked+=1;self.hints_total+=1
            self.feedback=('bad',f'Pista usada: −{cost} puntos de la recompensa');self.feedback_t=180

    def hint_text(self,level):
        """1: fórmula general · 2: primer paso pendiente · 3: resultado del campo enfocado."""
        clean=lambda f:f.label.replace(':',' ·')
        if level==0:
            return 'Fórmula general · '+self.problem['hint1'].replace('\n','  ;  ')
        if level==1:
            i=next((k for k,inp in enumerate(self.inputs) if not inp.locked),0);f=self.fields[i]
            return f'Primer paso · {clean(f)} = {engine.answer_text(f.v)}'
        f=self.fields[self.focus];return f'Resultado de la casilla enfocada · {clean(f)} = {engine.answer_text(f.v)}'

    def track_real(self):
        now=time.monotonic()
        if self.mission_active and not self.admin:self.real_used+=now-self._real_last
        self._real_last=now

    def timeout(self):
        if self.admin:return
        return super().timeout()

    def snapshot(self):
        return {'id':self.current_entry()['def']['id'],'seed':self.seed,'variant':self.variant,
           'time_left':self.time_left,'texts':[i.text for i in self.inputs],'focus':self.focus,
           'locked':[j for j,i in enumerate(self.inputs) if i.locked],
           'hints_unlocked':self.hints_unlocked,'hint_paid':0,'wrong_attempts':self.wrong_attempts,'hint_texts':self.hint_texts,'real_used':self.real_used}

    def autosave(self):
        if self.admin:return
        mission=self.snapshot() if self.mission_active and self.mode=='MISSION' else self.resume
        self.store['save']={'name':self.name,'done':sorted(self.done),'lives':self.lives,'score':self.score,
            'streak':self.streak,'mission':mission,'hints_total':self.hints_total,
            'wrong_total':self.wrong_total,'used_variants':self.used_variants,'suspect_run':self.suspect_run}
        if not data.save(self.store):self.feedback=('bad','No se pudo guardar; revisa el permiso de escritura de la carpeta.');self.feedback_t=240

    def load_continue(self):
        if not super().load_continue():return False
        s=self.store['save'];self.hints_total=s.get('hints_total',0);self.wrong_total=s.get('wrong_total',0)
        self.used_variants=copy.deepcopy(s.get('used_variants',{}));self.recorded=False;self.suspect_run=bool(s.get('suspect_run',False))
        return True

    def advance(self):
        if self.admin:self.mode='ADMIN';return
        super().advance()

    def finish_run(self,status):
        if self.admin or self.recorded:return
        self.recorded=True
        data.add_record(self.store,self.name or 'Jugador',self.score,self.worlds_done(),self.hints_total,status,self.suspect_run)
        self.store['save']=None;data.save(self.store)

    def authenticate(self,password):
        if password!='12345':return False
        if self.admin:return True
        attrs=['name','seq_i','done','resume','lives','score','streak','problem','inputs','fields',
               'focus','hints_unlocked','hint_paid','wrong_attempts','time_left','time_total',
               'mission_active','used_variants','hints_total','wrong_total','recorded','text_scale']
        self.admin_return={k:getattr(self,k) for k in attrs if hasattr(self,k)}
        self._real_store=self.store;self.store=copy.deepcopy(self.store)
        self.admin=True;self.done=set();self.resume=None;self.inputs=[];self.score=0;self.streak=0;self.lives=3
        self.hints_total=0;self.wrong_total=0;self.mode='ADMIN';self.admin_page=0;self.admin_filter='Todos'
        for selector in self.admin_selectors.values():selector.collapse()
        return True

    def leave_admin(self):
        if not self.admin:return
        self.store=self._real_store
        for k,v in self.admin_return.items():setattr(self,k,v)
        self.admin_return=None;del self._real_store;self.admin=False;self.mode='MENU'
        self.feedback=None;self._layout=None;self.mission_active=False

    def admin_open(self,pid,variant=None):
        if not self.admin:raise PermissionError('Se requiere ADMIN.')
        if variant is not None:
            if not 0<=variant<5:raise ValueError('Variante fuera del catálogo.')
            self.admin_variant=variant
        self.select(pid);self.start_mission();self.mode='MISSION'
        ids=self.admin_moons if pid in engine.PARENT else self.admin_planets
        self.admin_selectors['moon' if pid in engine.PARENT else 'planet'].index=ids.index(pid)


def install(env):
    ENV.update(env)
    original_game=env['Game']
    class Game(IntegratedGame,original_game):
        def __init__(self):super().__init__();self.init_integration()
    env['Game']=Game;env['game']=Game()
    original_draw_menu=env['draw_menu'];original_handle_menu=env['handle_menu']
    original_draw_mission=env['draw_mission'];original_nodes=env['map_nodes'];original_draw_map=env['draw_map']
    original_map_handler=env['handle_map'];original_travel=env['draw_travel'];original_update_travel=env['update_travel']
    original_new_game=env['start_new_game']
    screen=env['screen'];view=env['VIEW'];cx=env['CONTENT_X'];cw=env['CONTENT_W']

    def game():return env['game']
    def button(key,rect,label,size=19,primary=False):
        b=ui.Button(rect,label,size=size);b.primary=primary;b.update(pygame.mouse.get_pos());b.draw(screen);game().buttons[key]=b
    def clicked(key,event):return key in game().buttons and game().buttons[key].clicked(event)

    def toggle_theme():
        g=game();g.theme='light' if ui.THEME=='dark' else 'dark';ui.set_theme(g.theme);g._layout=None
        if not g.admin:g.store['theme']=g.theme;data.save(g.store)

    def ensure_layout():
        nonlocal cx,cw
        g=game()
        automatic=len(g.fields)>28 or g.text_scale>=1.5 or any(s['kind']=='table' and len(s['headers'])>=4 for s in g.problem['steps'])
        expanded=automatic if getattr(g,'expanded',None) is None else g.expanded
        g.wide_layout=expanded
        view.update(18 if expanded else 250,112,964 if expanded else 732,390)
        cx=view.x+20;cw=view.width-40;env['CONTENT_X']=cx;env['CONTENT_W']=cw
        reveal=g.admin or (bool(g.inputs) and all(i.locked for i in g.inputs))
        key=(id(g.problem),g.text_scale,g.hints_unlocked,tuple(g.hint_texts),ui.THEME,cw,reveal)
        if g._layout is None or g._layout_key!=key:
            old=g._layout;anchor=None
            if old and old.slots:
                i=min(range(len(old.slots)),key=lambda i:abs(old.slots[i].y-g.scroll))
                anchor=(i,old.slots[i].y-g.scroll)
            g._layout=Worksheet(g.problem,cw,g.text_scale,g.hints_unlocked,g.hint_texts,reveal);g._layout_key=key
            if anchor:g.scroll=max(0,g._layout.slots[anchor[0]].y-anchor[1])
            assert len(g._layout.slots)==len(g.inputs)
        return g._layout

    def vbar_geometry(g,layout):
        track=pygame.Rect(view.right-16,view.y+12,10,view.height-28)
        height=max(36,round(track.height*view.height/max(1,layout.height)))
        y=track.y+round((track.height-height)*g.scroll/max(1,g.max_scroll))
        return track,pygame.Rect(track.x,y,track.width,height)

    def hbar_geometry(g):
        track_x=view.x+50;track_w=view.width-100
        width=max(35,track_w*cw/g.visible_width);x=track_x+(track_w-width)*g.hscroll/max(1,g.visible_width-cw)
        return track_x,track_w,width

    def step_toward(value,goal,k):
        diff=goal-value
        if abs(diff)<1:return round(goal)
        move=round(diff*k)
        return value+(move if move else (1 if diff>0 else -1))

    def ease_scrolling(dt):
        """Desplazamiento suave: la rueda y las flechas fijan una meta y la hoja se acerca a ella."""
        g=game()
        if getattr(g,'_sp',None)!=g.scroll:g.scroll_goal=g.scroll          # otro código movió la hoja: respeta ese valor
        if getattr(g,'_hp',None)!=g.hscroll:g.hscroll_goal=g.hscroll
        k=min(1,dt*16)
        if g.drag is None:
            g.scroll=step_toward(g.scroll,g.scroll_goal,k);g.hscroll=step_toward(g.hscroll,g.hscroll_goal,k)
        else:g.scroll_goal=g.scroll;g.hscroll_goal=g.hscroll
        g._sp=g.scroll;g._hp=g.hscroll

    def render_content(draw):
        g=game();layout=ensure_layout()
        layout.draw(screen,view,cx,g.scroll,g.hscroll,g.inputs,draw)
        return layout.height

    def change_scale(delta):
        g=game();g.text_scale=max(1,min(1.75,round(g.text_scale+delta,2)));g._layout=None
        g.ensure_visible=True
        if not g.admin:g.store['text_scale']=g.text_scale;data.save(g.store)

    def draw_menu():
        original_draw_menu();button('admin_menu',(805,580,165,40),'ADMIN',20)
        if game().store.get('_tampered'):ui.draw_text(screen,'Archivo de datos alterado: se ignoraron récords y partida guardada.',(500,552),15,ui.BAD,center=True,max_w=900)

    def handle_menu(event):
        if clicked('admin_menu',event):
            game().mode='ADMIN_LOGIN';game().password_input.text='';game().password_input.active=True;game().feedback=None;return
        original_handle_menu(event)

    def new_game():
        g=game();g.suspect_run=False
        g.hints_total=0;g.wrong_total=0;g.used_variants={};g.recorded=False;original_new_game()

    def draw_mission():
        g=game();layout=ensure_layout()
        for key in ('hint','calc','smaller','larger','expand','admin_prev','admin_next','admin_panel','theme_toggle','scroll_left','scroll_right'):g.buttons.pop(key,None)
        g.hscroll=max(0,min(g.hscroll,max(0,layout.max_width-cw)))
        if g.ensure_visible and g.inputs:
            slot=layout.slots[g.focus]
            g.scroll=max(0,min(g.scroll,max(0,layout.height-view.height+12)))
            for _ in range(4):
                top_margin=layout.sticky_height(g.scroll)+12
                bottom_margin=38 if layout.visible_width(g.scroll,view.height)>cw else 12
                if slot.y-g.scroll<top_margin:g.scroll=max(0,slot.y-top_margin)
                elif slot.bottom-g.scroll>view.height-bottom_margin:g.scroll=slot.bottom-view.height+bottom_margin
                else:break
            if slot.x-g.hscroll<0:g.hscroll=max(0,slot.x-8)
            elif slot.right-g.hscroll>cw:g.hscroll=slot.right-cw+10
            g.ensure_visible=False;g.scroll=round(g.scroll);g.scroll_goal=g.scroll;g.hscroll_goal=g.hscroll;g._sp=g.scroll;g._hp=g.hscroll
        g.visible_width=layout.visible_width(g.scroll,view.height)
        g.hscroll=max(0,min(g.hscroll,max(0,g.visible_width-cw)))
        env['draw_background']()
        d=g.current_entry()['def']
        pid=d['id'];parent=engine.PARENT.get(pid)
        short=lambda key:engine._ALL[key]['name'].split(' · ')[0]
        trail=('LUNA OPCIONAL · '+short(parent)+' / '+engine.destination_title(pid)) if parent else f'PLANETA {[x[0] for x in engine.FAMILIES].index(pid)+1} DE 7 · '+engine.destination_title(pid)
        ui.panel(screen,(18,10,964,94),radius=14)
        ui.draw_text(screen,trail,(32,18),14,ui.TEXT_DIM,max_w=700)
        ui.draw_text(screen,d['method'],(32,40),22,ui.TEXT,bold=True,max_w=700)
        section=layout.section_at(g.scroll)
        while ui.font(13).size(section)[0]>290:section=section[:-2]+'…'
        ui.draw_text(screen,section,(32,80),13,ui.ACCENT)
        filled=sum(1 for i in g.inputs if i.text.strip());total_cells=max(1,len(g.inputs));pct=int(100*filled/total_cells)
        bar_color=ui.GOOD if filled==total_cells else ui.WARN if pct>=40 else ui.ACCENT
        pygame.draw.rect(screen,ui.PANEL_LIGHT,(335,83,310,10),border_radius=5)
        if filled:pygame.draw.rect(screen,bar_color,(335,83,max(8,round(310*filled/total_cells)),10),border_radius=5)
        pygame.draw.rect(screen,ui.ACCENT_SOFT,(335,83,310,10),width=1,border_radius=5)
        ui.draw_text(screen,f'{pct}% · {filled}/{total_cells}',(655,79),13,bar_color,bold=True)
        if g.admin:
            ui.draw_text(screen,'ADMIN · SIN TIEMPO',(766,24),15,ui.WARN,bold=True)
            ui.draw_text(screen,'Sin estadísticas',(766,51),14,ui.TEXT_DIM)
        else:
            seconds=max(0,math.ceil(g.time_left))
            ui.draw_text(screen,f'{seconds//60}:{seconds%60:02d}',(766,18),25,ui.TEXT,bold=True)
            ui.draw_shields(screen,(870,30),g.lives)
            ui.draw_timebar(screen,(766,53,196,10),g.time_left/g.time_total)
            ui.draw_text(screen,f'{g.score} puntos · Racha {g.streak}',(766,76),13,ui.TEXT_DIM)
        if not g.wide_layout:
            planet=parent or pid
            image=env['PLANET_IMG'].get(planet)
            if image:
                big=pygame.transform.scale(image,(180,180))
                old_clip=screen.get_clip();screen.set_clip(pygame.Rect(18,112,212,280))
                env['anim'].draw_scene(screen,planet,pygame.time.get_ticks()/1000,big,None,shake=min(1,g.shake_t*2),danger=False)
                screen.set_clip(old_clip)
            ui.panel(screen,(18,402,212,100),radius=12)
            ui.draw_text(screen,short(pid),(124,416),19,ui.TEXT,bold=True,center=True,max_w=190)
            ui.draw_text(screen,'Vista permite ampliar\nla hoja de trabajo.',(124,450),14,ui.TEXT_DIM,center=True,max_w=190)
        ui.panel(screen,view,radius=14)
        g.max_scroll=max(0,layout.height-view.height+12)
        g.scroll=max(0,min(g.scroll,g.max_scroll))
        for i,inp in enumerate(g.inputs):inp.active=i==g.focus
        layout.draw(screen,view,cx,g.scroll,g.hscroll,g.inputs)
        clip=screen.get_clip();screen.set_clip(view.inflate(-8,-8))
        for inp in g.inputs:
            if view.colliderect(inp.rect):
                inp.draw(screen)
                if not inp.text.strip() and not inp.locked and not g.admin:
                    r=inp.rect;pygame.draw.polygon(screen,ui.BAD,[(r.right-13,r.y+2),(r.right-2,r.y+2),(r.right-2,r.y+13)])
        layout.draw_sticky(screen,view,cx,g.scroll,g.hscroll)
        screen.set_clip(clip)
        if g.max_scroll:
            track,thumb=vbar_geometry(g,layout)
            hot=g.drag=='v' or thumb.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(screen,ui.PANEL_LIGHT,track,border_radius=5)
            pygame.draw.rect(screen,ui.ACCENT if hot else ui.ACCENT_SOFT,thumb,border_radius=5)
        if g.visible_width>cw:
            pygame.draw.rect(screen,ui.PANEL,(view.x+8,view.bottom-30,view.width-16,25))
            button('scroll_left',(view.x+12,view.bottom-30,28,24),'←',17)
            button('scroll_right',(view.right-40,view.bottom-30,28,24),'→',17)
            track_x,track_w,width=hbar_geometry(g);x=track_x+(track_w-width)*g.hscroll/max(1,g.visible_width-cw)
            pygame.draw.rect(screen,ui.ACCENT_SOFT,(track_x,view.bottom-20,track_w,6),border_radius=3)
            pygame.draw.rect(screen,ui.ACCENT,(round(x),view.bottom-22,round(width),10),border_radius=5)
        button('helpers',(18,514,148,44),'Revisión ▾' if g.admin else 'Ayudas ▾',18)
        button('view_options',(178,514,110,44),'Vista ▾',18)
        button('save',(570,514,190,44),'Elegir método' if g.admin else 'Guardar y salir',18)
        button('check',(772,514,210,44),'Comprobar',20,primary=True)
        completed=sum(i.locked for i in g.inputs)
        ui.draw_text(screen,f'{completed} / {len(g.inputs)} verificadas',(310,526),15,ui.TEXT_DIM)
        if g.feedback:
            ui.draw_text(screen,g.feedback[1],(500,565),15,ui.GOOD if g.feedback[0]=='ok' else ui.BAD,center=True,max_w=950)
        ui.draw_text(screen,'Tab: siguiente casilla · Mayús+Tab: anterior',(20,603),13,ui.TEXT_DIM)
        label=g.fields[g.focus].label.replace(':',' ·')
        while ui.font(13).size(label)[0]>530:label=label[:-2]+'…'
        ui.draw_text(screen,label,(450,603),13,ui.TEXT_DIM)
        if g.tool_menu=='helpers':
            height=220 if g.admin else 132;top=502-height
            ui.panel(screen,(18,top,300,height),glow=ui.ACCENT,radius=14)
            ui.draw_text(screen,'Revisión' if g.admin else 'Ayudas',(34,top+12),18,ui.TEXT,bold=True)
            hint='Restaurar respuestas' if g.admin else f'Solicitar pista · {[50,100,150][g.hints_unlocked]} pts' if g.hints_unlocked<3 else 'Sin pistas disponibles'
            button('hint',(30,top+42,276,36),hint,16)
            button('calc',(30,top+84,276,36),'Calculadora · Gratis',16)
            if g.admin:
                button('admin_prev',(30,top+130,276,36),'Método anterior',16)
                button('admin_next',(30,top+174,276,36),'Método siguiente',16)
        elif g.tool_menu=='view':
            top=292;ui.panel(screen,(178,top,300,210),glow=ui.ACCENT,radius=14)
            ui.draw_text(screen,'Presentación',(194,top+12),18,ui.TEXT,bold=True)
            button('smaller',(190,top+46,64,36),'A−',18);button('larger',(402,top+46,64,36),'A+',18)
            ui.draw_text(screen,f'Texto: {round(g.text_scale*100)}%',(270,top+54),16,ui.TEXT)
            button('expand',(190,top+94,276,40),'Mostrar planeta' if g.wide_layout else 'Ampliar procedimiento',16)
            button('theme_toggle',(190,top+146,276,40),'Cambiar a modo claro' if ui.THEME=='dark' else 'Cambiar a modo oscuro',16)
        if g.show_calc:draw_calculator()

    def do_submit():
        g=game();g.submit()
        if g.result_status=='advance':g.mode='SUMMARY'
        elif g.result_status=='admin':g.mode='TRAVEL'

    def draw_fx():
        g=game()
        if g.fx_flash:
            kind,left=g.fx_flash;color=(60,220,120) if kind=='ok' else (230,60,70)
            overlay=pygame.Surface(screen.get_size(),pygame.SRCALPHA);overlay.fill((*color,int(110*min(1,left/.35))))
            screen.blit(overlay,(0,0))
        for x,y,vx,vy,life,color,size in g.fx_particles:
            pygame.draw.rect(screen,color,(round(x),round(y),size,size))

    def apply_shake():
        g=game()
        if g.shake_t>0:
            frame=screen.copy();dx=round(math.sin(g.shake_t*70)*9*min(1,g.shake_t*2.5))
            screen.fill(ui.BG);screen.blit(frame,(dx,0))

    def draw_plot_reveal():
        g=game();s=g.summary;plot=s['plots'][0]
        overlay=pygame.Surface(screen.get_size(),pygame.SRCALPHA);overlay.fill((0,0,0,170));screen.blit(overlay,(0,0))
        ui.panel(screen,(120,104,760,408),glow=ui.GOOD,radius=18,fill=ui.PANEL)
        ui.draw_text(screen,'GRÁFICA REVELADA',(500,124),28,ui.GOOD,bold=True,center=True)
        ui.draw_text(screen,plot['title'],(500,162),16,ui.TEXT_DIM,center=True)
        from worksheet import plot_surface
        if 'image' not in s:s['image']=plot_surface(plot,720,250)
        screen.blit(s['image'],(140,192))
        button('sum_continue',(390,456,220,40),'Ver resumen',19,primary=True)

    def draw_summary():
        g=game();s=g.summary
        if s.get('plots') and s['page']==0:draw_plot_reveal();return
        overlay=pygame.Surface(screen.get_size(),pygame.SRCALPHA);overlay.fill((0,0,0,170));screen.blit(overlay,(0,0))
        ui.panel(screen,(240,84,520,452),glow=ui.GOOD,radius=18,fill=ui.PANEL)
        ui.draw_text(screen,'MISIÓN COMPLETADA',(500,100),30,ui.GOOD,bold=True,center=True)
        ui.draw_text(screen,s['method'],(500,138),17,ui.TEXT_DIM,center=True,max_w=480)
        seconds=int(s['time']);rows=[('Puntuación de la misión',f"+{s['points']}"),('Total acumulado',str(s['total'])),
           ('Racha',str(s['streak'])),('Tiempo usado',f'{seconds//60}:{seconds%60:02d}'),
           ('Pistas usadas',str(s['hints'])),('Intentos fallidos',str(s['wrong'])),
           ('Casillas correctas',f"{s['cells']} / {s['cells_total']}"),('Variante',f"{s['variant']} de 5"),('Tipo',s['kind'])]
        y=176
        for i,(label,value) in enumerate(rows):
            if i%2==0:pygame.draw.rect(screen,ui.PANEL_LIGHT,(262,y-4,476,30),border_radius=6)
            ui.draw_text(screen,label,(278,y),18,ui.TEXT);ui.draw_text(screen,value,(722-ui.font(18,True).size(value)[0],y),18,ui.ACCENT,bold=True)
            y+=31
        if s.get('suspect'):
            pygame.draw.polygon(screen,ui.WARN,[(262,476),(280,476),(271,460)]);pygame.draw.rect(screen,ui.BG,(270,465,2,6))
            ui.draw_text(screen,'Tiempo sospechoso: sin bono de rapidez',(290,458),15,ui.WARN)
        button('sum_continue',(390,484,220,44),'Continuar',20,primary=True)

    def handle_summary(event):
        g=game()
        if clicked('sum_continue',event) or event.type==pygame.KEYDOWN and event.key in (pygame.K_RETURN,pygame.K_KP_ENTER,pygame.K_SPACE,pygame.K_ESCAPE):
            if g.summary.get('plots') and g.summary['page']==0:g.summary['page']=1;return
            g.buttons.pop('sum_continue',None);g.flash=70;g.mode='TRAVEL'


    def handle_mission(event):
        g=game()
        if g.show_calc:handle_calculator(event);return
        if event.type==pygame.MOUSEBUTTONUP and event.button==1:g.drag=None
        if g.drag and event.type==pygame.MOUSEMOTION:
            if g.drag=='v':
                track,thumb=vbar_geometry(g,g._layout);span=max(1,track.height-thumb.height)
                g.scroll=round(max(0,min(g.max_scroll,(event.pos[1]-track.y-g.drag_off)/span*g.max_scroll)))
            else:
                track_x,track_w,width=hbar_geometry(g);span=max(1,track_w-width)
                g.hscroll=round(max(0,min(g.visible_width-cw,(event.pos[0]-track_x-g.drag_off)/span*(g.visible_width-cw))))
            return
        if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and not g.tool_menu and g._layout:
            if g.max_scroll:
                track,thumb=vbar_geometry(g,g._layout)
                if track.inflate(14,0).collidepoint(event.pos):
                    g.drag='v';g.drag_off=(event.pos[1]-thumb.y) if thumb.collidepoint(event.pos) else thumb.height//2
                    track,thumb=vbar_geometry(g,g._layout);span=max(1,track.height-thumb.height)
                    g.scroll=round(max(0,min(g.max_scroll,(event.pos[1]-track.y-g.drag_off)/span*g.max_scroll)));return
            if getattr(g,'visible_width',cw)>cw and view.bottom-30<=event.pos[1]<=view.bottom-4:
                track_x,track_w,width=hbar_geometry(g)
                if track_x<=event.pos[0]<=track_x+track_w:
                    x0=track_x+(track_w-width)*g.hscroll/max(1,g.visible_width-cw)
                    g.drag='h';g.drag_off=(event.pos[0]-x0) if x0<=event.pos[0]<=x0+width else width/2
                    span=max(1,track_w-width)
                    g.hscroll=round(max(0,min(g.visible_width-cw,(event.pos[0]-track_x-g.drag_off)/span*(g.visible_width-cw))));return
        if event.type==pygame.MOUSEWHEEL and not g.tool_menu:
            if pygame.key.get_mods()&pygame.KMOD_SHIFT:
                limit=max(0,getattr(g,'visible_width',cw)-cw);g.hscroll_goal=max(0,min(limit,g.hscroll_goal-event.y*90))
            else:g.scroll_goal=max(0,min(g.max_scroll,g.scroll_goal-event.y*80))
            return
        if event.type==pygame.KEYDOWN and event.key in (pygame.K_PAGEUP,pygame.K_PAGEDOWN) and not g.tool_menu:
            step=(view.height-60)*(1 if event.key==pygame.K_PAGEDOWN else -1);g.scroll_goal=max(0,min(g.max_scroll,g.scroll_goal+step));return
        if not g.tool_menu:
            for key in ('hint','calc','smaller','larger','expand','admin_prev','admin_next','theme_toggle'):g.buttons.pop(key,None)
        if clicked('helpers',event):g.tool_menu=None if g.tool_menu=='helpers' else 'helpers';return
        if clicked('view_options',event):g.tool_menu=None if g.tool_menu=='view' else 'view';return
        if g.tool_menu:
            if clicked('theme_toggle',event):toggle_theme();return
            if clicked('expand',event):g.expanded=not g.wide_layout;g.tool_menu=None;ensure_layout();g.hscroll=0;return
            if clicked('smaller',event):change_scale(-.25);return
            if clicked('larger',event):change_scale(.25);return
            if clicked('hint',event):g.use_hint();g.tool_menu=None;return
            if clicked('calc',event):g.show_calc=True;g.calc_expr='';g.tool_menu=None;return
            if g.admin and (clicked('admin_next',event) or clicked('admin_prev',event)):
                i=engine.ORDER.index(g.current_entry()['def']['id']);step=1 if clicked('admin_next',event) else -1
                g.admin_open(engine.ORDER[(i+step)%len(engine.ORDER)]);return
            if event.type==pygame.MOUSEBUTTONDOWN or event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE:g.tool_menu=None
            return
        if clicked('scroll_left',event) or clicked('scroll_right',event):
            step=1 if clicked('scroll_right',event) else -1
            g.hscroll_goal=max(0,min(g.visible_width-cw,g.hscroll_goal+step*cw*.6));return
        if clicked('expand',event):
            g.expanded=not g.wide_layout;ensure_layout();g.hscroll=0;return
        if clicked('smaller',event):change_scale(-.25);return
        if clicked('larger',event):change_scale(.25);return
        if g.admin:
            if clicked('save',event) or clicked('admin_panel',event):g.mode='ADMIN';g.mission_active=False;return
            if clicked('admin_next',event) or clicked('admin_prev',event):
                i=engine.ORDER.index(g.current_entry()['def']['id']);step=1 if clicked('admin_next',event) else -1
                g.admin_open(engine.ORDER[(i+step)%len(engine.ORDER)]);return
        if event.type==pygame.KEYDOWN and event.mod&pygame.KMOD_CTRL and event.key in (pygame.K_PLUS,pygame.K_EQUALS,pygame.K_MINUS):
            change_scale(-.25 if event.key==pygame.K_MINUS else .25);return
        if event.type==pygame.KEYDOWN and event.key==pygame.K_TAB and event.mod&pygame.KMOD_SHIFT:
            g.focus=(g.focus-1)%len(g.inputs);g.ensure_visible=True;return
        # El manejador recibido conserva rueda, Tab, Enter, calculadora y botones.
        original_handle_mission(event)

    original_handle_mission=env['handle_mission']
    def update_mission(dt):
        g=game();g.shake_t=max(0,g.shake_t-dt);g.update_fx(dt);ease_scrolling(dt);g.track_real()
        if g.save_dirty and g.mission_active and not g.admin:g.autosave();g.save_dirty=False;g.save_timer_accum=0
        if g.mission_active and not g.admin:
            g.time_left-=dt
            if g.time_left<=0:g.time_left=0;g.timeout();g.autosave();g.mode='TRAVEL'

    def map_nodes():
        return original_nodes()

    def draw_map():
        original_draw_map()

    def handle_map(event):
        original_map_handler(event)

    def draw_travel():
        g=game()
        if g.admin:
            old_status=g.result_status;g.result_status='advance';original_travel();g.result_status=old_status
            pygame.draw.rect(screen,ui.BG,(0,425,1000,120))
            ui.draw_text(screen,'ADMIN · Demostración sin puntos ni récords',(500,455),24,ui.WARN,center=True)
        else:original_travel()

    def update_travel(dt):
        g=game()
        if g.admin:
            g.flash-=1
            if g.flash<=0:g.mode='ADMIN';g.result_status=None
        else:original_update_travel(dt)

    def draw_warn_icon(x,y):
        pygame.draw.polygon(screen,ui.WARN,[(x,y+14),(x+16,y+14),(x+8,y)]);pygame.draw.rect(screen,ui.BG,(x+7,y+5,2,5));pygame.draw.rect(screen,ui.BG,(x+7,y+11,2,2))

    def draw_records():
        g=game();env['draw_background']()
        ui.draw_text(screen,'Récords',(500,50),34,ui.ACCENT,bold=True,center=True)
        records=g.store.get('records',[])
        ui.draw_text(screen,'#   Nombre            Puntos  Mundos  Pistas  Fecha        Estado',(90,110),16,ui.TEXT_DIM)
        y=140
        for i,r in enumerate(records[:15]):
            line=f"{i+1:<3} {r['name']:<16} {r['points']:<7} {r['worlds']:<7} {r['hints']:<7} {r['date']:<12} {r['status']}"
            ui.draw_text(screen,line,(90,y),16,ui.TEXT)
            if r.get('suspect'):
                end=90+ui.font(16).size(line)[0]+14;draw_warn_icon(end,y+2);ui.draw_text(screen,'sospechoso',(end+22,y),16,ui.WARN)
            y+=26
        if not records:ui.draw_text(screen,'Todavía no hay partidas registradas.',(500,160),18,ui.TEXT_DIM,center=True)
        if g.store.get('_tampered'):ui.draw_text(screen,'El archivo de datos fue modificado: se ignoraron los récords y la partida anteriores.',(500,528),15,ui.BAD,center=True,max_w=900)
        button('back',(410,560,180,44),'Volver',20)

    def draw_admin_login():
        env['draw_background']();env['_draw_map_sky'](pygame.time.get_ticks()/1000)
        ui.draw_text(screen,'ADMIN',(500,160),40,ui.ACCENT,bold=True,center=True)
        ui.panel(screen,(330,220,340,115));ui.draw_text(screen,'Contraseña',(360,230),18,ui.TEXT_DIM)
        g=game();g.password_input.rect=pygame.Rect(360,260,280,46);g.password_input.draw(screen)
        button('login',(350,360,140,44),'Entrar');button('login_back',(510,360,140,44),'Volver')
        if g.feedback:ui.draw_text(screen,g.feedback[1],(500,430),19,ui.BAD,center=True)

    def handle_admin_login(event):
        g=game();g.password_input.active=True;g.password_input.handle(event)
        enter=g.password_input.submitted;g.password_input.submitted=False
        if clicked('login_back',event):g.mode='MENU';return
        if enter or clicked('login',event):
            if not g.authenticate(g.password_input.text):g.feedback=('bad','Contraseña incorrecta.');g.password_input.text=''

    def draw_admin():
        env['draw_background']();env['_draw_map_sky'](pygame.time.get_ticks()/1000);g=game()
        ui.draw_text(screen,'ADMIN · REVISIÓN',(500,22),32,ui.ACCENT,bold=True,center=True)
        ui.draw_text(screen,'Campos llenos · Sin tiempo · Sin estadísticas',(500,64),18,ui.TEXT_DIM,center=True)
        ui.draw_text(screen,'Variante',(140,126),20,ui.ACCENT,bold=True)
        ui.draw_text(screen,'Planetas',(140,250),20,ui.ACCENT,bold=True)
        ui.draw_text(screen,'Lunas opcionales',(140,416),20,ui.ACCENT,bold=True)
        g.admin_selectors['variant'].index=g.admin_variant
        for selector in g.admin_selectors.values():selector.draw(screen)
        button('admin_open_planet',(140,340,720,44),'Ver planeta',20)
        button('admin_open_moon',(140,506,720,44),'Ver luna',20)
        button('admin_exit',(390,586,220,36),'Salir de ADMIN',18)
        for selector in g.admin_selectors.values():selector.draw(screen,popup_only=True)

    def handle_admin(event):
        g=game()
        opened=next((selector for selector in g.admin_selectors.values() if selector.open),None)
        if opened is not None:
            if opened.handle(event,screen.get_height()):
                g.admin_variant=g.admin_selectors['variant'].index;return
        else:
            for selector in g.admin_selectors.values():
                if selector.handle(event,screen.get_height()):return
        if clicked('admin_exit',event):g.leave_admin();return
        if clicked('admin_open_planet',event):g.admin_open(g.admin_planets[g.admin_selectors['planet'].index]);return
        if clicked('admin_open_moon',event):g.admin_open(g.admin_moons[g.admin_selectors['moon'].index]);return

    def draw_calculator():
        g=game();ui.panel(screen,(280,110,440,400),glow=ui.ACCENT,fill=ui.PANEL)
        ui.draw_text(screen,'Calculadora',(300,122),22,ui.ACCENT,bold=True)
        from math_notation import from_expression,layout as mathematical_layout
        try:
            expression=mathematical_layout(from_expression(g.calc_expr or '0'),390)
            preview=pygame.Surface((max(1,round(expression.width)),max(1,round(expression.height))),pygame.SRCALPHA)
            for kind,rect,value in expression.ops:
                if kind=='rect':pygame.draw.rect(preview,value,rect)
                else:preview.blit(value,rect)
            factor=min(1,400/preview.get_width(),62/preview.get_height())
            if factor<1:preview=pygame.transform.smoothscale(preview,(max(1,round(preview.get_width()*factor)),max(1,round(preview.get_height()*factor))))
            screen.blit(preview,(300,155))
        except (ValueError,SyntaxError,AttributeError,IndexError):
            shown=g.calc_expr.replace('exp(','e^(').replace('sqrt(','√(').replace('*','·').replace('/','÷')
            ui.draw_text(screen,shown or '0',(300,158),20,ui.TEXT,max_w=400)
        keys=['7','8','9','/','(', '4','5','6','*',')','1','2','3','-','ln(', '0','.','^','+','sqrt(', 'exp(','C','←','=','Cerrar']
        g.buttons['calc_keys']=[]
        for i,k in enumerate(keys):
            label={'exp(':'eˣ','sqrt(':'√','^':'xʸ','/':'÷','*':'×','ln(':'ln'}.get(k,k)
            b=ui.Button((300+(i%5)*80,224+(i//5)*50,74,42),label,size=17);b.update(pygame.mouse.get_pos());b.draw(screen);g.buttons['calc_keys'].append((k,b))

    def calc_press(k):
        g=game()
        if k=='Cerrar':g.show_calc=False
        elif k=='C':g.calc_expr=''
        elif k=='←':g.calc_expr=g.calc_expr[:-1]
        elif k=='=':
            try:
                val=engine.calculate(g.calc_expr)
                if not g.inputs[g.focus].locked:g.inputs[g.focus].text=engine.core.number(val,12)
                else:g.feedback=('bad','Selecciona una casilla pendiente para colocar el resultado.');g.feedback_t=180
                g.show_calc=False;g.calc_expr=''
            except (ValueError,OverflowError,SyntaxError,ZeroDivisionError):g.calc_expr='Error'
        else:g.calc_expr=(('' if g.calc_expr=='Error' else g.calc_expr)+k)[:120]

    def handle_calculator(event):
        g=game()
        if event.type==pygame.KEYDOWN:
            if event.key==pygame.K_ESCAPE:g.show_calc=False
            elif event.key in (pygame.K_RETURN,pygame.K_KP_ENTER):calc_press('=')
            elif event.key==pygame.K_BACKSPACE:calc_press('←')
            elif event.unicode and event.unicode in '0123456789.+-*/^()expsqrtln,':calc_press(event.unicode)
        elif event.type==pygame.MOUSEBUTTONDOWN:
            for k,b in g.buttons.get('calc_keys',[]):
                if b.clicked(event):calc_press(k);return
            if not pygame.Rect(280,110,440,400).collidepoint(event.pos):g.show_calc=False

    def draw_help():
        env['draw_background']()
        ui.draw_text(screen,'Cómo jugar',(500,25),34,ui.ACCENT,bold=True,center=True)
        cards=[
          ('Mapa','map',['7 planetas y 27 lunas opcionales.','Cinco variantes por misión.','Todas las misiones están disponibles.']),
          ('Procedimiento','check',['Llena también potencias y fracciones.','Las respuestas correctas se conservan.','Cada misión dura entre 5 y 30 minutos.']),
          ('Controles','keys',['Tab / Mayús+Tab: cambiar de casilla.','Rueda: mover · Mayús+rueda: lateral.','A− / A+: letra · F11: pantalla completa.']),
          ('Puntos y ayudas','star',['Planeta: 1000 · Luna: 450 puntos base.','Rapidez y racha: puntos extra.','Pistas: 50 / 100 / 150 · Calculadora gratis.']),
          ('Escudos','shield',['Comienzas con 3 escudos.','Tiempo agotado en planeta: −1 escudo','y hasta −100 puntos. En lunas, sin pérdida.']),
          ('Guardar y revisar','save',['Guardar y salir conserva tu progreso.','ADMIN · 12345: procedimientos llenos,','sin tiempo ni estadísticas.'])]
        game().help_card_rects=[]
        for i,(title,icon,lines) in enumerate(cards):
            rect=pygame.Rect(40+(i%2)*470,88+(i//2)*153,450,140)
            game().help_card_rects.append(rect);ui.panel(screen,rect,glow=ui.ACCENT_SOFT,fill=ui.PANEL)
            x,y=rect.x+29,rect.y+28;color=ui.ACCENT
            if icon=='map':
                pygame.draw.circle(screen,color,(x,y),10,2);pygame.draw.ellipse(screen,color,(x-20,y-7,40,14),1)
                pygame.draw.circle(screen,ui.WARN,(x+17,y-4),3)
            elif icon=='check':
                pygame.draw.rect(screen,color,(x-13,y-15,26,30),2,border_radius=3)
                pygame.draw.lines(screen,ui.GOOD,False,[(x-7,y),(x-2,y+5),(x+8,y-7)],3)
            elif icon=='keys':
                pygame.draw.rect(screen,color,(x-20,y-12,40,24),2,border_radius=3)
                for row in range(2):
                    for col in range(4):pygame.draw.rect(screen,color,(x-13+col*8,y-6+row*9,4,4))
            elif icon=='star':
                points=[]
                for k in range(10):
                    a=-math.pi/2+k*math.pi/5;r=17 if k%2==0 else 7
                    points.append((x+math.cos(a)*r,y+math.sin(a)*r))
                pygame.draw.polygon(screen,ui.WARN,points,2)
            elif icon=='shield':
                pygame.draw.polygon(screen,color,[(x-14,y-13),(x+14,y-13),(x+12,y+4),(x,y+17),(x-12,y+4)],2)
            else:
                pygame.draw.rect(screen,color,(x-15,y-15,30,30),2,border_radius=3)
                pygame.draw.rect(screen,color,(x-8,y-15,16,10),2)
                pygame.draw.rect(screen,color,(x-9,y+3,18,12),1)
            ui.draw_text(screen,title,(rect.x+59,rect.y+12),21,ui.ACCENT,bold=True)
            yy=rect.y+51
            for line in lines:
                yy=ui.draw_text(screen,line,(rect.x+17,yy),15,ui.TEXT,max_w=rect.width-32)
        button('back',(400,568,200,44),'Volver',20)

    def tick(dt):
        g=game()
        if g.mode=='MISSION':
            update_mission(dt)
            if g.mode=='MISSION':
                draw_mission();g.save_timer_accum+=dt
                if g.save_timer_accum>=5:g.autosave();g.save_timer_accum=0
                apply_shake();draw_fx()
            else:draw_travel()
        elif g.mode=='TRAVEL':
            update_travel(dt)
            if g.mode=='TRAVEL':draw_travel()
            elif g.mode=='MAP':draw_map()
            elif g.mode=='ADMIN':draw_admin()
            elif g.mode in ('WIN','LOSE'):env['draw_endscreen'](g.mode=='WIN')
            else:env['draw_intro']()
        elif g.mode=='SUMMARY':
            g.shake_t=max(0,g.shake_t-dt);g.update_fx(dt);draw_mission();draw_summary();draw_fx()
        else:
            draws={'MENU':draw_menu,'MAP':draw_map,'WORLD_INTRO':env['draw_intro'],'HELP':draw_help,
                 'RECORDS':env['draw_records'],'ADMIN_LOGIN':draw_admin_login,'ADMIN':draw_admin,
                 'WIN':lambda:env['draw_endscreen'](True),'LOSE':lambda:env['draw_endscreen'](False)}
            draws[g.mode]()
        if g.mode not in ('TRAVEL','MISSION','SUMMARY'):
            pos=(20,580,180,38) if g.mode=='MENU' else (705,56,150,30) if g.mode=='MAP' else (810,594,170,32)
            button('theme_toggle',pos,'Modo claro' if ui.THEME=='dark' else 'Modo oscuro',16)

    def dispatch(event):
        g=game()
        if g.mode not in ('TRAVEL','MISSION','SUMMARY') and clicked('theme_toggle',event):toggle_theme();return True
        if event.type==pygame.QUIT:
            if g.admin:g.leave_admin()
            else:
                if g.mode not in ('MENU','WIN','LOSE','RECORDS','HELP','ADMIN_LOGIN'):g.autosave()
                data.save(g.store)
            return False
        if event.type==pygame.KEYDOWN and (event.key==pygame.K_F11 or event.key==pygame.K_RETURN and event.mod&pygame.KMOD_ALT):
            pygame.display.toggle_fullscreen();return True
        handlers={'MENU':handle_menu,'MAP':handle_map,'WORLD_INTRO':env['handle_intro'],'MISSION':handle_mission,
           'HELP':env['handle_simple_back'],'RECORDS':env['handle_simple_back'],'WIN':env['handle_simple_back'],
           'LOSE':env['handle_simple_back'],'ADMIN_LOGIN':handle_admin_login,'ADMIN':handle_admin,'SUMMARY':handle_summary}
        if g.mode in handlers:
            before=[i.text for i in g.inputs] if g.mode=='MISSION' and not g.admin else None
            handlers[g.mode](event)
            if before is not None and g.mode=='MISSION' and [i.text for i in g.inputs]!=before:g.save_dirty=True
        return True

    def main():
        import sys
        if '--self-test' in sys.argv:
            from qa_fusion import run
            run(env,Path(sys.argv[sys.argv.index('--self-test')+1]));pygame.quit();return
        running=True
        while running:
            dt=env['clock'].tick(60)/1000
            for event in pygame.event.get():running=dispatch(event) and running
            if running:tick(dt);pygame.display.flip()
        pygame.quit()

    # Los nombres globales originales resuelven aquí sus funciones al ejecutar cada pantalla.
    replacements=locals()
    for name in ['draw_menu','handle_menu','draw_mission','render_content','handle_mission','do_submit',
       'update_mission','map_nodes','draw_map','handle_map','draw_travel','update_travel','draw_calculator','draw_records',
       'calc_press','draw_help','main']:env[name]=replacements[name]
    env['draw_records']=draw_records;env['start_new_game']=new_game;env['fusion_tick']=tick;env['fusion_dispatch']=dispatch
    env['fusion_layout']=ensure_layout;env['fusion_change_scale']=change_scale
    patch_inputs()


def patch_inputs():
    original=ui.TextInput.handle
    def handle(self,event):
        if self.numeric and event.type==pygame.KEYDOWN and self.active and not self.locked:
            if event.mod&pygame.KMOD_CTRL and event.key==pygame.K_a:self.fresh=True;return
            if event.key==pygame.K_DELETE:self.text='';self.fresh=False;self.status=None;return
            if self.fresh and event.unicode and event.unicode in '0123456789+-−.,/':self.text='';self.fresh=False
        if getattr(self,'procedure',False):
            if self.locked:return
            if event.type==pygame.MOUSEBUTTONDOWN:
                self.active=self.rect.collidepoint(event.pos)
                if self.active:self.cursor=len(self.text)
                return
            if event.type!=pygame.KEYDOWN or not self.active:return
            pos=min(len(self.text),getattr(self,'cursor',len(self.text)))
            if event.key in (pygame.K_RETURN,pygame.K_KP_ENTER):self.submitted=True;return
            if event.key==pygame.K_TAB:return
            if event.mod&pygame.KMOD_CTRL and event.key==pygame.K_a:self.fresh=True;return
            if event.key==pygame.K_LEFT:self.cursor=max(0,pos-1);return
            if event.key==pygame.K_RIGHT:self.cursor=min(len(self.text),pos+1);return
            if event.key==pygame.K_HOME:self.cursor=0;return
            if event.key==pygame.K_END:self.cursor=len(self.text);return
            if event.key==pygame.K_BACKSPACE:
                if self.fresh:self.text='';pos=0;self.fresh=False
                elif pos:self.text=self.text[:pos-1]+self.text[pos:];pos-=1
            elif event.key==pygame.K_DELETE:
                if self.fresh:self.text='';pos=0;self.fresh=False
                else:self.text=self.text[:pos]+self.text[pos+1:]
            else:
                ch=event.unicode
                if not ch or not ch.isprintable():return
                if self.fresh:self.text='';pos=0;self.fresh=False
                if len(self.text)+len(ch)>self.max_len:return
                self.text=self.text[:pos]+ch+self.text[pos:];pos+=len(ch)
            self.cursor=pos;self.status=None;return
        if self.numeric and event.type==pygame.KEYDOWN and self.active and not self.locked and event.unicode in ('+','−'):
            if self.fresh:self.text='';self.fresh=False
            if len(self.text)<self.max_len:self.text+=event.unicode
            self.status=None;return
        original(self,event)
    def value(self):
        text=self.text.strip().replace('−','-')
        if text in ('+','-'):return text
        try:return engine.core.parse_number(text)
        except (ValueError,OverflowError,ZeroDivisionError):return None
    def draw(self,surf):
        glow=ui.GOOD if self.locked or self.status=='ok' else ui.BAD if self.status=='bad' else ui.ACCENT if self.active else ui.ACCENT_SOFT
        fill=ui.OK_FILL if self.locked or self.status=='ok' else ui.BAD_FILL if self.status=='bad' else ui.PANEL_LIGHT
        ui.panel(surf,self.rect,glow=glow,radius=10,fill=fill)
        shown=('•'*len(self.text) if getattr(self,'secret',False) else self.text) or self.placeholder
        size=getattr(self,'font_size',22)
        if getattr(self,'procedure',False):
            size=max(16,size-2);font=ui.font(size)
            clip=surf.get_clip();surf.set_clip(self.rect.inflate(-12,-8).clip(clip))
            lines=ui.wrap_lines(shown,font,max(30,self.rect.width-24))
            lineheight=font.get_linesize();maxlines=max(1,(self.rect.height-12)//lineheight)
            cursor=min(len(self.text),getattr(self,'cursor',len(self.text)))
            before=ui.wrap_lines(self.text[:cursor] or ' ',font,max(30,self.rect.width-24))
            cursorline=len(before)-1;offset=max(0,cursorline-maxlines+1) if self.active else 0
            for i,line in enumerate(lines[offset:offset+maxlines]):
                img=font.render(line,True,ui.TEXT);surf.blit(img,(self.rect.x+12,self.rect.y+8+i*lineheight))
            if self.active and not self.locked and pygame.time.get_ticks()%1000<500:
                x=self.rect.x+12+font.size(before[-1])[0];y=self.rect.y+8+(cursorline-offset)*lineheight
                pygame.draw.line(surf,ui.TEXT,(x,y),(x,y+lineheight-3))
            surf.set_clip(clip);return
        while size>14 and ui.font(size).size(shown)[0]>self.rect.width-20:size-=1
        clip=surf.get_clip();surf.set_clip(self.rect.clip(clip));img=ui.font(size).render(shown,True,ui.TEXT if self.text else ui.TEXT_DIM)
        surf.blit(img,img.get_rect(midleft=(self.rect.x+10,self.rect.centery)))
        if self.active and not self.locked and pygame.time.get_ticks()%1000<500:
            x=min(self.rect.right-7,self.rect.x+12+img.get_width());pygame.draw.line(surf,ui.ACCENT,(x,self.rect.centery-10),(x,self.rect.centery+10))
        surf.set_clip(clip)
    ui.TextInput.handle=handle;ui.TextInput.value=value;ui.TextInput.draw=draw
