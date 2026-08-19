"""Stretchy Cat Rap - a self-contained Pygame toy.

Drag the cat's head or back end, then let go and watch it spring back.
The program creates its own original hip-hop-style instrumental at runtime.
"""

import math
import os
import random
import struct
import tempfile
import wave

import pygame


WIDTH, HEIGHT = 1000, 650
FPS = 60
BG = (31, 22, 55)
CREAM = (255, 218, 151)
CREAM_DARK = (224, 164, 89)
INK = (48, 34, 55)
PINK = (244, 130, 161)
CYAN = (71, 226, 221)
WHITE = (250, 247, 255)
MENU_BUTTON = pygame.Rect(WIDTH - 170, 18, 130, 42)


def clamp(value, low, high):
    return max(low, min(high, value))


def make_rap_beat(filename, seconds=16, sample_rate=22050, bpm=96):
    """Create an original, looping drum-and-bass beat as a WAV file."""
    random.seed(60)
    total = int(seconds * sample_rate)
    audio = [0.0] * total
    beat = 60.0 / bpm

    def mix(start, duration, generator, volume=1.0):
        first = int(start * sample_rate)
        count = int(duration * sample_rate)
        for i in range(count):
            index = first + i
            if index >= total:
                break
            audio[index] += volume * generator(i / sample_rate, duration)

    def kick(t, duration):
        env = math.exp(-11 * t)
        phase = 2 * math.pi * (72 * t - 24 * t * t)
        return math.sin(phase) * env

    def snare(t, duration):
        env = math.exp(-14 * t)
        noise = random.uniform(-1, 1)
        tone = math.sin(2 * math.pi * 185 * t)
        return env * (0.78 * noise + 0.22 * tone)

    def hat(t, duration):
        return random.uniform(-1, 1) * math.exp(-55 * t)

    bass_notes = [55.0, 55.0, 65.41, 49.0, 55.0, 73.42, 65.41, 49.0]
    steps = int(seconds / (beat / 2))
    for step in range(steps):
        when = step * beat / 2
        if step % 2 == 0:
            mix(when, 0.22, kick, 0.95)
        if step % 4 in (2,):
            mix(when, 0.18, snare, 0.55)
        mix(when, 0.055, hat, 0.16 if step % 2 else 0.11)

        freq = bass_notes[(step // 2) % len(bass_notes)]

        def bass(t, duration, f=freq):
            env = min(1.0, t * 35) * math.exp(-2.7 * t)
            return (math.sin(2 * math.pi * f * t) +
                    0.28 * math.sin(2 * math.pi * f * 2 * t)) * env

        if step % 2 == 0:
            mix(when, beat * 0.78, bass, 0.30)

    peak = max(1.0, max(abs(v) for v in audio))
    pcm = bytearray()
    for value in audio:
        sample = int(clamp(value / peak, -1, 1) * 30000)
        pcm.extend(struct.pack("<h", sample))
    with wave.open(filename, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm)


def unit(vector):
    length = max(0.001, vector.length())
    return vector / length


def bezier(a, b, c, d, steps=24):
    points = []
    for i in range(steps + 1):
        t = i / steps
        p = (a * (1 - t) ** 3 + b * 3 * (1 - t) ** 2 * t +
             c * 3 * (1 - t) * t ** 2 + d * t ** 3)
        points.append((round(p.x), round(p.y)))
    return points


class StretchyCat:
    def __init__(self):
        self.rest_left = pygame.Vector2(340, 365)
        self.rest_right = pygame.Vector2(660, 365)
        self.left = self.rest_left.copy()
        self.right = self.rest_right.copy()
        self.left_velocity = pygame.Vector2()
        self.right_velocity = pygame.Vector2()
        self.dragging = None
        self.best_stretch = 1.0
        self.wobble = 0.0

    def begin_drag(self, mouse):
        mouse = pygame.Vector2(mouse)
        dl = mouse.distance_to(self.left)
        dr = mouse.distance_to(self.right)
        axis = self.right - self.left
        axis_len = max(1, axis.length())
        along = clamp((mouse - self.left).dot(axis) / (axis_len * axis_len), 0, 1)
        closest = self.left + axis * along
        if mouse.distance_to(closest) < 95 or min(dl, dr) < 110:
            self.dragging = "left" if dl < dr else "right"
            self.wobble = 1.0

    def update(self, dt, mouse):
        if self.dragging:
            target = pygame.Vector2(mouse)
            target.x = clamp(target.x, 80, WIDTH - 80)
            target.y = clamp(target.y, 150, HEIGHT - 115)
            if self.dragging == "left":
                self.left = target
                self.left_velocity.update(0, 0)
            else:
                self.right = target
                self.right_velocity.update(0, 0)
            self.best_stretch = max(self.best_stretch, self.stretch_ratio())
        else:
            # Damped springs make both ends bounce smoothly home.
            for point, velocity, home in (
                (self.left, self.left_velocity, self.rest_left),
                (self.right, self.right_velocity, self.rest_right),
            ):
                velocity += (home - point) * 30.0 * dt
                velocity *= 0.84 ** (dt * 60)
                point += velocity * dt
        self.wobble = max(0, self.wobble - dt * 2.5)

    def stretch_ratio(self):
        return self.left.distance_to(self.right) / self.rest_left.distance_to(self.rest_right)

    def end_drag(self):
        if self.dragging:
            moving = self.left if self.dragging == "left" else self.right
            home = self.rest_left if self.dragging == "left" else self.rest_right
            velocity = self.left_velocity if self.dragging == "left" else self.right_velocity
            velocity += (home - moving) * 2.5
        self.dragging = None

    def draw(self, screen, time_now):
        axis = self.right - self.left
        direction = unit(axis)
        normal = pygame.Vector2(-direction.y, direction.x)
        length = axis.length()
        stretch = self.stretch_ratio()
        body_width = int(clamp(116 / math.sqrt(max(0.6, stretch)), 70, 135))
        bounce = math.sin(time_now * 8) * 3 * self.wobble
        left = self.left + normal * bounce
        right = self.right - normal * bounce

        # Shadow
        shadow_y = max(left.y, right.y) + body_width * 0.62
        shadow_rect = pygame.Rect(0, 0, max(180, length * 0.92), 25)
        shadow_rect.center = ((left.x + right.x) / 2, shadow_y)
        pygame.draw.ellipse(screen, (18, 13, 34), shadow_rect)

        # Legs stretch with the body, but stay pleasingly cat-like.
        for fraction in (0.18, 0.82):
            hip = left.lerp(right, fraction) + normal * body_width * 0.16
            foot = hip + pygame.Vector2(direction.x * (fraction - .5) * 25,
                                        body_width * 0.82)
            pygame.draw.line(screen, CREAM_DARK, hip, foot, 23)
            pygame.draw.circle(screen, CREAM_DARK, foot, 16)

        # Capsule body
        pygame.draw.line(screen, CREAM, left, right, body_width)
        pygame.draw.circle(screen, CREAM, left, body_width // 2)
        pygame.draw.circle(screen, CREAM, right, body_width // 2)

        # Stripes follow the stretched axis.
        for fraction in (0.30, 0.47, 0.64):
            center = left.lerp(right, fraction)
            a = center - normal * body_width * 0.46
            b = center - normal * body_width * 0.15
            pygame.draw.line(screen, CREAM_DARK, a, b, max(7, body_width // 12))

        # Tail curls upward from the back end.
        tail_base = left - direction * body_width * 0.28
        points = bezier(
            tail_base,
            tail_base - direction * 90 + normal * 25,
            tail_base - direction * 105 - normal * 125,
            tail_base - direction * 35 - normal * 135,
        )
        pygame.draw.lines(screen, CREAM_DARK, False, points, 22)
        pygame.draw.lines(screen, CREAM, False, points[:-3], 13)

        # Head, ears and face at the right end.
        head = right + direction * body_width * 0.16
        ear_size = body_width * 0.42
        for sign in (-1, 1):
            ear_center = head + normal * sign * body_width * 0.33 - direction * body_width * 0.16
            tip = ear_center - direction * ear_size + normal * sign * ear_size * 0.35
            base1 = ear_center + direction * ear_size * .45 + normal * sign * ear_size * .40
            base2 = ear_center + direction * ear_size * .45 - normal * sign * ear_size * .22
            pygame.draw.polygon(screen, CREAM_DARK, [tip, base1, base2])
            inner = tip.lerp(ear_center, .45)
            pygame.draw.circle(screen, PINK, inner, max(4, int(body_width * .07)))
        pygame.draw.circle(screen, CREAM, head, int(body_width * 0.56))

        eye_forward = direction * body_width * .20
        for sign in (-1, 1):
            eye = head + eye_forward + normal * sign * body_width * .20
            pygame.draw.circle(screen, INK, eye, max(4, body_width // 18))
            pygame.draw.circle(screen, WHITE, eye - pygame.Vector2(2, 2), 2)
        nose = head + direction * body_width * .42
        pygame.draw.circle(screen, PINK, nose, max(5, body_width // 16))
        for sign in (-1, 1):
            whisker_start = nose + normal * sign * 3
            for spread in (-0.18, 0.12):
                whisker_end = whisker_start + direction * 42 + normal * sign * (13 + spread * 35)
                pygame.draw.line(screen, INK, whisker_start, whisker_end, 2)

        # Grab handles appear while hovering/dragging.
        if self.dragging:
            held = left if self.dragging == "left" else right
            pygame.draw.circle(screen, CYAN, held, body_width // 2 + 13, 4)


def draw_background(screen, t):
    screen.fill(BG)
    # Equalizer bars animate with the beat.
    for i in range(22):
        x = 18 + i * 46
        phase = t * 5 + i * 0.7
        height = 22 + (math.sin(phase) + 1) * 22
        color = (73, 48 + (i * 7) % 80, 112 + (i * 5) % 80)
        pygame.draw.rect(screen, color, (x, HEIGHT - height, 28, height), border_radius=7)
    for i in range(18):
        x = (i * 83 + t * (18 + i % 3 * 7)) % (WIDTH + 40) - 20
        y = 95 + (i * 71) % 420
        pygame.draw.circle(screen, (63, 43, 90), (int(x), y), 3 + i % 5)


def main():
    pygame.mixer.pre_init(22050, -16, 1, 512)
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Stretchy Cat Rap")
    clock = pygame.time.Clock()
    title_font = pygame.font.SysFont("arialrounded", 48, bold=True)
    font = pygame.font.SysFont("arial", 25, bold=True)
    small_font = pygame.font.SysFont("arial", 19)

    music_file = os.path.join(tempfile.gettempdir(), "stretchy_cat_original_rap.wav")
    try:
        make_rap_beat(music_file)
        pygame.mixer.music.load(music_file)
        pygame.mixer.music.set_volume(0.55)
        pygame.mixer.music.play(-1)
        music_on = True
    except (pygame.error, OSError):
        music_on = False

    cat = StretchyCat()
    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.04)
        now = pygame.time.get_ticks() / 1000.0
        mouse = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_m:
                    music_on = not music_on
                    pygame.mixer.music.set_volume(0.55 if music_on else 0.0)
                elif event.key == pygame.K_r:
                    cat = StretchyCat()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if MENU_BUTTON.collidepoint(event.pos):
                    running = False
                else:
                    cat.begin_drag(event.pos)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                cat.end_drag()

        cat.update(dt, mouse)
        draw_background(screen, now)

        title = title_font.render("STRETCHY CAT RAP", True, CYAN)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 62)))
        instruction = font.render("Grab either end • Pull • Release • BOING!", True, WHITE)
        screen.blit(instruction, instruction.get_rect(center=(WIDTH // 2, 112)))

        cat.draw(screen, now)

        stretch_text = font.render(f"STRETCH  {cat.stretch_ratio():.2f}x", True, PINK)
        best_text = small_font.render(f"Best: {cat.best_stretch:.2f}x", True, WHITE)
        screen.blit(stretch_text, (28, 24))
        screen.blit(best_text, (31, 56))
        music_text = small_font.render(f"[M] Music: {'ON' if music_on else 'OFF'}    [R] Reset    [Esc] Quit", True, WHITE)
        screen.blit(music_text, music_text.get_rect(bottomright=(WIDTH - 22, HEIGHT - 16)))

        menu_hover = MENU_BUTTON.collidepoint(mouse)
        menu_color = (127, 203, 255) if menu_hover else (100, 170, 245)
        pygame.draw.rect(screen, menu_color, MENU_BUTTON, border_radius=12)
        pygame.draw.rect(screen, WHITE, MENU_BUTTON, 2, border_radius=12)
        menu_label = small_font.render("MENU", True, INK)
        screen.blit(menu_label, menu_label.get_rect(center=MENU_BUTTON.center))

        # A tiny original rap chant, displayed rather than recorded vocals.
        lines = ["Pull that cat, let it snap!", "Long cat groove with a springy back!",
                 "Stretch to the left, stretch to the right!", "Feline flow all through the night!"]
        line = lines[int(now / 2) % len(lines)]
        lyric = small_font.render(line, True, CREAM)
        screen.blit(lyric, lyric.get_rect(center=(WIDTH // 2, HEIGHT - 58)))
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
