"""
Astro Numérica — prototipo jugable
Menú → nombre → 7 planetas + 27 lunas (alternados) → récords.
Ejecutar:  python main.py
"""
import os
import sys
import math
import random
# Suaviza el texto cuando SDL adapta la ventana a otra resolución.
os.environ.setdefault('SDL_RENDER_SCALE_QUALITY','1')
import pygame
import asyncio

import anim
import engine
import data
import ui

pygame.init()
pygame.key.set_repeat(400, 40)
pygame.display.set_caption("Astro Numérica")
SCREEN_W, SCREEN_H = 1000, 640
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), (0 if os.environ.get("SDL_VIDEODRIVER")=="dummy" else pygame.SCALED | pygame.RESIZABLE))
clock = pygame.time.Clock()

STARS = [(random.randint(0, SCREEN_W), random.randint(0, SCREEN_H), random.randint(1, 2))
         for _ in range(140)]


ASSET_DIR = os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))), "assets")


def _load(name, size=None):
    """Carga un sprite de assets/. Si falta, devuelve None y el juego usa figuras simples."""
    try:
        img = pygame.image.load(os.path.join(ASSET_DIR, name)).convert_alpha()
        return pygame.transform.scale(img, size) if size else img
    except (pygame.error, FileNotFoundError):
        return None


BG_IMG = _load("bg.png", (SCREEN_W, SCREEN_H))
PLANET_IMG = {}
for _pid in ("helios", "ares", "vesper", "nereida", "sonda", "ganimedes", "baliza"):
    PLANET_IMG[_pid] = _load(f"planet_{_pid}.png", (96, 96))
