"""ui.py — Helpers de dibujo: estilo 'cristal oscuro con bordes iluminados'."""
import pygame
import os
from typography import MathFont

BG = (10, 12, 22)
PANEL = (22, 26, 44)
PANEL_LIGHT = (30, 35, 58)
ACCENT = (96, 200, 255)
ACCENT_SOFT = (60, 110, 160)
GOOD = (110, 230, 150)
BAD = (240, 100, 110)
WARN = (250, 200, 90)
TEXT = (255, 255, 255)
TEXT_DIM = (232, 237, 246)
TABLE_HEAD=(30,48,80)
TABLE_ROW=(22,34,58)
TABLE_ALT=(26,40,66)
OK_FILL=(18,40,28)
BAD_FILL=(50,22,30)
THEME='dark'

def set_theme(name):
    global THEME,BG,PANEL,PANEL_LIGHT,ACCENT,ACCENT_SOFT,GOOD,BAD,WARN,TEXT,TEXT_DIM,TABLE_HEAD,TABLE_ROW,TABLE_ALT,OK_FILL,BAD_FILL
    THEME='light' if name=='light' else 'dark'
    if THEME=='light':
        BG=(237,243,251);PANEL=(255,255,255);PANEL_LIGHT=(244,248,253)
        ACCENT=(16,79,153);ACCENT_SOFT=(107,132,163);GOOD=(19,106,61);BAD=(172,32,55);WARN=(133,76,0)
        TEXT=(17,31,53);TEXT_DIM=(48,65,89);TABLE_HEAD=(207,222,242);TABLE_ROW=(247,250,255);TABLE_ALT=(229,239,250)
        OK_FILL=(225,244,232);BAD_FILL=(255,232,236)
    else:
        BG=(10,12,22);PANEL=(22,26,44);PANEL_LIGHT=(30,35,58)
        ACCENT=(96,200,255);ACCENT_SOFT=(60,110,160);GOOD=(110,230,150);BAD=(240,100,110);WARN=(250,200,90)
        TEXT=(255,255,255);TEXT_DIM=(232,237,246);TABLE_HEAD=(30,48,80);TABLE_ROW=(22,34,58);TABLE_ALT=(26,40,66)
        OK_FILL=(18,40,28);BAD_FILL=(50,22,30)

pygame.font.init()
FONT_CACHE = {}


def font(size, bold=False):
    key = (size, bold)
    if key not in FONT_CACHE:
        f=MathFont(size,bold)
        FONT_CACHE[key] = f
    return FONT_CACHE[key]


