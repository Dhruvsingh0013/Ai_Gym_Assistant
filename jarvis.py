"""
╔══════════════════════════════════════════════════════════════════╗
║          J.A.R.V.I.S  —  ULTIMATE VOICE-REACTIVE HUD            ║
║          Built by: Dhruv Singh  |  AI Content Creator            ║
╚══════════════════════════════════════════════════════════════════╝

FEATURES:
  ★ Real-time microphone voice detection (PyAudio)
  ★ Voice amplitude drives particle explosions & ring pulsing
  ★ 3000+ particle system with physics (gravity, drag, trails)
  ★ Volumetric bloom glow on all elements
  ★ Waveform visualizer ring (voice waveform displayed on outer ring)
  ★ Plasma energy core that reacts to voice
  ★ Holographic scan lines & chromatic aberration flash on loud input
  ★ Neural network grid that pulses with voice
  ★ Floating data streams on the sides
  ★ Dynamic HUD with live microphone level bar

REQUIREMENTS:
    pip install pygame pyaudio numpy

RUN:
    python jarvis_ultimate.py

CONTROLS:
    ESC / Q  → Quit
    SPACE    → Toggle microphone (use keyboard simulation instead)
    M        → Mute mic (demo mode - auto oscillation)
"""

import pygame
import math
import random
import sys
import time
import threading
import numpy as np

# ── Try importing PyAudio (graceful fallback to demo mode) ───────────────────
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("[JARVIS] PyAudio not found → running in DEMO mode (simulated voice)")
    print("         Install with:  pip install pyaudio")

# ════════════════════════════════════════════════════════════════════════════
#  CONSTANTS & PALETTE
# ════════════════════════════════════════════════════════════════════════════
W, H   = 1280, 720
FPS    = 60
CX, CY = W // 2, H // 2

# Colour palette  (R, G, B)
C_BG        = (0,   4,  10)
C_CYAN      = (0,  230, 255)
C_CYAN2     = (0,  180, 220)
C_CYAN_DIM  = (0,   80, 110)
C_WHITE     = (255, 255, 255)
C_GOLD      = (255, 210,  60)
C_RED       = (255,  50,  50)
C_BLUE_DEEP = (10,   30,  80)
C_TEAL      = (0,  255, 200)

# Audio config
CHUNK       = 512
RATE        = 44100
CHANNELS    = 1

