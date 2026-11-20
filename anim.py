"""anim.py — Animaciones de la escena del planeta según la historia de cada problema.
Todo se dibuja por código (sin imágenes extra)."""
import math
import random
import pygame

AREA = pygame.Rect(15, 80, 240, 405)   # zona de la pantalla donde se anima
C = (135, 235)                         # centro del planeta


def _glow(surf, color, pos, r, alpha, width=0):
    r = max(1, int(r))
    s = pygame.Surface((2 * r + 4, 2 * r + 4), pygame.SRCALPHA)
    pygame.draw.circle(s, (*color, max(0, min(255, int(alpha)))), (r + 2, r + 2), r, width)
    surf.blit(s, (pos[0] - r - 2, pos[1] - r - 2))


def _lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _ship(surf, pos, ang, color=(220, 240, 255), size=9):
    c, s = math.cos(ang), math.sin(ang)
    pts = [(pos[0] + c * size * 1.4, pos[1] + s * size * 1.4),
           (pos[0] - c * size + s * size * 0.7, pos[1] - s * size - c * size * 0.7),
           (pos[0] - c * size * 0.5, pos[1] - s * size * 0.5),
           (pos[0] - c * size - s * size * 0.7, pos[1] - s * size + c * size * 0.7)]
    pygame.draw.polygon(surf, color, pts)
    _glow(surf, (255, 180, 80), (pos[0] - c * size * 1.1, pos[1] - s * size * 1.1), 5, 150)


def _explosion(surf, pos, k, color=(255, 190, 90)):
    """k de 0 a 1: anillos y chispas que se expanden y se desvanecen."""
    a = 255 * (1 - k)
    _glow(surf, (255, 240, 200), pos, 6 + 26 * k, a * 0.5)
    _glow(surf, color, pos, 10 + 42 * k, a, width=3)
    rnd = random.Random(7)
    for _ in range(12):
        ang, sp = rnd.uniform(0, 6.28), rnd.uniform(0.5, 1.2)
        p = (pos[0] + math.cos(ang) * 46 * k * sp, pos[1] + math.sin(ang) * 46 * k * sp)
        _glow(surf, color, p, 3, a)


def _helios(surf, t):
    ph = (t % 5.5) / 5.5
    start, impact = (240, 100), (206, 164)
    boom = 0.62
    k = min(ph / boom, 1)
    pos = _lerp(start, impact, k)
    if ph < boom:
        for i in range(9):  # estela
            q = _lerp(start, impact, max(0, k - i * 0.025))
            _glow(surf, (255, 150, 60), q, 7 - i * 0.6, 200 - i * 20)
        _glow(surf, (190, 120, 80), pos, 8, 255)
        _glow(surf, (255, 210, 120), pos, 4, 255)
    if 0.5 < ph < boom:  # cañón de partículas
        pygame.draw.line(surf, (120, 240, 255), (34, 410), pos, 3)
        _glow(surf, (120, 240, 255), (34, 410), 12, 160)
    if ph >= boom:
        _explosion(surf, impact, min(1, (ph - boom) / 0.3))


def _ares(surf, t):
    r = 112 + 6 * math.sin(t * 2)
    pygame.draw.ellipse(surf, (50, 60, 90), (C[0] - r, C[1] - r * 0.45, 2 * r, r * 0.9), 1)
    a = t * 0.9
    pos = (C[0] + math.cos(a) * r, C[1] + math.sin(a) * r * 0.45)
    _ship(surf, pos, a + math.pi / 2 + 0.2)
    ph = (t % 6.5) / 6.5  # asteroide que cruza
    ax, ay = 250 - ph * 280, 130 + 60 * math.sin(ph * 5)
    rnd = random.Random(3)
    pts = [(ax + math.cos(i * 0.9 + t) * (11 + rnd.random() * 5), ay + math.sin(i * 0.9 + t) * (11 + rnd.random() * 5))
           for i in range(7)]
    pygame.draw.polygon(surf, (150, 135, 120), pts)
    pygame.draw.polygon(surf, (90, 80, 70), pts, 2)


def _vesper(surf, t):
    A, Bp = (48, 150), (222, 330)
    for p in (A, Bp):
        _glow(surf, (255, 220, 120), p, 14 + 3 * math.sin(t * 6), 140)
        _glow(surf, (255, 250, 220), p, 5, 255)
    rnd = random.Random(int(t * 14))
    for end in (A, Bp):
        pts = [C]
        for i in range(1, 7):
            q = _lerp(C, end, i / 7)
            pts.append((q[0] + rnd.uniform(-10, 10), q[1] + rnd.uniform(-10, 10)))
        pts.append(end)
        if rnd.random() > 0.25:
            pygame.draw.lines(surf, (255, 235, 150), False, pts, 2)
    _glow(surf, (255, 200, 90), C, 95 + 8 * math.sin(t * 5), 40)


def _nereida(surf, t):
    for row in range(5):
        y0 = 345 + row * 20
        pts = [(x, y0 + 5 * math.sin(x * 0.05 + t * 2 + row)) for x in range(20, 252, 6)]
        pygame.draw.lines(surf, (70 + row * 12, 120 + row * 14, 210), False, pts, 3)
    ph = (t % 6) / 6
    x = 25 + ph * 210
    y = 320 + 6 * math.sin(t * 3)
    for i in range(8):
        _glow(surf, (150, 210, 255), (x - 10 - i * 8, y + 3), 4 - i * 0.3, 160 - i * 18)
    _ship(surf, (x, y), 0)