MOON_IMG = _load("moon.png", (32, 32))
if MOON_IMG:
    # El sprite original trae esquinas oscuras; limitar el dibujo al disco
    # evita cuadrados negros cuando se usa el fondo claro.
    _moon_mask=pygame.Surface(MOON_IMG.get_size(),pygame.SRCALPHA)
    pygame.draw.circle(_moon_mask,(255,255,255,255),(16,16),16)
    MOON_IMG.blit(_moon_mask,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
MOON_DONE_IMG = None
if MOON_IMG:
    MOON_DONE_IMG = MOON_IMG.copy()
    MOON_DONE_IMG.fill((110, 230, 150, 255), special_flags=pygame.BLEND_RGBA_MULT)


def draw_background():
    if ui.THEME=='light':
        screen.fill(ui.BG)
        for x,y,r in STARS:pygame.draw.circle(screen,(170,188,212),(x,y),r)
        return
    if BG_IMG:
        screen.blit(BG_IMG, (0, 0))
        return
    screen.fill(ui.BG)
    for (x, y, r) in STARS:
        pygame.draw.circle(screen, (70, 80, 110), (x, y), r)


def build_sequence():
    return ([{"type": "world", "def": w} for w in engine.WORLDS] +
            [{"type": "event", "def": e} for e in engine.EVENTS])


PLANET_COLORS = [(96, 200, 255), (130, 230, 160), (250, 200, 90), (230, 140, 220),
                 (255, 150, 110), (150, 170, 255), (120, 220, 220)]


class Game:
    def __init__(self):
        self.store = data.load()
        self.mode = "MENU"
        self.name = ""
        self.name_input = ui.TextInput((360, 260, 280, 46), "Escribe tu nombre", numeric=False, max_len=14)
        self.name_input.text = self.store.get("last_name", "")
        self.name_input.active = True
        self.name_input.fresh = bool(self.name_input.text)
        self.buttons = {}
        self.sequence = build_sequence()
        self.seq_i = 0
        self.done = set()       # ids de mundos y eventos completados
        self.resume = None      # misión guardada con "Guardar y salir"
        self.shake_t = 0.0
        self.lives = 3
        self.score = 0
        self.streak = 0
        self.problem = None
        self.inputs = []
        self.focus = 0
        self.hints_unlocked = 0
        self.hint_paid = 0
        self.wrong_attempts = 0
        self.time_left = 0
        self.time_total = 0
        self.mission_active = False
        self.feedback = None  # ("ok"/"bad", texto)
        self.feedback_t = 0
        self.show_calc = False
        self.calc_expr = ""
        self.last_save_t = 0
        self.flash = 0  # overlay al completar (mapa/celebración)
        self.result_status = None
        self.save_timer_accum = 0

    # ---------------------------------------------------------- helpers
    def select(self, entry_id):
        for i, e in enumerate(self.sequence):
            if e["def"]["id"] == entry_id:
                self.seq_i = i
                return

    def worlds_done(self):
        return sum(1 for w in engine.WORLDS if w["id"] in self.done)

    def current_entry(self):
        if self.seq_i < len(self.sequence):
            return self.sequence[self.seq_i]
        return None

    def start_mission(self):
        entry = self.current_entry()
        d = entry["def"]
        res = self.resume if (self.resume and self.resume.get("id") == d["id"]) else None
        self.resume = None
        seed = res["seed"] if res else random.randrange(2 ** 31)
        random.seed(seed)            # misma semilla = mismo problema al reanudar
        self.problem = d["gen"]()
        random.seed()
        self.seed = seed
        # Una casilla por cada celda B(...) de las tablas del procedimiento.
        self.fields = [{"value": c.v} for t in self.problem["steps"] for r in t["rows"]
                       for c in r if isinstance(c, engine.B)]
        self.inputs = [ui.TextInput((0, 0, 110, 34)) for _ in self.fields]
        self.scroll = 0
        self.ensure_visible = False
        self.focus = 0
        self.inputs[0].active = True
        self.hints_unlocked = 0
        self.hint_paid = 0
        self.wrong_attempts = 0
        self.time_total = d["time"]
        self.time_left = d["time"]
        self.mission_active = True
        self.feedback = None
        self.show_calc = False
        self.calc_expr = ""
        if res:  # reanudar donde se quedó
            self.time_left = res["time_left"]
            self.hints_unlocked = res["hints_unlocked"]
            self.hint_paid = res["hint_paid"]
            self.wrong_attempts = res["wrong_attempts"]
            for inp, txt in zip(self.inputs, res["texts"]):
                inp.text = txt
            self.focus = min(res.get("focus", 0), len(self.inputs) - 1)
            self.ensure_visible = True

    def check_fields(self):
        """Marca cada casilla (ok/bad) y devuelve cuántas son correctas."""
        good = 0
        for inp, f in zip(self.inputs, self.fields):
            v = inp.value()
            ok = v is not None and engine.check_answer(v, f["value"])
            inp.status = "ok" if ok else "bad"
            good += ok
        return good

    def answers_correct(self):
        return self.check_fields() == len(self.fields)

    def hint_cost(self):
        costs = [50, 100, 150]
        return sum(costs[:self.hints_unlocked])

    def submit(self):
        entry = self.current_entry()
        is_event = entry["type"] == "event"
        if any(inp.value() is None for inp in self.inputs):
            self.feedback = ("bad", "Llena todas las casillas con un número.")  # sin penalización
            self.feedback_t = 90
            return
        if self.answers_correct():
            frac = max(0.0, self.time_left / self.time_total)
            base = 450 if is_event else 1000
            speed_max = 200 if is_event else 400
            speed_bonus = round(speed_max * frac)
            streak_bonus = min(150, 30 * self.streak)
            hints_cost = self.hint_cost() - self.hint_paid  # lo ya descontado al pedir la pista
            wrong_cost = max(0, self.wrong_attempts - 1) * 15
            points = max(0, base + speed_bonus + streak_bonus - hints_cost - wrong_cost)
            self.score += points
            self.streak += 1
            for inp in self.inputs:
                inp.locked = True
            self.mission_active = False
            self.feedback = ("ok", f"¡Correcto! +{points} puntos")
            self.flash = 70
            self.result_status = "advance"
        else:
            self.wrong_attempts += 1
            self.streak = 0
            cost = 0 if self.wrong_attempts <= 1 else 15
            self.score = max(0, self.score - cost)
            good = sum(1 for i in self.inputs if i.status == "ok")
            self.shake_t = 0.5
            self.feedback = ("bad", f"{good} de {len(self.inputs)} casillas correctas. Revisa las rojas.")
            self.feedback_t = 90

    def use_hint(self):
        if self.hints_unlocked < 3:
            cost = [50, 100, 150][self.hints_unlocked]
            self.hints_unlocked += 1
            paid = min(cost, self.score)  # el puntaje nunca baja de 0
            self.score -= paid
            self.hint_paid += paid
            self.feedback = ("bad", f"Pista usada: −{cost} puntos")
            self.feedback_t = 90

    def skip_event(self):
        self.mission_active = False
        self.feedback = None
        self.mode = "MAP"

    def timeout(self):
        entry = self.current_entry()
        self.streak = 0
        self.mission_active = False
        if entry["type"] == "event":
            self.result_status = "event_fail"  # los eventos no cuestan vida
            self.feedback = ("bad", "¡Tiempo agotado!")
            self.flash = 40
            return
        self.lives -= 1
        self.score = max(0, self.score - 100)
        if self.lives <= 0:
            self.result_status = "gameover"
        else:
            self.result_status = "retry"
        self.feedback = ("bad", "¡Tiempo agotado!")
        self.flash = 40

    def advance(self):
        self.done.add(self.current_entry()["def"]["id"])
        if self.worlds_done() >= len(engine.WORLDS):
            self.finish_run("Completada")
            self.mode = "WIN"
        else:
            self.autosave()
            self.feedback_t = 0
            self.mode = "MAP"

    def finish_run(self, status):
        hints_total = self.hints_unlocked
        data.add_record(self.store, self.name or "Jugador", self.score, self.worlds_done(), hints_total, status)
        self.store["save"] = None
        data.save(self.store)

    def snapshot(self):
        """Estado de la misión en curso (para guardar y reanudar)."""
        return {"id": self.current_entry()["def"]["id"], "seed": self.seed, "time_left": self.time_left,
                "texts": [i.text for i in self.inputs], "focus": self.focus,
                "hints_unlocked": self.hints_unlocked, "hint_paid": self.hint_paid,
                "wrong_attempts": self.wrong_attempts}

    def autosave(self):
        mission = self.snapshot() if (self.mission_active and self.mode == "MISSION") else self.resume
        self.store["save"] = {
            "name": self.name, "done": sorted(self.done), "lives": self.lives,
            "score": self.score, "streak": self.streak, "mission": mission,
        }
        data.save(self.store)

    def load_continue(self):
        s = self.store.get("save")
        if not s:
            return False
        self.name = s["name"]
        self.done = set(s.get("done", []))
        self.lives = s["lives"]
        self.score = s["score"]
        self.streak = s["streak"]
        self.resume = s.get("mission")
        return True


game = Game()


# ----------------------------------------------------------------- MENU
def draw_menu():
    draw_background()
    t = pygame.time.get_ticks() / 1000.0
    _draw_map_sky(t)
    # título con pulso de brillo y leve flotación
    ui.panel(screen,(190,48,620,122),glow=(112,180,232),radius=24,fill=(15,25,45))
    ui.draw_text(screen, "ASTRO NUMÉRICA", (SCREEN_W // 2, 66 + int(2 * math.sin(t * 1.6))), 54, (255,255,255), bold=True, center=True)
    ui.draw_text(screen, "Resuelve. Vuela. Sobrevive.", (SCREEN_W // 2, 132), 20, (239,245,255), center=True)
    # planetas flotando, con brillo y una nave que cruza
    for i, (pid, (px, py)) in enumerate((("helios", (120, 150)), ("vesper", (880, 150)),
                                         ("ares", (150, 470)), ("ganimedes", (860, 480)))):
        img = PLANET_IMG.get(pid)
        if img:
            anim._glow(screen, PLANET_COLORS[i] if i < len(PLANET_COLORS) else ui.ACCENT, (px, py), 62 + 4 * math.sin(t * 1.8 + i), 30)
            by = py + int(8 * math.sin(t * 1.1 + i * 1.7))
            bx = px + int(4 * math.cos(t * 0.9 + i))
            screen.blit(img, img.get_rect(center=(bx, by)))
    # nave cruzando la pantalla
    k = (t % 9.0) / 9.0
    sx, sy = -40 + k * (SCREEN_W + 80), 560 + 25 * math.sin(k * 6.28 * 2)
    for j in range(10):
        anim._glow(screen, (255, 170, 60), (sx - 10 - j * 7, sy), max(1, 5 - j * 0.4), 200 * (1 - j / 10))
    anim._ship(screen, (sx, sy), 0) if False else pygame.draw.polygon(screen, (220, 230, 255), [(sx + 14, sy), (sx - 8, sy - 7), (sx - 4, sy), (sx - 8, sy + 7)])

    ui.panel(screen, (340, 220, 320, 90))
    ui.draw_text(screen, "Tu nombre (Enter para comenzar):", (360, 232), 15, ui.TEXT_DIM)
    game.name_input.rect.topleft = (360, 256)
    game.name_input.active = True
    game.name_input.draw(screen)

    labels = ["Comenzar", "Continuar" if game.store.get("save") else None, "Récords", "Cómo jugar"]
    game.buttons["menu"] = []
    y = 340
    for lab in labels:
        if lab is None:
            y += 56
            continue
        btn = ui.Button((380, y, 240, 46), lab, enabled=True)
        game.buttons["menu"].append((lab, btn))
        btn.update(pygame.mouse.get_pos())
        btn.draw(screen)
        y += 56


def start_new_game():
    game.name = game.name_input.text.strip() or "Jugador"
    game.store["last_name"] = game.name  # se recuerda para la próxima vez
    data.save(game.store)
    game.seq_i, game.lives, game.score, game.streak = 0, 3, 0, 0
    game.done = set()
    game.resume = None
    game.mode = "MAP"


def begin_mission():
    for k in ("check", "hint", "calc", "save"):
        game.buttons.pop(k, None)
    game.start_mission()
    game.mode = "MISSION"


def handle_menu(event):
    game.name_input.handle(event)
    game.name_input.active = True  # la casilla del nombre nunca pierde el foco
    if game.name_input.submitted:  # Enter en la casilla del nombre = Comenzar
        game.name_input.submitted = False
        start_new_game()
        return
    for lab, btn in game.buttons.get("menu", []):
        if btn.clicked(event):
            if lab == "Comenzar":
                start_new_game()
            elif lab == "Continuar":
                if game.load_continue():
                    typed = game.name_input.text.strip()
                    if typed:
                        game.name = typed
                        game.store["last_name"] = typed
                        data.save(game.store)
                    game.mode = "MAP"
            elif lab == "Récords":
                game.mode = "RECORDS"
            elif lab == "Cómo jugar":
                game.mode = "HELP"


# ----------------------------------------------------------- WORLD/EVENT INTRO
def draw_intro():
    draw_background()
    entry = game.current_entry()
    d = entry["def"]

    parent=engine.PARENT.get(d['id'])
    label='PLANETA PRINCIPAL' if parent is None else 'LUNA OPCIONAL · Órbita de '+engine.destination_name(parent)
    ui.panel(screen,(18,14,964,105),radius=16)
    ui.draw_text(screen,label,(SCREEN_W//2,27),15,ui.ACCENT,bold=True,center=True)
    ui.draw_text(screen,engine.destination_title(d['id']),(SCREEN_W//2,57),28,ui.TEXT,bold=True,center=True,max_w=924)

    ui.panel(screen, (140, 130, SCREEN_W - 280, 140))
    ui.draw_text(screen, d.get("story", ""), (166, 145), 20, ui.TEXT, max_w=SCREEN_W - 332)
    mins, secs = divmod(d["time"], 60)
    ui.draw_text(screen, f"Método: {d['method']}   ·   Tiempo límite: {mins}:{secs:02d} min",
                 (SCREEN_W // 2, 295), 18, ui.TEXT_DIM, center=True)
    ui.draw_shields(screen, (SCREEN_W // 2 - 34, 350), game.lives)
    ui.draw_text(screen, f"Puntos: {game.score}   Racha: {game.streak}", (SCREEN_W // 2, 375), 18, ui.TEXT_DIM, center=True)
    ui.draw_text(screen, "Presiona Enter o Espacio para continuar", (SCREEN_W // 2, 420), 14, ui.TEXT_DIM, center=True)
    btn = ui.Button((SCREEN_W // 2 - 110, 445, 220, 50), "Continuar")
    btn.update(pygame.mouse.get_pos())
    btn.draw(screen)
    game.buttons["intro"] = btn
    skip_btn = ui.Button((SCREEN_W // 2 - 110, 510, 220, 40), "Volver al mapa", size=18)
    skip_btn.update(pygame.mouse.get_pos())
    skip_btn.draw(screen)
    game.buttons["intro_skip"] = skip_btn


def handle_intro(event):
    if (game.buttons.get("intro") and game.buttons["intro"].clicked(event)) or (
            event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)):
        begin_mission()
        return
    sk = game.buttons.get("intro_skip")
    if sk and sk.clicked(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
        game.mode = "MAP"


# ----------------------------------------------------------------- MISSION
VIEW = pygame.Rect(250, 75, 720, 410)   # panel con el contenido desplazable
CONTENT_X, CONTENT_W = 270, 680


def _col_widths(headers, rows, total):
    w = []
    for j, h in enumerate(headers):
        longest = len(str(h))
        for r in rows:
            c = r[j] if j < len(r) else ""
            longest = max(longest, 9 if isinstance(c, engine.B) else len(str(c)))
        w.append(max(8, min(longest, 38)))
    s = sum(w)
    return [int(total * x / s) for x in w]


def render_content(draw):
    """Coloca (y dibuja si draw=True) el enunciado y las tablas; devuelve la altura total.
    Las casillas quedan en inp.cy (y del contenido) y inp.rect (en pantalla)."""
    p = game.problem
    y = 8 - game.scroll
    top = VIEW.y
    W = CONTENT_W

    def text(t, size, color, bold=False):
        nonlocal y
        h = ui.text_height(t, size, bold, W)
        if draw:
            ui.draw_text(screen, t, (CONTENT_X, top + y), size, color, bold=bold, max_w=W)
        y += h + 6

    def table(tb, interactive):
        nonlocal y, box_i
        if tb.get("title"):
            text(tb["title"], 16, ui.ACCENT, True)
        hdr, rows = tb["headers"], tb["rows"]
        cw = _col_widths(hdr, rows, W)
        xs = [CONTENT_X + sum(cw[:j]) for j in range(len(cw))]
        hh = max(ui.text_height(h, 15, True, cw[j] - 10) for j, h in enumerate(hdr)) + 14
        if draw:
            pygame.draw.rect(screen, (30, 48, 80), (CONTENT_X, top + y, W, hh))
            for j, h in enumerate(hdr):
                ui.draw_text(screen, h, (xs[j] + cw[j] // 2, top + y + 7), 15, ui.ACCENT, bold=True, center=True, max_w=cw[j] - 10)
        y += hh
        for ri, r in enumerate(rows):
            rh = 46 if interactive else 30
            for j, c in enumerate(r):
                if not isinstance(c, engine.B):
                    rh = max(rh, ui.text_height(c, 15, False, cw[j] - 10) + (14 if interactive else 8))
            if draw:
                pygame.draw.rect(screen, (22, 34, 58) if ri % 2 == 0 else (26, 40, 66), (CONTENT_X, top + y, W, rh))
            for j, c in enumerate(r):
                if isinstance(c, engine.B):
                    inp = game.inputs[box_i]
                    bw = max(70, cw[j] - 22)
                    inp.cy = y + (rh - 34) // 2
                    inp.rect = pygame.Rect(xs[j] + (cw[j] - bw) // 2, top + inp.cy, bw, 34)
                    box_i += 1
                elif draw and str(c) != "":
                    th = ui.text_height(c, 15, False, cw[j] - 10)
                    ui.draw_text(screen, c, (xs[j] + cw[j] // 2, top + y + (rh - th) // 2), 15, ui.TEXT, center=True, max_w=cw[j] - 10)
            y += rh
        y += 14

    box_i = 0
    text(p["prompt"], 17, ui.TEXT)
    if p.get("data"):
        y += 4
        table(p["data"], False)
    text(p["formula"], 15, ui.ACCENT)
    for lvl in range(game.hints_unlocked):
        text(f"Pista {lvl+1}: {p[f'hint{lvl+1}']}", 15, ui.WARN)
    y += 6
    text("Procedimiento", 20, ui.TEXT, True)
    for tb in p["steps"]:
        table(tb, True)
    return y + game.scroll


def draw_mission():
    draw_background()
    entry = game.current_entry()
    d = entry["def"]
    p = game.problem

    ui.draw_shields(screen, (30, 24), game.lives)
    ui.draw_text(screen, f"Puntos: {game.score}", (150, 16), 20, ui.TEXT)
    ui.draw_text(screen, f"Racha: {game.streak}", (150, 42), 16, ui.TEXT_DIM)
    frac = max(0.0, game.time_left / game.time_total)
    ui.draw_timebar(screen, (SCREEN_W // 2 - 170, 20, 400, 22), frac)
    secs_left = max(0, math.ceil(game.time_left))
    ui.draw_text(screen, f"{secs_left // 60}:{secs_left % 60:02d}", (SCREEN_W // 2, 46), 16, ui.TEXT_DIM, center=True)
    ui.draw_text(screen, d["name"], (SCREEN_W - 250, 46), 16, ui.ACCENT)

    # --- columna izquierda: escena animada del planeta (según la historia del problema)
    pid = d["id"] if d["id"] in PLANET_IMG else engine.PARENT.get(d["id"])
    big = pygame.transform.scale(PLANET_IMG[pid], (180, 180)) if PLANET_IMG.get(pid) else None
    moon = pygame.transform.scale(MOON_IMG, (48, 48)) if (MOON_IMG and d["id"] != pid) else None
    anim.draw_scene(screen, pid, pygame.time.get_ticks() / 1000.0, big, moon,
                    shake=min(1.0, game.shake_t * 2), danger=frac < 0.2 and game.mission_active)
    ui.draw_text(screen, d["name"].split(" · ")[0], (135, 440), 22, ui.TEXT, center=True)
    ui.draw_text(screen, d["method"], (135, 466), 13, ui.TEXT_DIM, center=True, max_w=225)

    # --- panel con el procedimiento (se desplaza con la rueda del mouse)
    ui.panel(screen, VIEW)
    total = render_content(False)
    max_scroll = max(0, total - VIEW.height + 12)
    if game.ensure_visible and game.inputs:
        cy = game.inputs[game.focus].cy  # en coordenadas del contenido
        if cy - game.scroll < 10:
            game.scroll = max(0, cy - 20)
        elif cy + 44 - game.scroll > VIEW.height - 6:
            game.scroll = cy + 50 - VIEW.height
        game.ensure_visible = False
    game.scroll = max(0, min(game.scroll, max_scroll))
    game.max_scroll = max_scroll
    screen.set_clip(VIEW.inflate(-6, -6))
    render_content(True)
    for inp in game.inputs:
        if VIEW.colliderect(inp.rect):
            inp.draw(screen)
    screen.set_clip(None)
    if max_scroll > 0:  # barra de desplazamiento
        bar_h = max(30, int((VIEW.height - 20) * VIEW.height / (total + 12)))
        bar_y = VIEW.y + 10 + int((VIEW.height - 20 - bar_h) * game.scroll / max_scroll)
        pygame.draw.rect(screen, (70, 100, 150), (VIEW.right - 10, bar_y, 5, bar_h), border_radius=3)

    check_btn = ui.Button((SCREEN_W - 30 - 190, 492, 190, 46), "Comprobar")
    check_btn.update(pygame.mouse.get_pos())
    check_btn.draw(screen)
    game.buttons["check"] = check_btn
    ui.draw_text(screen, "Enter = siguiente · Tab = cambiar · Rueda = desplazar", (255, 497), 13, ui.TEXT_DIM, max_w=260)
    save_btn = ui.Button((535, 492, 230, 46), "Guardar y salir", size=20)
    save_btn.update(pygame.mouse.get_pos())
    save_btn.draw(screen)
    game.buttons["save"] = save_btn

    hint_label = f"Pista ({[50,100,150][game.hints_unlocked] if game.hints_unlocked < 3 else '—'})"
    hint_btn = ui.Button((30, 492, 100, 46), hint_label if game.hints_unlocked < 3 else "Sin pistas",
                          enabled=game.hints_unlocked < 3, size=18)
    hint_btn.update(pygame.mouse.get_pos())
    hint_btn.draw(screen)
    game.buttons["hint"] = hint_btn

    calc_btn = ui.Button((140, 492, 100, 46), "Calc.", size=18)
    calc_btn.update(pygame.mouse.get_pos())
    calc_btn.draw(screen)
    game.buttons["calc"] = calc_btn

    if game.feedback:
        kind, msg = game.feedback
        color = ui.GOOD if kind == "ok" else ui.BAD
        ui.draw_text(screen, msg, (SCREEN_W // 2, 566), 20, color, center=True, bold=True)

    if game.show_calc:
        draw_calculator()


def draw_calculator():
    rect = pygame.Rect(SCREEN_W // 2 - 170, 150, 340, 230)
    ui.panel(screen, rect, glow=ui.ACCENT, fill=(16, 18, 32))
    ui.draw_text(screen, "Calculadora", (rect.x + 16, rect.y + 10), 18, ui.ACCENT, bold=True)
    ui.draw_text(screen, game.calc_expr or "0", (rect.x + 16, rect.y + 38), 22, ui.TEXT)
    keys = ["7", "8", "9", "/", "4", "5", "6", "*",
            "1", "2", "3", "-", "0", ".", "√", "+",
            "^", "log", "C", "="]
    game.buttons["calc_keys"] = []
    for i, k in enumerate(keys):
        kx = rect.x + 16 + (i % 4) * 78
        ky = rect.y + 70 + (i // 4) * 38
        b = ui.Button((kx, ky, 70, 32), k, size=16)
        b.update(pygame.mouse.get_pos())
        b.draw(screen)
        game.buttons["calc_keys"].append((k, b))


def calc_press(k):
    if k == "C":
        game.calc_expr = ""
    elif k == "=":
        expr = game.calc_expr.replace("√", "math.sqrt").replace("^", "**").replace("log", "math.log10")
        try:
            val = eval(expr, {"__builtins__": {}}, {"math": math})
            game.inputs[game.focus].text = str(round(float(val), 6))
            game.calc_expr = ""
            game.show_calc = False
        except Exception:
            game.calc_expr = "Error"
    elif k == "√":
        game.calc_expr += "√("
    elif k == "log":
        game.calc_expr += "log("
    else:
        game.calc_expr += k


def do_submit():
    game.submit()
    if game.result_status == "advance":
        game.mode = "TRAVEL"


def handle_mission(event):
    if game.show_calc:
        if event.type == pygame.MOUSEBUTTONDOWN:
            for k, b in game.buttons.get("calc_keys", []):
                if b.clicked(event):
                    calc_press(k)
                    return
            calc_rect = pygame.Rect(SCREEN_W // 2 - 170, 150, 340, 230)
            if not calc_rect.collidepoint(event.pos):
                game.show_calc = False
        return

    # Siempre hay exactamente una casilla activa (game.focus): se escribe sin hacer clic.
    enter_pressed = False
    if event.type == pygame.MOUSEWHEEL:
        game.scroll = max(0, min(getattr(game, "max_scroll", 0), game.scroll - event.y * 45))
        return
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        if VIEW.collidepoint(event.pos):
            for i, inp in enumerate(game.inputs):
                if inp.rect.collidepoint(event.pos):
                    game.focus = i
                    game.ensure_visible = True
    elif event.type == pygame.KEYDOWN:
        if event.key == pygame.K_PAGEDOWN:
            game.scroll = min(getattr(game, "max_scroll", 0), game.scroll + 300)
            return
        if event.key == pygame.K_PAGEUP:
            game.scroll = max(0, game.scroll - 300)
            return
        if event.key == pygame.K_TAB:
            game.focus = (game.focus + 1) % len(game.inputs)
            game.ensure_visible = True
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            enter_pressed = True
        else:
            for i, inp in enumerate(game.inputs):
                inp.active = (i == game.focus)
                inp.handle(event)
    for i, inp in enumerate(game.inputs):
        inp.active = (i == game.focus)

    if enter_pressed:
        # Enter pasa a la siguiente casilla; en la última, comprueba.
        if game.focus < len(game.inputs) - 1:
            game.focus += 1
            game.ensure_visible = True
        else:
            do_submit()
            return

    if not all(k in game.buttons for k in ("check", "save")):
        return  # aún no se dibuja el primer cuadro de la misión
    if game.buttons["save"].clicked(event):
        game.resume = game.snapshot()
        game.mission_active = False
        game.autosave()
        game.feedback = ("bad", "Progreso guardado. Puedes continuar este problema desde el mapa.")
        game.feedback_t = 180
        game.mode = "MAP"
        return
    if game.buttons["check"].clicked(event):
        do_submit()
        return
    if game.buttons.get('hint') and game.buttons["hint"].clicked(event):
        game.use_hint()
    if game.buttons.get('calc') and game.buttons["calc"].clicked(event):
        game.show_calc = True
        game.calc_expr = ""


def update_mission(dt):
    game.shake_t = max(0.0, game.shake_t - dt)
    if game.mission_active:
        game.time_left -= dt
        if game.time_left <= 0:
            game.time_left = 0
            game.timeout()
            game.autosave()
            game.mode = "TRAVEL"


# ----------------------------------------------------------------- MAP
import math as _math

PLANET_CENTERS = [(125, 205), (375, 205), (625, 205), (875, 205), (250, 440), (500, 440), (750, 440)]
RING = 78


def map_nodes():
    """[(id, def, (x,y), radio, estado, idx_familia, es_planeta)]"""
    nodes = []
    for fi, (pid, title, moons) in enumerate(engine.FAMILIES):
        cx, cy = PLANET_CENTERS[fi]
        nodes.append((pid, engine._ALL[pid], (cx, cy), 38, "done" if pid in game.done else "open", fi, True))
        t = pygame.time.get_ticks() / 1000.0
        spin = 0.16 * (1 if fi % 2 == 0 else -1)   # las lunas giran, alternando el sentido
        for k, mid in enumerate(moons):
            ang = -_math.pi / 2 + 2 * _math.pi * k / len(moons) + t * spin
            pos = (int(cx + RING * _math.cos(ang)), int(cy + RING * _math.sin(ang)))
            nodes.append((mid, engine._ALL[mid], pos, 15, "done" if mid in game.done else "open", fi, False))
    return nodes


MAP_STARS = [(random.randint(10, SCREEN_W - 10), random.randint(10, SCREEN_H - 10),
              random.uniform(0, 6.28), random.uniform(1.0, 2.6)) for _ in range(45)]


def _draw_map_sky(t):
    """Estrellas que titilan y una estrella fugaz de vez en cuando."""
    for x, y, ph, sp in MAP_STARS:
        b = 0.25 + 0.75 * abs(math.sin(t * sp + ph))
        col = (int(255 * b), int(225 * b), int(120 * b))
        pygame.draw.rect(screen, col, (x - 1, y - 1, 3, 3))
        if b > 0.8:
            for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
                pygame.draw.rect(screen, (int(160 * b), int(140 * b), int(80 * b)), (x + dx - 1, y + dy - 1, 2, 2))
    period = 7.0
    k = (t % period) / 1.1
    if k < 1:
        rnd = random.Random(int(t / period))
        sx, sy = rnd.randint(300, SCREEN_W), rnd.randint(40, 260)
        for i in range(14):
            kk = max(0.0, k - i * 0.025)
            p = (sx - kk * 360, sy + kk * 150)
            anim._glow(screen, (200, 225, 255), p, max(1, 4 - i * 0.25), 230 * (1 - k) * (1 - i / 14))


def draw_map():
    draw_background()
    t_now = pygame.time.get_ticks() / 1000.0
    _draw_map_sky(t_now)
    ui.draw_shields(screen, (30, 24), game.lives)
    ui.draw_text(screen, f"Puntos: {game.score}   Racha: {game.streak}", (24, 48), 16, ui.TEXT)
    ui.draw_text(screen, "MAPA DE LA EXPEDICIÓN", (SCREEN_W // 2, 12), 26, ui.ACCENT, bold=True, center=True)
    ui.draw_text(screen, f"Planetas: {game.worlds_done()}/{len(engine.WORLDS)}", (SCREEN_W - 80, 18), 20, ui.TEXT, center=True)
    mouse = pygame.mouse.get_pos()
    hover = None
    nodes = map_nodes()
    for fi, (pid, title, moons) in enumerate(engine.FAMILIES):
        cx, cy = PLANET_CENTERS[fi]
        pygame.draw.circle(screen, (35, 42, 70), (cx, cy), RING, width=1)  # órbita
    for nid, d, (x, y), r, state, fi, is_planet in nodes:
        col = ui.GOOD if state == "done" else PLANET_COLORS[fi]
        if game.resume and game.resume.get("id") == nid:
            pygame.draw.circle(screen, ui.WARN, (x, y), r + 6, width=3)  # problema guardado
        if (mouse[0] - x) ** 2 + (mouse[1] - y) ** 2 <= (r + 4) ** 2:
            hover = (d, state, is_planet)
            game.map_selection=nid
        if nid==getattr(game,'map_selection',None):
            pygame.draw.circle(screen,ui.ACCENT,(x,y),r+5,width=2)
        if is_planet:
            img = PLANET_IMG.get(nid)
            pulse = 0.5 + 0.5 * math.sin(t_now * 1.8 + fi)
            gcol = ui.GOOD if state == "done" else PLANET_COLORS[fi]
            anim._glow(screen, gcol, (x, y), 52 + 4 * pulse, 28 + 30 * pulse)
            by = y + int(3 * math.sin(t_now * 1.5 + fi * 1.3))   # el planeta flota suavemente
            if img:
                if hover and hover[0]["id"] == nid:
                    img = pygame.transform.scale(img, (106, 106))
                screen.blit(img, img.get_rect(center=(x, by)))
            else:
                pygame.draw.circle(screen, col, (x, y), r)
            if state == "done":  # palomita verde sobre el planeta
                pygame.draw.circle(screen, (10, 12, 22), (x + 26, y - 26), 13)
                pygame.draw.circle(screen, ui.GOOD, (x + 26, y - 26), 11)
                pygame.draw.lines(screen, (10, 12, 22), False,
                                  [(x + 20, y - 26), (x + 25, y - 21), (x + 33, y - 31)], 3)
        else:
            img = MOON_DONE_IMG if state == "done" else MOON_IMG
            if state == "open":  # halo que respira: invita a jugar
                anim._glow(screen, col, (x, y), 17 + 2 * math.sin(t_now * 3 + x), 35)
            if img:
                screen.blit(img, img.get_rect(center=(x, y)))
                if state != "done":
                    pygame.draw.circle(screen, col, (x, y), r + 1, width=2)
            else:
                pygame.draw.circle(screen, col, (x, y), r, width=0 if state == "done" else 2)
    # Placas opacas después de las estrellas y las lunas: el texto permanece
    # limpio durante toda la animación y en ambos temas de la interfaz.
    for fi,(pid,title,moons) in enumerate(engine.FAMILIES):
        cx,cy=PLANET_CENTERS[fi];plate=pygame.Rect(cx-119,cy+RING+10,238,36)
        ui.panel(screen,plate,glow=(73,91,121),radius=10,fill=(14,24,43))
        pygame.draw.rect(screen,PLANET_COLORS[fi],(plate.x+7,plate.y+8,3,20),border_radius=1)
        ui.draw_text(screen,engine.destination_name(pid),(cx,plate.y+6),18,(255,255,255),bold=True,center=True)

    # Panel de información persistente (abajo, siempre visible)
    selected=getattr(game,'map_selection',None)
    title='Explora los planetas y sus lunas'
    detail='Acerca el cursor a un destino. Su información quedará visible al retirarlo.'
    if selected in engine._ALL:
        d=engine._ALL[selected];parent=engine.PARENT.get(selected)
        title=engine.destination_title(selected)
        kind='Planeta principal' if parent is None else 'Luna de '+engine.destination_name(parent)
        detail=f"{kind} · {d['method']} · {d['time']//60} min"
        if selected in game.done:detail+=' · Completado'
        elif game.resume and game.resume.get('id')==selected:detail+=' · En progreso'
    game.map_info=(title,detail)
    ui.panel(screen,(18,570,964,64),radius=12)
    ui.draw_text(screen,title,(34,577),21,ui.TEXT,bold=True,max_w=932)
    ui.draw_text(screen,detail,(34,605),19,ui.TEXT_DIM,max_w=932)
    if game.feedback and game.feedback_t > 0:
        game.feedback_t -= 1
        ui.draw_text(screen, game.feedback[1], (SCREEN_W // 2, 70), 18, ui.WARN, center=True)
    menu_btn = ui.Button((SCREEN_W - 130, 56, 110, 32), "Menú", size=16)
    menu_btn.update(mouse)
    menu_btn.draw(screen)
    game.buttons["map_menu"] = menu_btn


def handle_map(event):
    mb = game.buttons.get("map_menu")
    if mb and mb.clicked(event):
        game.autosave()
        game.mode = "MENU"
        return
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        for nid, d, (x, y), r, state, fi, is_planet in map_nodes():
            if (event.pos[0] - x) ** 2 + (event.pos[1] - y) ** 2 <= (r + 4) ** 2:
                game.map_selection=nid
                if state == "done":
                    game.feedback = ("bad", "Ya completaste este mundo.")
                    game.feedback_t = 90
                else:
                    game.select(nid)
                    game.mode = "WORLD_INTRO"
                return


# ----------------------------------------------------------------- TRAVEL (mapa/transición)
def draw_travel():
    draw_background()
    ok = game.result_status in ("advance",)
    msg = ("¡Procedimiento correcto!" if ok else
           "Tiempo agotado en el evento (sin penalización)" if game.result_status == "event_fail" else
           "Tiempo agotado. Reintentando misión..." if game.result_status == "retry" else "¡Sin vidas!")
    ui.draw_text(screen, msg, (SCREEN_W // 2, 70), 30, ui.GOOD if ok else ui.BAD, center=True, bold=True)
    d = game.current_entry()["def"]
    pid = d["id"] if d["id"] in PLANET_IMG else engine.PARENT.get(d["id"])
    k = max(0.0, min(1.0, 1 - game.flash / 70.0))
    if PLANET_IMG.get(pid):
        size = int(200 * (1 + 0.08 * math.sin(k * 12)))
        img = pygame.transform.scale(PLANET_IMG[pid], (size, size))
        screen.blit(img, img.get_rect(center=(SCREEN_W // 2, 290)))
    anim.celebrate(screen, (SCREEN_W // 2, 290), k, ok)
    ui.draw_text(screen, f"Planetas completados: {game.worlds_done()} de {len(engine.WORLDS)}",
                 (SCREEN_W // 2, 450), 22, ui.TEXT_DIM, center=True)
    ui.draw_text(screen, "Puntuación: " + str(game.score), (SCREEN_W // 2, 490), 22, ui.TEXT, center=True)


def update_travel(dt):
    game.flash -= 1
    if game.flash <= 0:
        if game.result_status == "advance":
            game.advance()
        elif game.result_status == "event_fail":
            game.mode = "MAP"
        elif game.result_status == "retry":
            game.mode = "WORLD_INTRO"  # mismo mundo, nueva variante al continuar
        elif game.result_status == "gameover":
            game.finish_run("Vidas agotadas")
            game.mode = "LOSE"
        game.result_status = None


# ----------------------------------------------------------------- HELP / RECORDS / WIN / LOSE
def draw_help():
    draw_background()
    ui.draw_text(screen, "Cómo jugar", (SCREEN_W // 2, 50), 34, ui.ACCENT, bold=True, center=True)
    rules = [
        "Cada mundo plantea una emergencia que se resuelve con un método numérico.",
        "Llena las casillas del procedimiento (paso a paso) y presiona Comprobar. Rojo = incorrecta.",
        "Tienes 3 vidas (escudos). Si se agota el tiempo de una misión principal,",
        "pierdes una vida y reintentas con otro problema del mismo mundo.",
        "Un error de casilla NO quita vida, pero sí interrumpe tu racha.",
        "Las pistas cuestan puntos (50, 100 y 150) y se usan una sola vez cada una.",
        "Las lunas dan puntos extra; omitirlas o fallarlas no cuesta vidas.",
        "Cada planeta es un método principal; sus lunas son métodos parecidos. La expedición termina al completar los 7 planetas o al perder las 3 vidas.",
        "",
        "Incluye 32 métodos numéricos: 7 planetas (obligatorios) y 27 lunas (opcionales)",
        "(interpolación, raíces, sistemas, integración, EDO y mínimos cuadrados).",
    ]
    y = 110
    for r in rules:
        ui.draw_text(screen, r, (SCREEN_W // 2, y), 18, ui.TEXT if r else ui.TEXT, center=True)
        y += 28
    btn = ui.Button((SCREEN_W // 2 - 90, y + 20, 180, 44), "Volver")
    btn.update(pygame.mouse.get_pos())
    btn.draw(screen)
    game.buttons["back"] = btn


def draw_records():
    draw_background()
    ui.draw_text(screen, "Récords", (SCREEN_W // 2, 50), 34, ui.ACCENT, bold=True, center=True)
    recs = game.store.get("records", [])
    headers = "#   Nombre            Puntos  Mundos  Pistas  Fecha        Estado"
    ui.draw_text(screen, headers, (90, 110), 16, ui.TEXT_DIM)
    y = 140
    for i, r in enumerate(recs[:15]):
        line = f"{i+1:<3} {r['name']:<16} {r['points']:<7} {r['worlds']:<7} {r['hints']:<7} {r['date']:<12} {r['status']}"
        ui.draw_text(screen, line, (90, y), 16, ui.TEXT)
        y += 26
    if not recs:
        ui.draw_text(screen, "Todavía no hay partidas registradas.", (SCREEN_W // 2, 160), 18, ui.TEXT_DIM, center=True)
    btn = ui.Button((SCREEN_W // 2 - 90, 560, 180, 44), "Volver")
    btn.update(pygame.mouse.get_pos())
    btn.draw(screen)
    game.buttons["back"] = btn


def draw_endscreen(win):
    draw_background()
    title = "¡Expedición completada!" if win else "Expedición perdida"
    color = ui.GOOD if win else ui.BAD
    ui.draw_text(screen, title, (SCREEN_W // 2, 220), 36, color, bold=True, center=True)
    ui.draw_text(screen, f"Puntuación final: {game.score}", (SCREEN_W // 2, 280), 24, ui.TEXT, center=True)
    ev_done = sum(1 for e in engine.EVENTS if e["id"] in game.done)
    ui.draw_text(screen, f"Planetas: {game.worlds_done()}/{len(engine.WORLDS)}   ·   Lunas: {ev_done}/{len(engine.EVENTS)}",
                 (SCREEN_W // 2, 320), 18, ui.TEXT_DIM, center=True)
    btn = ui.Button((SCREEN_W // 2 - 110, 360, 220, 48), "Volver al menú")
    btn.update(pygame.mouse.get_pos())
    btn.draw(screen)
    game.buttons["back"] = btn


def handle_simple_back(event):
    if game.buttons.get("back") and game.buttons["back"].clicked(event):
        game.mode = "MENU"


# ----------------------------------------------------------------------- LOOP
def main():
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                data.save(game.store)
                running = False
            elif event.type == pygame.KEYDOWN and (event.key == pygame.K_F11 or (
                    event.key == pygame.K_RETURN and event.mod & pygame.KMOD_ALT)):
                pygame.display.toggle_fullscreen()   # F11 o Alt+Enter: pantalla completa
            elif game.mode == "MENU":
                handle_menu(event)
            elif game.mode == "MAP":
                handle_map(event)
            elif game.mode == "WORLD_INTRO":
                handle_intro(event)
            elif game.mode == "MISSION":
                handle_mission(event)
            elif game.mode == "HELP":
                handle_simple_back(event)
            elif game.mode == "RECORDS":
                handle_simple_back(event)
            elif game.mode in ("WIN", "LOSE"):
                handle_simple_back(event)

        if game.mode == "MENU":
            draw_menu()
        elif game.mode == "MAP":
            draw_map()
        elif game.mode == "WORLD_INTRO":
            draw_intro()
        elif game.mode == "MISSION":
            update_mission(dt)
            draw_mission()
            game.save_timer_accum += dt
            if game.save_timer_accum >= 5:
                game.autosave()
                game.save_timer_accum = 0
        elif game.mode == "TRAVEL":
            update_travel(dt)
            draw_travel()
        elif game.mode == "HELP":
            draw_help()
        elif game.mode == "RECORDS":
            draw_records()
        elif game.mode == "WIN":
            draw_endscreen(True)
        elif game.mode == "LOSE":
            draw_endscreen(False)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


from fusion_runtime import install
install(globals())

async def browser_main():
    running = True
    while running:
        dt = min(clock.tick(60) / 1000.0, 0.1)
        for event in pygame.event.get():
            running = fusion_dispatch(event) and running
        if running:
            fusion_tick(dt)
            pygame.display.flip()
        await asyncio.sleep(0)

if __name__ == "__main__":
    if sys.platform == "emscripten":
        asyncio.run(browser_main())
    else:
        main()