# ════════════════════════════════════════════════════════════════════════════
#  AUDIO ENGINE  (runs in separate thread)
# ════════════════════════════════════════════════════════════════════════════
class AudioEngine:
    def __init__(self):
        self.amplitude   = 0.0      # 0..1 smoothed
        self.raw_amp     = 0.0
        self.waveform    = np.zeros(128)   # for waveform ring
        self.running     = False
        self.muted       = not PYAUDIO_AVAILABLE
        self._demo_t     = 0.0
        self._thread     = None
        self._lock       = threading.Lock()

    def start(self):
        self.running = True
        if PYAUDIO_AVAILABLE and not self.muted:
            self._thread = threading.Thread(target=self._audio_loop, daemon=True)
            self._thread.start()

    def _audio_loop(self):
        pa = pyaudio.PyAudio()
        try:
            stream = pa.open(format=pyaudio.paInt16, channels=CHANNELS,
                             rate=RATE, input=True, frames_per_buffer=CHUNK)
            while self.running:
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                    samples /= 32768.0
                    rms = float(np.sqrt(np.mean(samples ** 2)))
                    with self._lock:
                        self.raw_amp = min(rms * 50.0, 1.0)
                        # downsample for waveform ring
                        step = max(1, len(samples) // 128)
                        self.waveform = samples[::step][:128]
                except Exception:
                    pass
            stream.stop_stream()
            stream.close()
        except Exception as e:
            print(f"[Audio] Error: {e} → switching to demo mode")
            self.muted = True
        finally:
            pa.terminate()

    def update(self, dt):
        if self.muted or not PYAUDIO_AVAILABLE:
            # Demo: simulate natural speech rhythm
            self._demo_t += dt
            base = 0.05
            speech = (
                0.3  * max(0, math.sin(self._demo_t * 3.7)) *
                max(0, math.sin(self._demo_t * 0.8))
            )
            burst  = 0.5 * max(0, math.sin(self._demo_t * 11.0)) * \
                     (1 if random.random() < 0.08 else 0)
            self.raw_amp = min(base + speech + burst, 1.0)
            # Fake waveform
            t = self._demo_t
            self.waveform = np.array([
                math.sin(t * 8 + i * 0.25) * self.raw_amp * 0.6 +
                math.sin(t * 17 + i * 0.5) * self.raw_amp * 0.3 +
                random.gauss(0, 0.02)
                for i in range(128)
            ])
        # Smooth amplitude
        alpha = 0.15
        self.amplitude = self.amplitude * (1 - alpha) + self.raw_amp * alpha
        # Peak hold
        self.amplitude = max(self.amplitude, self.raw_amp * 0.3)

    def stop(self):
        self.running = False

# ════════════════════════════════════════════════════════════════════════════
#  PARTICLE  (with trail & physics)
# ════════════════════════════════════════════════════════════════════════════
class Particle:
    __slots__ = ['x','y','vx','vy','life','max_life','size','color',
                 'trail','grav','drag','mode']

    def __init__(self, x, y, mode='burst'):
        self.x, self.y = float(x), float(y)
        self.mode = mode
        self.trail = []

        if mode == 'burst':
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1.5, 8.0)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed
            self.life     = random.randint(25, 70)
            self.max_life = self.life
            self.size     = random.uniform(1.5, 4.0)
            self.color    = random.choice([C_CYAN, C_WHITE, C_TEAL, C_GOLD])
            self.grav     = 0.08
            self.drag     = 0.97

        elif mode == 'orbit':
            angle = random.uniform(0, 2 * math.pi)
            r = random.uniform(50, 260)
            self.x = CX + math.cos(angle) * r
            self.y = CY + math.sin(angle) * r
            speed = random.uniform(0.5, 2.0)
            perp  = angle + math.pi / 2
            self.vx = math.cos(perp) * speed
            self.vy = math.sin(perp) * speed
            self.life     = random.randint(60, 180)
            self.max_life = self.life
            self.size     = random.uniform(1.0, 2.5)
            self.color    = C_CYAN2
            self.grav     = 0.0
            self.drag     = 0.99

        elif mode == 'stream':
            self.vx = random.uniform(-0.3, 0.3)
            self.vy = random.uniform(-3.0, -0.5)
            self.life     = random.randint(40, 100)
            self.max_life = self.life
            self.size     = random.uniform(1.0, 2.5)
            self.color    = C_CYAN_DIM
            self.grav     = -0.02
            self.drag     = 0.98

        elif mode == 'plasma':
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.3, 2.0)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed
            self.life     = random.randint(20, 50)
            self.max_life = self.life
            self.size     = random.uniform(2.0, 6.0)
            self.color    = random.choice([C_CYAN, C_WHITE, (100, 255, 255)])
            self.grav     = 0.0
            self.drag     = 0.93

    def update(self):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 8:
            self.trail.pop(0)
        self.vx *= self.drag
        self.vy *= self.drag
        self.vy += self.grav
        self.x  += self.vx
        self.y  += self.vy
        self.life -= 1

    def draw(self, surf):
        ratio = self.life / self.max_life
        # Trail
        for i, (tx, ty) in enumerate(self.trail):
            tr = i / len(self.trail)
            a  = int(80 * tr * ratio)
            s  = max(1, int(self.size * tr * 0.7))
            ts = pygame.Surface((s * 2 + 1, s * 2 + 1), pygame.SRCALPHA)
            pygame.draw.circle(ts, (*self.color, a), (s, s), s)
            surf.blit(ts, (int(tx) - s, int(ty) - s))
        # Core dot
        a = int(255 * ratio)
        s = max(1, int(self.size))
        ps = pygame.Surface((s * 4 + 1, s * 4 + 1), pygame.SRCALPHA)
        pygame.draw.circle(ps, (*self.color, min(a, 200)), (s * 2, s * 2), s * 2)
        pygame.draw.circle(ps, (*self.color, a),           (s * 2, s * 2), s)
        surf.blit(ps, (int(self.x) - s * 2, int(self.y) - s * 2))

# ════════════════════════════════════════════════════════════════════════════
#  GLOW UTILITIES
# ════════════════════════════════════════════════════════════════════════════
_glow_cache = {}