def wrap_lines(text, f, max_w=None):
    lines = []
    for para in str(text).split("\n"):
        if max_w:
            cur = ""
            for w in para.split(" "):
                # Las sustituciones pueden no contener espacios. También deben
                # envolver esos tokens, sin encoger la letra ni ocultar cifras.
                if f.size(w)[0]>max_w:
                    if cur:lines.append(cur);cur=''
                    part=''
                    for ch in w:
                        if part and f.size(part+ch)[0]>max_w:
                            cuts=[i+1 for i,c in enumerate(part) if c in '+-*/' and i>=len(part)//3]
                            cut=cuts[-1] if cuts else len(part)
                            lines.append(part[:cut]);part=part[cut:]+ch
                        else:part+=ch
                    cur=part
                    continue
                test = (cur + " " + w).strip()
                if f.size(test)[0] > max_w and cur:
                    lines.append(cur)
                    cur = w
                else:
                    cur = test
            lines.append(cur)
        else:
            lines.append(para)
    return lines


def text_height(text, size=22, bold=False, max_w=None):
    f = font(size, bold)
    return len(wrap_lines(text, f, max_w)) * f.get_linesize()


def draw_text(surf, text, pos, size=22, color=None, bold=False, center=False, max_w=None):
    color=color or TEXT
    f = font(size, bold)
    lines = wrap_lines(text, f, max_w)
    y = pos[1]
    for line in lines:
        img = f.render(line, True, color)
        r = img.get_rect()
        if center:
            r.midtop = (pos[0], y)
        else:
            r.topleft = (pos[0], y)
        surf.blit(img, r)
        y += f.get_linesize()
    return y


def panel(surf, rect, glow=None, radius=18, fill=None):
    glow=glow or ACCENT_SOFT;fill=fill or PANEL
    pygame.draw.rect(surf, fill, rect, border_radius=radius)
    pygame.draw.rect(surf, glow, rect, width=2, border_radius=radius)


class Button:
    def __init__(self, rect, label, size=24, enabled=True):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.size = size
        self.enabled = enabled
        self.hover = False

    def update(self, mouse_pos):
        self.hover = self.enabled and self.rect.collidepoint(mouse_pos)

    def clicked(self, event):
        return (self.enabled and event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1 and self.rect.collidepoint(event.pos))

    def draw(self, surf):
        fill = PANEL_LIGHT if self.enabled else (20, 20, 28)
        glow = ACCENT if (self.hover and self.enabled) else ACCENT_SOFT if self.enabled else (60, 60, 70)
        primary=getattr(self,'primary',False)
        if primary:fill=ACCENT;glow=ACCENT
        panel(surf, self.rect, glow=glow, radius=12, fill=fill)
        color = TEXT if self.enabled else TEXT_DIM
        if primary:color=(255,255,255) if THEME=='light' else (8,23,40)
        img = font(self.size).render(self.label, True, color)
        surf.blit(img, img.get_rect(center=self.rect.center))


class TextInput:
    """Caja de texto para capturar un número (admite coma/punto y fracciones a/b)."""
    def __init__(self, rect, placeholder="", numeric=True, max_len=16):
        self.rect = pygame.Rect(rect)
        self.text = ""
        self.active = False
        self.placeholder = placeholder
        self.locked = False  # se bloquea cuando ya se validó correcto
        self.numeric = numeric  # False = acepta cualquier carácter imprimible (nombre)
        self.max_len = max_len
        self.submitted = False  # se activa al presionar Enter
        self.status = None  # None / "ok" / "bad": resultado de la última comprobación
        self.fresh = False  # True = la primera tecla reemplaza el texto precargado

    def handle(self, event):
        if self.locked:
            return
        if event.type == pygame.KEYDOWN and self.active and event.key not in (
                pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_TAB):
            self.status = None  # al editar, se quita la marca roja/verde
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                if self.fresh:
                    self.text = ""
                    self.fresh = False
                else:
                    self.text = self.text[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.submitted = True  # el juego decide qué hacer con Enter
            elif event.key == pygame.K_TAB:
                pass  # el cambio de casilla lo maneja el juego
            elif len(self.text) < self.max_len or self.fresh:
                ch = event.unicode
                if not ch:
                    return
                if self.fresh and (not self.numeric) and ch.isprintable():
                    self.text = ""
                self.fresh = False
                if self.numeric:
                    if ch.isdigit() or ch in "-.,/":
                        self.text += ch
                elif ch.isprintable():
                    self.text += ch

    def value(self):
        """Convierte el texto a float; admite coma decimal y fracción a/b."""
        t = self.text.strip().replace(",", ".")
        if not t:
            return None
        try:
            if "/" in t:
                num, den = t.split("/", 1)
                return float(num) / float(den)
            return float(t)
        except (ValueError, ZeroDivisionError):
            return None

    def draw(self, surf):
        glow = GOOD if (self.locked or self.status == "ok") else (
            BAD if self.status == "bad" else (ACCENT if self.active else ACCENT_SOFT))
        fill = (18, 40, 28) if (self.locked or self.status == "ok") else (
            (50, 22, 30) if self.status == "bad" else PANEL_LIGHT)
        panel(surf, self.rect, glow=glow, radius=10, fill=fill)
        shown = self.text if self.text else self.placeholder
        color = TEXT if self.text else TEXT_DIM
        img = font(22).render(shown, True, color)
        surf.blit(img, img.get_rect(midleft=(self.rect.x + 12, self.rect.centery)))


def draw_shields(surf, pos, lives, max_lives=3):
    x, y = pos
    for i in range(max_lives):
        color = ACCENT if i < lives else (50, 55, 70)
        pygame.draw.circle(surf, color, (x + i * 34, y), 12, width=0 if i < lives else 2)


def draw_timebar(surf, rect, frac, danger=0.2):
    rect = pygame.Rect(rect)
    pygame.draw.rect(surf, PANEL_LIGHT, rect, border_radius=8)
    inner = rect.copy()
    inner.width = max(0, int(rect.width * max(0.0, min(1.0, frac))))
    color = BAD if frac < danger else (WARN if frac < 0.5 else GOOD)
    if inner.width > 0:
        pygame.draw.rect(surf, color, inner, border_radius=8)
    pygame.draw.rect(surf, ACCENT_SOFT, rect, width=2, border_radius=8)