def _sonda(surf, t):
    ph = (t % 8) / 8
    r = 70 + ph * 70
    a = t * 1.1
    pos = (C[0] + math.cos(a) * r, C[1] + math.sin(a) * r * 0.6)
    for i in range(10):
        b = a - i * 0.09
        rr = 70 + max(0, ph - i * 0.006) * 70
        _glow(surf, (150, 200, 255), (C[0] + math.cos(b) * rr, C[1] + math.sin(b) * rr * 0.6), 3, 150 - i * 14)
    pygame.draw.circle(surf, (210, 220, 235), pos, 7)
    pygame.draw.line(surf, (210, 220, 235), pos, (pos[0] + 10, pos[1] - 10), 2)
    pygame.draw.circle(surf, (255, 200, 90), (int(pos[0] + 10), int(pos[1] - 10)), 3)
    # barra de energía que se agota
    pygame.draw.rect(surf, (40, 50, 80), (pos[0] - 14, pos[1] + 13, 28, 5))
    pygame.draw.rect(surf, (110, 230, 150) if ph < 0.6 else (240, 100, 110), (pos[0] - 14, pos[1] + 13, 28 * (1 - ph), 5))


def _ganimedes(surf, t):
    p0, p1 = (22, 430), (250, 92)
    for i in range(0, 20):  # trayectoria predicha
        if i % 2 == 0:
            q = _lerp(p0, p1, i / 20)
            _glow(surf, (150, 170, 255), q, 2, 120)
    ph = (t % 4.5) / 4.5
    head = _lerp(p0, p1, ph)
    for i in range(18):
        q = _lerp(p0, p1, max(0, ph - i * 0.012))
        _glow(surf, (140, 200, 255), (q[0] + 2 * math.sin(i + t * 9), q[1]), 9 - i * 0.45, 190 - i * 9)
    _glow(surf, (255, 255, 255), head, 8, 255)
    _glow(surf, (170, 220, 255), head, 14, 120)


def _baliza(surf, t):
    b = (62, 125)
    for i in range(3):
        k = ((t * 0.5 + i / 3) % 1)
        _glow(surf, (200, 150, 255), b, 8 + k * 120, 200 * (1 - k), width=2)
    pts = [(b[0], b[1] - 12), (b[0] + 9, b[1]), (b[0], b[1] + 12), (b[0] - 9, b[1])]
    pygame.draw.polygon(surf, (235, 190, 255) if int(t * 3) % 2 else (180, 120, 230), pts)
    rnd = random.Random(11)
    n = int((t * 2) % 9)
    for i in range(n):  # puntos de datos que aparecen
        x = 30 + i * 24
        y = 400 - i * 18 + rnd.uniform(-12, 12)
        _glow(surf, (235, 190, 255), (x, y), 4, 230)
    if n > 3:
        pygame.draw.line(surf, (200, 150, 255), (30, 400), (30 + (n - 1) * 24, 400 - (n - 1) * 18), 1)


SCENES = {"helios": _helios, "ares": _ares, "vesper": _vesper, "nereida": _nereida,
          "sonda": _sonda, "ganimedes": _ganimedes, "baliza": _baliza}
GLOW = {"helios": (110, 180, 255), "ares": (255, 120, 90), "vesper": (255, 210, 110), "nereida": (110, 150, 255),
        "sonda": (190, 230, 255), "ganimedes": (130, 190, 255), "baliza": (200, 130, 255)}


def draw_scene(surf, planet_id, t, planet_img, moon_img=None, shake=0.0, danger=False):
    """Dibuja el planeta con su escena animada. shake>0: sacudida (respuesta incorrecta)."""
    surf.set_clip(AREA)
    bob = math.sin(t * 1.6) * 4
    dx = math.sin(t * 60) * 7 * shake
    center = (C[0] + dx, C[1] + bob)
    gcol = (255, 70, 70) if danger else GLOW.get(planet_id, (120, 180, 255))
    pulse = 0.5 + 0.5 * math.sin(t * (7 if danger else 2))
    _glow(surf, gcol, center, 100 + 6 * pulse, 40 + 50 * pulse * (1.4 if danger else 0.6))
    if moon_img is not None:  # las lunas giran alrededor de su planeta
        a = t * 0.8
        mpos = (C[0] + math.cos(a) * 118, C[1] + math.sin(a) * 38)
        behind = math.sin(a) < 0
    if moon_img is not None and behind:
        surf.blit(moon_img, moon_img.get_rect(center=mpos))
    if planet_img is not None:
        surf.blit(planet_img, planet_img.get_rect(center=center))
    if moon_img is not None and not behind:
        surf.blit(moon_img, moon_img.get_rect(center=mpos))
    SCENES.get(planet_id, lambda s, tt: None)(surf, t)
    surf.set_clip(None)


def celebrate(surf, center, k, ok=True):
    """Anillos y chispas al terminar el problema (k de 0 a 1)."""
    col = (110, 230, 150) if ok else (240, 100, 110)
    for i in range(3):
        kk = max(0, min(1, k * 1.4 - i * 0.2))
        _glow(surf, col, center, 60 + kk * 220, 230 * (1 - kk), width=4)
    rnd = random.Random(5)
    for _ in range(26):
        ang, sp = rnd.uniform(0, 6.28), rnd.uniform(0.4, 1.0)
        p = (center[0] + math.cos(ang) * 260 * k * sp, center[1] + math.sin(ang) * 200 * k * sp)
        _glow(surf, (255, 235, 150) if ok else col, p, 4, 255 * (1 - k))