def glow_circle(surf, color, center, radius, width, layers=7):
    for i in range(layers, 0, -1):
        a = min(int(255 / layers * (layers - i + 1) * 0.55), 200)
        r = max(1, radius + i * 4)
        w = max(1, width + i * 3)
        gs = pygame.Surface((r * 2 + w * 2 + 4, r * 2 + w * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*color, a), (r + w + 2, r + w + 2), r, w)
        surf.blit(gs, (center[0] - r - w - 2, center[1] - r - w - 2))
    pygame.draw.circle(surf, (*color, 255), center, radius, width)

def glow_line(surf, color, p1, p2, width=2, layers=6):
    for i in range(layers, 0, -1):
        a = min(int(200 / layers * (layers - i + 1)), 180)
        gs = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.line(gs, (*color, a), p1, p2, width + i * 3)
        surf.blit(gs, (0, 0))
    pygame.draw.line(surf, color, p1, p2, width)

def glow_arc(surf, color, rect, a1, a2, width=3, layers=6):
    for i in range(layers, 0, -1):
        a = min(int(180 / layers * (layers - i + 1)), 160)
        ri = rect.inflate(i * 6, i * 6)
        gs = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.arc(gs, (*color, a), ri, a1, a2, width + i * 2)
        surf.blit(gs, (0, 0))
    pygame.draw.arc(surf, (*color, 230), rect, a1, a2, width)

def draw_text_glow(surf, text, font, color, center, layers=6):
    rendered = font.render(text, True, color)
    rx, ry   = rendered.get_size()
    bx, by   = center[0] - rx // 2, center[1] - ry // 2
    gs = pygame.Surface((W, H), pygame.SRCALPHA)
    for i in range(layers, 0, -1):
        a = min(int(180 / layers * (layers - i + 1)), 200)
        for dx, dy in [(-i,0),(i,0),(0,-i),(0,i),(-i,-i),(i,i),(-i,i),(i,-i)]:
            g = font.render(text, True, (*color, a))
            gs.blit(g, (bx + dx, by + dy))
    gs.blit(rendered, (bx, by))
    surf.blit(gs, (0, 0))

# ════════════════════════════════════════════════════════════════════════════
#  NEURAL GRID  (background hex-dot grid that pulses with voice)
# ════════════════════════════════════════════════════════════════════════════
class NeuralGrid:
    def __init__(self):
        self.nodes = []
        spacing = 60
        for gx in range(0, W + spacing, spacing):
            for gy in range(0, H + spacing, spacing):
                if math.dist((gx, gy), (CX, CY)) < 310:
                    continue
                self.nodes.append([gx, gy, random.uniform(0, 2 * math.pi)])

    def draw(self, surf, amp, t):
        gs = pygame.Surface((W, H), pygame.SRCALPHA)
        for node in self.nodes:
            nx, ny, phase = node
            node[2] += 0.02
            pulse = 0.3 + 0.7 * amp * abs(math.sin(t * 3 + phase))
            a = int(20 + 35 * pulse)
            r = max(1, int(1.5 + 2.5 * pulse))
            pygame.draw.circle(gs, (*C_CYAN_DIM, a), (nx, ny), r)
        surf.blit(gs, (0, 0))

# ════════════════════════════════════════════════════════════════════════════
#  WAVEFORM RING  (voice waveform displayed on a ring)
# ════════════════════════════════════════════════════════════════════════════
def draw_waveform_ring(surf, cx, cy, radius, waveform, amp, color=C_CYAN):
    n = len(waveform)
    gs = pygame.Surface((W, H), pygame.SRCALPHA)
    prev = None
    for i in range(n):
        angle = (2 * math.pi * i / n) - math.pi / 2
        wave_val = float(waveform[i]) * amp * 60
        r = radius + wave_val
        r = max(radius - 30, min(radius + 60, r))
        x = int(cx + math.cos(angle) * r)
        y = int(cy + math.sin(angle) * r)
        if prev:
            a = int(150 + 105 * abs(float(waveform[i])) * amp)
            pygame.draw.line(gs, (*color, min(a, 255)), prev, (x, y), 2)
        prev = (x, y)
    surf.blit(gs, (0, 0))

# ════════════════════════════════════════════════════════════════════════════
#  PLASMA CORE
# ════════════════════════════════════════════════════════════════════════════
def draw_plasma_core(surf, cx, cy, amp, t):
    max_r = int(35 + amp * 30)
    gs = pygame.Surface((W, H), pygame.SRCALPHA)
    for r in range(max_r, 0, -4):
        ratio = r / max_r
        a = int((1 - ratio) * 200 * (0.6 + 0.4 * amp))
        color_lerp = (
            int(C_CYAN[0] * (1 - ratio) + C_WHITE[0] * ratio),
            int(C_CYAN[1] * (1 - ratio) + C_WHITE[1] * ratio),
            int(C_CYAN[2] * (1 - ratio) + C_WHITE[2] * ratio),
        )
        # Wobble
        wobble_x = int(math.sin(t * 5.3 + r * 0.2) * amp * 8)
        wobble_y = int(math.cos(t * 4.7 + r * 0.3) * amp * 8)
        pygame.draw.circle(gs, (*color_lerp, a),
                           (cx + wobble_x, cy + wobble_y), r)
    surf.blit(gs, (0, 0))

# ════════════════════════════════════════════════════════════════════════════
#  DATA STREAMS  (left & right side floating data columns)
# ════════════════════════════════════════════════════════════════════════════
class DataStream:
    def __init__(self, x):
        self.x   = x
        self.chars = [chr(random.randint(0x30A0, 0x30FF)) for _ in range(20)]
        self.y_offsets = [random.uniform(0, H) for _ in range(20)]
        self.speeds    = [random.uniform(0.5, 2.5) for _ in range(20)]

    def update(self, amp):
        for i in range(len(self.y_offsets)):
            self.y_offsets[i] += self.speeds[i] * (1 + amp * 3)
            if self.y_offsets[i] > H:
                self.y_offsets[i] = -20
                self.chars[i] = chr(random.randint(0x30A0, 0x30FF))

    def draw(self, surf, font, amp):
        gs = pygame.Surface((W, H), pygame.SRCALPHA)
        for i, (y, ch) in enumerate(zip(self.y_offsets, self.chars)):
            a = int(60 + 80 * amp)
            color = C_CYAN if i % 3 == 0 else C_CYAN_DIM
            txt = font.render(ch, True, (*color, min(a, 200)))
            gs.blit(txt, (self.x, int(y)))
        surf.blit(gs, (0, 0))

# ════════════════════════════════════════════════════════════════════════════
#  RING CONFIG
# ════════════════════════════════════════════════════════════════════════════
RINGS = [
    {"r": 270, "spd":  0.4, "ticks": 90,  "w": 3, "gap": 0.5, "col": C_CYAN},
    {"r": 230, "spd": -0.7, "ticks": 60,  "w": 2, "gap": 0.4, "col": C_CYAN2},
    {"r": 190, "spd":  1.1, "ticks": 48,  "w": 3, "gap": 0.6, "col": C_CYAN},
    {"r": 155, "spd": -0.9, "ticks": 36,  "w": 2, "gap": 0.3, "col": C_TEAL},
    {"r": 118, "spd":  1.6, "ticks": 24,  "w": 3, "gap": 0.4, "col": C_CYAN},
    {"r":  80, "spd": -2.0, "ticks": 16,  "w": 2, "gap": 0.2, "col": C_CYAN2},
    {"r":  45, "spd":  3.0, "ticks":  8,  "w": 2, "gap": 0.15,"col": C_GOLD},
]

# ════════════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H), pygame.DOUBLEBUF | pygame.HWSURFACE)
    pygame.display.set_caption("J.A.R.V.I.S — Voice Reactive HUD  |  Dhruv Singh")
    clock = pygame.time.Clock()

    # ── Fonts ────────────────────────────────────────────────────────────────
    try:
        font_title  = pygame.font.SysFont("Consolas",  50, bold=True)
        font_sub    = pygame.font.SysFont("Consolas",  18)
        font_small  = pygame.font.SysFont("Consolas",  14)
        font_matrix = pygame.font.SysFont("Consolas",  16)
        font_hud    = pygame.font.SysFont("Consolas",  13)
    except Exception:
        font_title  = pygame.font.SysFont(None, 52, bold=True)
        font_sub    = pygame.font.SysFont(None, 20)
        font_small  = pygame.font.SysFont(None, 16)
        font_matrix = pygame.font.SysFont(None, 18)
        font_hud    = pygame.font.SysFont(None, 15)

    # ── Systems ──────────────────────────────────────────────────────────────
    audio  = AudioEngine()
    audio.start()

    grid   = NeuralGrid()
    stream_L = [DataStream(random.choice([20, 50, 80]))   for _ in range(3)]
    stream_R = [DataStream(random.choice([W-40, W-70, W-100])) for _ in range(3)]

    ring_angles = [0.0] * len(RINGS)
    particles   = []

    # ── State ────────────────────────────────────────────────────────────────
    t           = 0.0
    frame       = 0
    prev_amp    = 0.0
    chromatic   = 0.0          # chromatic aberration intensity on loud sounds
    shockwave_r = 0.0          # expanding shockwave circle
    shockwave_a = 0            # alpha
    boot_phase  = 0.0          # 0→1 boot reveal
    status_idx  = 0
    status_timer= 0.0

    STATUS_LINES = [
        "BOOTING NEURAL CORE...",
        "VOICE RECOGNITION: ACTIVE",
        "PARTICLE ENGINE: ONLINE",
        "HOLOGRAPHIC MATRIX: READY",
        "ALL SYSTEMS: NOMINAL",
        "LISTENING...",
    ]

    # Peak bar history for VU meter
    vu_history  = [0.0] * 40

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        t += dt
        frame += 1

        # ── Events ───────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                if event.key == pygame.K_m:
                    audio.muted = not audio.muted
                    if not audio.muted and PYAUDIO_AVAILABLE:
                        audio.start()

        # ── Audio update ─────────────────────────────────────────────────────
        audio.update(dt)
        amp       = audio.amplitude
        waveform  = audio.waveform.copy()
        vu_history.pop(0)
        vu_history.append(amp)

        # Boot reveal
        boot_phase = min(1.0, boot_phase + dt * 0.4)

        # Status cycling
        status_timer += dt
        if status_timer > 1.8:
            status_timer = 0
            status_idx = (status_idx + 1) % len(STATUS_LINES)

        # ── Detect voice spikes → shockwave + burst particles ────────────────
        spike = amp - prev_amp
        if spike > 0.12:
            shockwave_r = 30.0
            shockwave_a = 220
            burst_n = int(spike * 200)
            for _ in range(min(burst_n, 120)):
                particles.append(Particle(CX, CY, 'burst'))
        prev_amp = amp

        # Continuous particles
        if amp > 0.05:
            for _ in range(int(amp * 18)):
                r = random.choice(RINGS)
                angle = random.uniform(0, 2 * math.pi)
                px = CX + math.cos(angle) * r["r"]
                py = CY + math.sin(angle) * r["r"]
                particles.append(Particle(px, py, 'burst'))

        # Orbit particles always
        if len(particles) < 400 and random.random() < 0.4:
            particles.append(Particle(CX, CY, 'orbit'))

        # Plasma particles from core
        if amp > 0.03 and random.random() < amp * 0.6:
            particles.append(Particle(CX, CY, 'plasma'))

        # Cap particles
        if len(particles) > 1800:
            particles = particles[-1800:]

        # Chromatic aberration — fades fast
        if spike > 0.15:
            chromatic = 1.0
        chromatic = max(0, chromatic - dt * 4.0)

        # Shockwave expand
        if shockwave_r > 0:
            shockwave_r += dt * 500
            shockwave_a  = max(0, shockwave_a - int(dt * 600))
            if shockwave_r > 700:
                shockwave_r = 0

        # ── Ring rotation ─────────────────────────────────────────────────────
        for i, ring in enumerate(RINGS):
            speed_boost = 1.0 + amp * 5.0
            ring_angles[i] += math.radians(ring["spd"] * speed_boost)

        # ── UPDATE PARTICLES ─────────────────────────────────────────────────
        for p in particles[:]:
            p.update()
            if p.life <= 0:
                particles.remove(p)

        # ── DATA STREAMS UPDATE ───────────────────────────────────────────────
        for ds in stream_L + stream_R:
            ds.update(amp)

        # ════════════════════════════════════════════════════════════════════
        #  DRAW
        # ════════════════════════════════════════════════════════════════════
        screen.fill(C_BG)

        # ── 1. Neural grid background ─────────────────────────────────────────
        grid.draw(screen, amp, t)

        # ── 2. Scan lines overlay (CRT effect) ───────────────────────────────
        scan_surf = pygame.Surface((W, H), pygame.SRCALPHA)
        for sy in range(0, H, 4):
            pygame.draw.line(scan_surf, (0, 0, 0, 25), (0, sy), (W, sy), 1)
        screen.blit(scan_surf, (0, 0))

        # ── 3. Data streams ───────────────────────────────────────────────────
        for ds in stream_L:
            ds.draw(screen, font_matrix, amp)
        for ds in stream_R:
            ds.draw(screen, font_matrix, amp)

        # ── 4. Particles (behind rings) ───────────────────────────────────────
        p_surf = pygame.Surface((W, H), pygame.SRCALPHA)
        for p in particles:
            p.draw(p_surf)
        screen.blit(p_surf, (0, 0))

        # ── 5. WAVEFORM RING (outermost) ──────────────────────────────────────
        draw_waveform_ring(screen, CX, CY, 295, waveform, amp)

        # ── 6. HUD RINGS ─────────────────────────────────────────────────────
        for i, ring in enumerate(RINGS):
            reveal = min(1.0, boot_phase * 2.0 - i * 0.15)
            if reveal <= 0:
                continue

            r_base = ring["r"]
            pulse  = 1.0 + amp * 0.12 * math.sin(t * 8 + i)
            r = int(r_base * pulse)

            col = ring["col"]
            a   = ring_angles[i]

            # Full ring glow
            glow_circle(screen, col, (CX, CY), r, ring["w"],
                        layers=int(4 + amp * 5))

            # Accent bright arc
            arc_span  = math.pi * ring["gap"] * (1 + amp * 0.5)
            arc_rect  = pygame.Rect(CX - r, CY - r, r * 2, r * 2)
            bright_col = C_WHITE if amp > 0.3 else col
            glow_arc(screen, bright_col, arc_rect, a, a + arc_span,
                     width=ring["w"] + 2, layers=4)

            # Tick marks
            tick_surf = pygame.Surface((W, H), pygame.SRCALPHA)
            n_ticks   = ring["ticks"]
            for ti in range(n_ticks):
                angle   = a + (2 * math.pi / n_ticks) * ti
                tick_len = 12 if ti % 6 == 0 else (7 if ti % 3 == 0 else 4)
                ox, oy  = math.cos(angle), math.sin(angle)
                sx = int(CX + (r - tick_len) * ox)
                sy = int(CY + (r - tick_len) * oy)
                ex = int(CX + r * ox)
                ey = int(CY + r * oy)
                ta = int(180 * reveal + 75 * amp)
                tc = C_WHITE if ti % 6 == 0 else col
                pygame.draw.line(tick_surf, (*tc, min(ta, 255)), (sx, sy), (ex, ey),
                                 2 if ti % 6 == 0 else 1)
            screen.blit(tick_surf, (0, 0))

        # ── 7. Plasma energy core ─────────────────────────────────────────────
        draw_plasma_core(screen, CX, CY, amp, t)

        # ── 8. J.A.R.V.I.S title ──────────────────────────────────────────────
        title_alpha = int(255 * min(1.0, (boot_phase - 0.5) * 2))
        if title_alpha > 0:
            title_col  = C_WHITE if amp > 0.5 else C_CYAN
            ts = pygame.Surface((W, H), pygame.SRCALPHA)
            txt = font_title.render("J.A.R.V.I.S", True, (*title_col, title_alpha))
            ts.blit(txt, (CX - txt.get_width() // 2, CY - txt.get_height() // 2))
            screen.blit(ts, (0, 0))
            # Glow
            if amp > 0.05:
                draw_text_glow(screen, "J.A.R.V.I.S", font_title, title_col,
                               (CX, CY), layers=int(3 + amp * 8))

        # ── 9. Subtitle / status ──────────────────────────────────────────────
        if boot_phase > 0.7:
            ba = int(255 * min(1.0, (boot_phase - 0.7) * 3.3))
            ss = pygame.Surface((W, H), pygame.SRCALPHA)
            st = font_sub.render(STATUS_LINES[status_idx], True, (*C_CYAN_DIM, ba))
            ss.blit(st, (CX - st.get_width() // 2, CY + 285))
            screen.blit(ss, (0, 0))

        # ── 10. Shockwave ring ────────────────────────────────────────────────
        if shockwave_r > 0 and shockwave_a > 0:
            sw_surf = pygame.Surface((W, H), pygame.SRCALPHA)
            sw_r = int(shockwave_r)
            for layer in range(5, 0, -1):
                a = max(0, int(shockwave_a * layer / 5))
                pygame.draw.circle(sw_surf, (*C_WHITE, a),
                                   (CX, CY), min(sw_r + layer * 4, 700),
                                   max(1, 3 - layer))
            screen.blit(sw_surf, (0, 0))

        # ── 11. Chromatic aberration flash ────────────────────────────────────
        if chromatic > 0.01:
            ca_surf = pygame.Surface((W, H), pygame.SRCALPHA)
            ca_int  = int(chromatic * 30)
            ca_a    = int(chromatic * 80)
            txt_ca  = font_title.render("J.A.R.V.I.S", True, (255, 0, 0, ca_a))
            ca_surf.blit(txt_ca, (CX - txt_ca.get_width() // 2 + ca_int,
                                  CY - txt_ca.get_height() // 2))
            txt_ca2 = font_title.render("J.A.R.V.I.S", True, (0, 0, 255, ca_a))
            ca_surf.blit(txt_ca2, (CX - txt_ca2.get_width() // 2 - ca_int,
                                   CY - txt_ca2.get_height() // 2))
            screen.blit(ca_surf, (0, 0))

        # ── 12. HUD overlays ──────────────────────────────────────────────────
        hud = pygame.Surface((W, H), pygame.SRCALPHA)
        ha  = int(200 * boot_phase)

        # Corner brackets
        corners = [(18, 18, 1, 1), (W-18, 18, -1, 1),
                   (18, H-18, 1, -1), (W-18, H-18, -1, -1)]
        for bx, by, dx, dy in corners:
            for ln in [((bx, by), (bx + dx*50, by)),
                       ((bx, by), (bx, by + dy*50)),
                       ((bx + dx*50, by), (bx + dx*42, by)),
                       ((bx, by + dy*50), (bx, by + dy*42))]:
                pygame.draw.line(hud, (*C_CYAN, ha), ln[0], ln[1], 2)

        # System readout (top-left)
        sys_lines = [
            f"SYSTEM  ── ONLINE",
            f"AI CORE ── ACTIVE",
            f"VOICE   ── {'DETECTED' if amp > 0.1 else 'STANDBY'}",
            f"AMP     ── {amp*100:05.1f}%",
            f"PTCL    ── {len(particles):04d}",
            f"UPTIME  ── {int(t):05d}s",
        ]
        for idx_l, line in enumerate(sys_lines):
            col_l = C_GOLD if (idx_l == 2 and amp > 0.1) else C_CYAN_DIM
            sl = font_hud.render(line, True, (*col_l, ha))
            hud.blit(sl, (30, 28 + idx_l * 19))

        # Microphone VU meter (bottom-left)
        vu_label = font_hud.render("MIC INPUT", True, (*C_CYAN_DIM, ha))
        hud.blit(vu_label, (30, H - 90))
        for vi, vv in enumerate(vu_history):
            bar_h = int(vv * 40)
            bar_col = C_GOLD if vv > 0.7 else (C_CYAN if vv > 0.3 else C_CYAN2)
            pygame.draw.rect(hud, (*bar_col, ha),
                             (30 + vi * 7, H - 50 - bar_h, 5, bar_h))
        pygame.draw.rect(hud, (*C_CYAN_DIM, ha // 2), (30, H - 50, 280, 1))

        # Top centre: coordinates / targeting reticle text
        coord_txt = font_hud.render(
            f"LAT 28.6139°N  LON 77.2090°E  ALT 0216m", True, (*C_CYAN_DIM, ha))
        hud.blit(coord_txt, (CX - coord_txt.get_width() // 2, 20))

        # Bottom-right: build tag
        tag = font_hud.render("BUILD v7.4.2  |  DHRUV SINGH  |  AI SYSTEMS", True,
                               (*C_CYAN_DIM, ha))
        hud.blit(tag, (W - tag.get_width() - 25, H - 25))

        # Horizontal divider lines
        pygame.draw.line(hud, (*C_CYAN_DIM, ha // 2), (0, 1),   (W, 1),   1)
        pygame.draw.line(hud, (*C_CYAN_DIM, ha // 2), (0, H-1), (W, H-1), 1)

        screen.blit(hud, (0, 0))

        # ── 13. "VOICE ACTIVE" flash ──────────────────────────────────────────
        if amp > 0.45:
            flash_a = int((amp - 0.45) / 0.55 * 60)
            flash = pygame.Surface((W, H), pygame.SRCALPHA)
            flash.fill((*C_CYAN, flash_a))
            screen.blit(flash, (0, 0))

        pygame.display.flip()

    audio.stop()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
