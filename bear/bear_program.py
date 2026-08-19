import pygame
import math
import random
import array

pygame.init()

# ============================================================
# SOUND
# ============================================================

# Thunder stays silent, but an original rap beat plays in the background.
sound_enabled = False
music_enabled = True

try:
    pygame.mixer.quit()
    pygame.mixer.init(
        frequency=44100,
        size=-16,
        channels=1,
        buffer=512
    )
except pygame.error:
    music_enabled = False


# ============================================================
# WINDOW
# ============================================================

WIDTH = 1000
HEIGHT = 700

screen = pygame.display.set_mode(
    (WIDTH, HEIGHT)
)

pygame.display.set_caption(
    "Cursor Bear - Thunder Escape"
)

clock = pygame.time.Clock()


# ============================================================
# COLORS
# ============================================================

SKY_NORMAL = (155, 210, 240)
SKY_STORM = (90, 105, 135)

GRASS = (105, 180, 100)
DARK_GRASS = (60, 135, 65)

WHITE = (255, 255, 255)
BLACK = (20, 20, 25)

YELLOW = (255, 240, 90)
ORANGE = (255, 170, 50)
RED = (235, 70, 55)


# ============================================================
# FONTS
# ============================================================

font_huge = pygame.font.SysFont(
    None,
    90,
    bold=True
)

font_big = pygame.font.SysFont(
    None,
    55,
    bold=True
)

font_medium = pygame.font.SysFont(
    None,
    36,
    bold=True
)

font_small = pygame.font.SysFont(
    None,
    25
)

font_day = pygame.font.SysFont(
    None,
    23,
    bold=True
)

font_today = pygame.font.SysFont(
    None,
    16,
    bold=True
)


# ============================================================
# DAY-OF-WEEK CHART
# ============================================================

DAYS_OF_WEEK = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]

# Each weekday stays highlighted for this many seconds.
DAY_DURATION = 6.0

FRIDAY_INDEX = 4

active_day_index = 0
previous_day_index = -1

DAY_CHART_RECT = pygame.Rect(
    20,
    15,
    WIDTH - 40,
    58
)


def draw_day_chart(day_index):

    chart = pygame.Surface(
        DAY_CHART_RECT.size,
        pygame.SRCALPHA
    )

    pygame.draw.rect(
        chart,
        (25, 35, 55, 190),
        chart.get_rect(),
        border_radius=16
    )

    gap = 6
    padding = 8
    card_width = (
        DAY_CHART_RECT.width
        - padding * 2
        - gap * 6
    ) // 7

    for index, day in enumerate(DAYS_OF_WEEK):

        card = pygame.Rect(
            padding + index * (card_width + gap),
            7,
            card_width,
            44
        )

        is_active_day = index == day_index

        if is_active_day:
            card_color = (255, 215, 75, 245)
            text_color = BLACK
        else:
            card_color = (235, 242, 250, 215)
            text_color = (35, 45, 65)

        pygame.draw.rect(
            chart,
            card_color,
            card,
            border_radius=10
        )

        day_text = font_day.render(
            day,
            True,
            text_color
        )

        day_y = card.centery

        if is_active_day:
            day_y -= 7

        chart.blit(
            day_text,
            day_text.get_rect(
                center=(card.centerx, day_y)
            )
        )

        if is_active_day:
            today_text = font_today.render(
                "FRIDAY!" if index == FRIDAY_INDEX else "CURRENT DAY",
                True,
                (120, 75, 10)
            )

            chart.blit(
                today_text,
                today_text.get_rect(
                    center=(card.centerx, card.bottom - 9)
                )
            )

    screen.blit(
        chart,
        DAY_CHART_RECT.topleft
    )


# ============================================================
# LOAD BEAR
# ============================================================

bear_image = pygame.image.load(
    "bear.jpg"
).convert_alpha()

BEAR_WIDTH = 165

scale = (
    BEAR_WIDTH
    / bear_image.get_width()
)

BEAR_HEIGHT = int(
    bear_image.get_height()
    * scale
)

bear_image = pygame.transform.smoothscale(
    bear_image,
    (
        BEAR_WIDTH,
        BEAR_HEIGHT
    )
)


# ============================================================
# BEAR PHYSICS
# ============================================================

CURSOR_PULL = 10.0

# Fast/heavy gravity
GRAVITY = 1600.0

AIR_RESISTANCE = 0.985

MAX_SPEED = 1000

GROUND_Y = 625

GROUND_FRICTION = 0.86

BOUNCE = 0.18

FOLLOW_DISTANCE = 35


# ============================================================
# LIGHTNING AVOIDANCE
# ============================================================

DANGER_RADIUS = 250

DANGER_FORCE = 6000

EMERGENCY_FORCE = 9500


# ============================================================
# KEYBOARD-CONTROLLED WIND
# ============================================================

WIND_FORCE = 2400

wind_active = False
wind_vector = pygame.Vector2(0, 0)


def draw_wind(time_now):

    if not wind_active:
        return

    wind_layer = pygame.Surface(
        (WIDTH, HEIGHT),
        pygame.SRCALPHA
    )

    # Fast-moving streaks follow the keyboard-controlled wind.
    for index in range(18):

        x = (
            index * 157
            + time_now * 430 * wind_vector.x
        ) % (WIDTH + 200) - 100

        y = (
            index * 83
            + time_now * 430 * wind_vector.y
        ) % (HEIGHT + 200) - 100

        line_length = 45 + (index % 4) * 12

        pygame.draw.line(
            wind_layer,
            (235, 250, 255, 155),
            (int(x), int(y)),
            (
                int(x - wind_vector.x * line_length),
                int(y - wind_vector.y * line_length)
            ),
            4
        )

    screen.blit(wind_layer, (0, 0))

    direction_words = []

    if wind_vector.y < 0:
        direction_words.append("UP")
    elif wind_vector.y > 0:
        direction_words.append("DOWN")

    if wind_vector.x < 0:
        direction_words.append("LEFT")
    elif wind_vector.x > 0:
        direction_words.append("RIGHT")

    direction_word = " + ".join(direction_words)

    indicator = font_medium.render(
        "WIND " + direction_word,
        True,
        WHITE
    )

    indicator_box = indicator.get_rect(
        topleft=(24, 86)
    ).inflate(24, 14)

    label_layer = pygame.Surface(
        (indicator_box.width, indicator_box.height),
        pygame.SRCALPHA
    )

    pygame.draw.rect(
        label_layer,
        (35, 85, 120, 210),
        label_layer.get_rect(),
        border_radius=12
    )

    screen.blit(label_layer, indicator_box.topleft)
    screen.blit(indicator, indicator.get_rect(center=indicator_box.center))


# ============================================================
# EARTHQUAKES
# ============================================================

EARTHQUAKE_DURATION = 2.3
EARTHQUAKE_MIN_WAIT = 8.0
EARTHQUAKE_MAX_WAIT = 14.0

earthquake_active = False
earthquake_timer = 5.0
earthquake_elapsed = 0.0
earthquake_offset = pygame.Vector2(0, 0)
earthquake_cursor_anchor = pygame.Vector2(0, 0)
earthquake_last_cursor = pygame.Vector2(0, 0)


def draw_earthquake_warning():

    if not earthquake_active:
        return

    warning_text = font_medium.render(
        "EARTHQUAKE!",
        True,
        WHITE
    )

    warning_box = warning_text.get_rect(
        topright=(WIDTH - 24, 86)
    ).inflate(24, 14)

    warning_layer = pygame.Surface(
        warning_box.size,
        pygame.SRCALPHA
    )

    pygame.draw.rect(
        warning_layer,
        (185, 75, 40, 225),
        warning_layer.get_rect(),
        border_radius=12
    )

    pygame.draw.rect(
        warning_layer,
        (255, 190, 90, 245),
        warning_layer.get_rect(),
        3,
        border_radius=12
    )

    screen.blit(warning_layer, warning_box.topleft)
    screen.blit(
        warning_text,
        warning_text.get_rect(center=warning_box.center)
    )


# ============================================================
# CREATE THUNDER SOUND
# ============================================================

def make_thunder_sound():

    if not sound_enabled:
        return None

    sample_rate = 44100

    duration = 1.8

    samples = []

    for i in range(
        int(sample_rate * duration)
    ):

        t = i / sample_rate

        envelope = math.exp(
            -t * 2.2
        )

        low_rumble = math.sin(
            2 * math.pi * 45 * t
        )

        second_rumble = (
            0.5
            * math.sin(
                2 * math.pi * 72 * t
            )
        )

        noise = random.uniform(
            -1,
            1
        )

        value = (
            low_rumble * 0.50
            + second_rumble * 0.25
            + noise * 0.25
        )

        value *= envelope

        value = max(
            -1,
            min(1, value)
        )

        samples.append(
            int(value * 15000)
        )

    sound_data = array.array(
        "h",
        samples
    )

    return pygame.mixer.Sound(
        buffer=sound_data
    )


thunder_sound = make_thunder_sound()


# ============================================================
# ORIGINAL RAP-STYLE BACKGROUND BEAT
# ============================================================

def make_rap_music():

    if not music_enabled:
        return None

    sample_rate = 44100
    duration = 4.0
    music_random = random.Random(77)
    samples = []

    bass_notes = [
        55.0,
        55.0,
        65.4,
        55.0,
        73.4,
        65.4,
        55.0,
        49.0
    ]

    for i in range(int(sample_rate * duration)):

        t = i / sample_rate
        beat_index = int(t / 0.5) % 8
        beat_phase = t % 0.5

        kick = 0.0

        if beat_index in (0, 3, 4, 6):
            kick_envelope = math.exp(-beat_phase * 20)
            kick_frequency = 78 - beat_phase * 55
            kick = (
                math.sin(
                    2 * math.pi * kick_frequency * beat_phase
                )
                * kick_envelope
                * 0.62
            )

        snare = 0.0

        if beat_index in (2, 6):
            snare_envelope = math.exp(-beat_phase * 24)
            snare = (
                music_random.uniform(-1, 1)
                * snare_envelope
                * 0.28
            )

        hat_phase = t % 0.25
        hi_hat = (
            music_random.uniform(-1, 1)
            * math.exp(-hat_phase * 55)
            * 0.10
        )

        bass_frequency = bass_notes[beat_index]
        bass = (
            math.sin(2 * math.pi * bass_frequency * t)
            * 0.18
        )

        value = kick + snare + hi_hat + bass
        value = max(-1, min(1, value))
        samples.append(int(value * 14500))

    return pygame.mixer.Sound(
        buffer=array.array("h", samples)
    )


rap_music = make_rap_music()

if rap_music:
    rap_music.set_volume(0.48)
    rap_music.play(loops=-1)


# ============================================================
# CLOUDS
# ============================================================

clouds = [

    {
        "x": 150.0,
        "y": 105,
        "speed": 14,
        "scale": 1.35,
        "storm": True
    },

    {
        "x": 500.0,
        "y": 80,
        "speed": 8,
        "scale": 1.0,
        "storm": False
    },

    {
        "x": 780.0,
        "y": 150,
        "speed": 11,
        "scale": 0.85,
        "storm": False
    }
]


# The first cloud creates the thunder
THUNDER_CLOUD = 0


# ============================================================
# FLOWERS
# ============================================================

random.seed(10)

flowers = []

for i in range(35):

    flowers.append(
        {
            "x": random.randint(
                20,
                WIDTH - 20
            ),

            "y": random.randint(
                530,
                HEIGHT - 15
            ),

            "height": random.randint(
                18,
                38
            ),

            "phase":
                random.random()
                * math.pi
                * 2
        }
    )


# ============================================================
# POND
# ============================================================

pond_rect = pygame.Rect(
    650,
    455,
    280,
    130
)

ripples = []

last_ripple_time = 0


# ============================================================
# THUNDER / LIGHTNING SETTINGS
# ============================================================

# States:
#
# waiting
# warning
# striking
# finished

thunder_state = "waiting"

thunder_timer = 3.0

target_x = WIDTH // 2

lightning_path = []

strike_elapsed = 0


# ------------------------------------------------------------
# HOW LONG THE WARNING LASTS
# ------------------------------------------------------------

WARNING_TIME = 2.5


# ------------------------------------------------------------
# THIS CONTROLS HOW SLOW THE LIGHTNING MOVES
#
# Bigger number = slower lightning
# ------------------------------------------------------------

LIGHTNING_TRAVEL_TIME = 1.50


# Lightning remains visible briefly
LIGHTNING_HOLD_TIME = 0.35


# How often thunder happens
THUNDER_MIN_WAIT = 3.0
THUNDER_MAX_WAIT = 6.0


# ============================================================
# SCREEN FLASH
# ============================================================

flash_alpha = 0


# ============================================================
# GAME STATE
# ============================================================

game_over = False
game_won = False


# ============================================================
# DRAW CLOUD
# ============================================================

def draw_cloud(surface, cloud):

    x = cloud["x"]
    y = cloud["y"]
    scale = cloud["scale"]

    if cloud["storm"]:

        color = (
            60,
            65,
            82
        )

    else:

        color = (
            235,
            240,
            245
        )

    pygame.draw.circle(
        surface,
        color,
        (
            int(x),
            int(y)
        ),
        int(
            30 * scale
        )
    )

    pygame.draw.circle(
        surface,
        color,
        (
            int(
                x + 35 * scale
            ),
            int(
                y - 10 * scale
            )
        ),
        int(
            38 * scale
        )
    )

    pygame.draw.circle(
        surface,
        color,
        (
            int(
                x + 75 * scale
            ),
            int(y)
        ),
        int(
            31 * scale
        )
    )

    pygame.draw.ellipse(
        surface,
        color,
        (
            int(
                x - 20 * scale
            ),
            int(y),

            int(
                125 * scale
            ),

            int(
                45 * scale
            )
        )
    )


# ============================================================
# GET BOTTOM CENTER OF STORM CLOUD
# ============================================================

def get_cloud_lightning_start():

    cloud = clouds[
        THUNDER_CLOUD
    ]

    start_x = (
        cloud["x"]
        + 38 * cloud["scale"]
    )

    start_y = (
        cloud["y"]
        + 35 * cloud["scale"]
    )

    return pygame.Vector2(
        start_x,
        start_y
    )


# ============================================================
# CREATE LIGHTNING PATH
# ============================================================

def create_lightning_path():

    global lightning_path

    start = (
        get_cloud_lightning_start()
    )

    lightning_path = []

    steps = 14

    for step in range(
        steps + 1
    ):

        progress = (
            step / steps
        )

        # Move smoothly toward target
        x = (
            start.x
            + (
                target_x
                - start.x
            )
            * progress
        )

        y = (
            start.y
            + (
                GROUND_Y
                - start.y
            )
            * progress
        )

        # Give lightning zig-zag shape
        if (
            step != 0
            and
            step != steps
        ):

            x += random.randint(
                -25,
                25
            )

        lightning_path.append(
            pygame.Vector2(
                x,
                y
            )
        )


# ============================================================
# WARNING IMAGE
# ============================================================

def draw_thunder_warning():

    warning = pygame.Surface(
        (
            520,
            125
        ),
        pygame.SRCALPHA
    )

    pygame.draw.rect(
        warning,
        (
            25,
            28,
            40,
            235
        ),
        (
            0,
            0,
            520,
            125
        ),
        border_radius=24
    )

    pygame.draw.rect(
        warning,
        YELLOW,
        (
            0,
            0,
            520,
            125
        ),
        5,
        border_radius=24
    )


    # --------------------------------------------------------
    # LIGHTNING ICON
    # --------------------------------------------------------

    bolt = [

        (50, 12),

        (25, 65),

        (55, 65),

        (35, 112),

        (95, 50),

        (62, 50)
    ]

    pygame.draw.polygon(
        warning,
        YELLOW,
        bolt
    )


    # --------------------------------------------------------
    # TEXT
    # --------------------------------------------------------

    text = font_big.render(
        "THUNDER IS COMING!",
        True,
        WHITE
    )

    text_rect = text.get_rect(
        center=(
            315,
            48
        )
    )

    warning.blit(
        text,
        text_rect
    )


    smaller = font_small.render(
        "Move the bear away from the warning zone!",
        True,
        (
            220,
            225,
            235
        )
    )

    smaller_rect = smaller.get_rect(
        center=(
            305,
            91
        )
    )

    warning.blit(
        smaller,
        smaller_rect
    )


    screen.blit(
        warning,
        (
            WIDTH // 2 - 260,
            200
        )
    )


# ============================================================
# WARNING TARGET ON GROUND
# ============================================================

def draw_target_warning(time_now):

    pulse = (
        math.sin(
            time_now * 12
        )
        + 1
    ) / 2

    radius = int(
        55
        + pulse * 15
    )

    surface = pygame.Surface(
        (
            WIDTH,
            HEIGHT
        ),
        pygame.SRCALPHA
    )


    # Large transparent danger zone
    pygame.draw.circle(
        surface,
        (
            255,
            70,
            40,
            45
        ),
        (
            int(target_x),
            GROUND_Y
        ),
        DANGER_RADIUS
    )


    # Actual impact target
    pygame.draw.ellipse(
        surface,
        (
            255,
            80,
            40,
            90
        ),
        (
            target_x
            - radius,

            GROUND_Y
            - 18,

            radius * 2,

            36
        )
    )


    pygame.draw.ellipse(
        surface,
        YELLOW,
        (
            target_x
            - radius,

            GROUND_Y
            - 18,

            radius * 2,

            36
        ),
        5
    )


    screen.blit(
        surface,
        (
            0,
            0
        )
    )


# ============================================================
# LIGHTNING PROGRESS
# ============================================================

def lightning_progress():

    if thunder_state != "striking":
        return 0

    return min(
        1.0,
        strike_elapsed
        / LIGHTNING_TRAVEL_TIME
    )


# ============================================================
# GET CURRENT VISIBLE LIGHTNING SEGMENTS
# ============================================================

def get_visible_segments():

    if thunder_state != "striking":
        return []

    progress = lightning_progress()

    total_segments = (
        len(lightning_path)
        - 1
    )

    exact_segments = (
        total_segments
        * progress
    )

    full_segments = int(
        exact_segments
    )

    partial_amount = (
        exact_segments
        - full_segments
    )

    visible = []


    # --------------------------------------------------------
    # COMPLETELY VISIBLE SEGMENTS
    # --------------------------------------------------------

    for i in range(
        min(
            full_segments,
            total_segments
        )
    ):

        visible.append(
            (
                lightning_path[i],
                lightning_path[i + 1]
            )
        )


    # --------------------------------------------------------
    # PARTIAL LAST SEGMENT
    # --------------------------------------------------------

    if (
        full_segments
        < total_segments
    ):

        start = lightning_path[
            full_segments
        ]

        end = lightning_path[
            full_segments + 1
        ]

        partial_end = (
            start
            + (
                end - start
            )
            * partial_amount
        )

        visible.append(
            (
                start,
                partial_end
            )
        )


    return visible


# ============================================================
# DRAW LIGHTNING
# ============================================================

def draw_lightning():

    segments = (
        get_visible_segments()
    )

    for start, end in segments:

        # Blue glow
        pygame.draw.line(
            screen,
            (
                150,
                180,
                255
            ),
            start,
            end,
            14
        )

        # Bright white
        pygame.draw.line(
            screen,
            WHITE,
            start,
            end,
            7
        )

        # Yellow center
        pygame.draw.line(
            screen,
            YELLOW,
            start,
            end,
            3
        )


    # --------------------------------------------------------
    # GROUND IMPACT
    # --------------------------------------------------------

    if lightning_progress() >= 1:

        pygame.draw.circle(
            screen,
            (
                255,
                245,
                170
            ),
            (
                int(target_x),
                GROUND_Y
            ),
            35
        )


# ============================================================
# COLLISION CHECK
# ============================================================

def lightning_hits_bear(
    bear_hitbox
):

    if thunder_state != "striking":

        return False

    segments = (
        get_visible_segments()
    )

    for start, end in segments:

        # pygame Rect.clipline determines whether
        # the lightning segment crosses the bear.
        if bear_hitbox.clipline(
            (
                int(start.x),
                int(start.y)
            ),
            (
                int(end.x),
                int(end.y)
            )
        ):

            return True

    return False


# ============================================================
# GAME OVER IMAGE
# ============================================================

def create_game_over_image():

    image = pygame.Surface(
        (
            560,
            290
        ),
        pygame.SRCALPHA
    )

    pygame.draw.rect(
        image,
        (
            20,
            22,
            32,
            245
        ),
        (
            0,
            0,
            560,
            290
        ),
        border_radius=30
    )

    pygame.draw.rect(
        image,
        RED,
        (
            0,
            0,
            560,
            290
        ),
        6,
        border_radius=30
    )


    # --------------------------------------------------------
    # LIGHTNING IMAGE
    # --------------------------------------------------------

    bolt = [

        (70, 35),

        (35, 125),

        (80, 125),

        (50, 240),

        (145, 105),

        (95, 105)
    ]

    pygame.draw.polygon(
        image,
        YELLOW,
        bolt
    )


    # --------------------------------------------------------
    # GAME OVER
    # --------------------------------------------------------

    title = font_huge.render(
        "GAME OVER",
        True,
        WHITE
    )

    title_rect = title.get_rect(
        center=(
            355,
            105
        )
    )

    image.blit(
        title,
        title_rect
    )


    message = font_medium.render(
        "The bear was hit!",
        True,
        (
            230,
            230,
            235
        )
    )

    message_rect = message.get_rect(
        center=(
            355,
            180
        )
    )

    image.blit(
        message,
        message_rect
    )


    message2 = font_small.render(
        "Try again and escape the thunder.",
        True,
        (
            190,
            195,
            210
        )
    )

    message2_rect = (
        message2.get_rect(
            center=(
                355,
                225
            )
        )
    )

    image.blit(
        message2,
        message2_rect
    )

    return image


game_over_image = (
    create_game_over_image()
)


# ============================================================
# YOU-WIN IMAGE WITH HAPPY FACE
# ============================================================

def create_win_image():

    image = pygame.Surface(
        (600, 330),
        pygame.SRCALPHA
    )

    pygame.draw.rect(
        image,
        (24, 105, 70, 245),
        image.get_rect(),
        border_radius=30
    )

    pygame.draw.rect(
        image,
        (120, 255, 150),
        image.get_rect(),
        6,
        border_radius=30
    )

    # Large happy face
    face_center = (120, 165)

    pygame.draw.circle(
        image,
        (255, 225, 70),
        face_center,
        82
    )

    pygame.draw.circle(
        image,
        BLACK,
        (92, 140),
        9
    )

    pygame.draw.circle(
        image,
        BLACK,
        (148, 140),
        9
    )

    pygame.draw.lines(
        image,
        BLACK,
        False,
        [
            (78, 170),
            (90, 185),
            (105, 195),
            (120, 199),
            (135, 195),
            (150, 185),
            (162, 170)
        ],
        8
    )

    title = font_huge.render(
        "YOU WIN!",
        True,
        WHITE
    )

    image.blit(
        title,
        title.get_rect(center=(400, 105))
    )

    message = font_medium.render(
        "The bear reached Sunday!",
        True,
        (225, 255, 230)
    )

    image.blit(
        message,
        message.get_rect(center=(400, 190))
    )

    smaller = font_small.render(
        "You escaped Friday's thunder!",
        True,
        (195, 240, 205)
    )

    image.blit(
        smaller,
        smaller.get_rect(center=(400, 235))
    )

    return image


win_image = create_win_image()


# ============================================================
# MENU / RESTART BUTTONS
# ============================================================

menu_button = pygame.Rect(
    WIDTH - 180,
    18,
    150,
    42
)

restart_button = pygame.Rect(
    WIDTH // 2 - 120,
    530,
    240,
    70
)


# ============================================================
# RESET GAME
# ============================================================

def reset_game():

    global bear_pos
    global bear_velocity

    global thunder_state
    global thunder_timer

    global strike_elapsed
    global target_x

    global lightning_path

    global flash_alpha

    global game_over
    global game_won

    global active_day_index
    global previous_day_index
    global game_start_time

    global wind_active
    global wind_vector

    global earthquake_active
    global earthquake_timer
    global earthquake_elapsed
    global earthquake_offset
    global earthquake_last_cursor


    bear_pos = pygame.Vector2(
        WIDTH / 2,
        300
    )

    bear_velocity = pygame.Vector2(
        0,
        0
    )


    thunder_state = "waiting"

    thunder_timer = random.uniform(
        2.5,
        4.0
    )

    strike_elapsed = 0

    target_x = (
        WIDTH // 2
    )

    lightning_path = []


    flash_alpha = 0

    game_over = False
    game_won = False

    active_day_index = 0
    previous_day_index = -1
    game_start_time = (
        pygame.time.get_ticks()
        / 1000.0
    )

    wind_active = False
    wind_vector.update(0, 0)

    earthquake_active = False
    earthquake_timer = 5.0
    earthquake_elapsed = 0.0
    earthquake_offset.update(0, 0)
    earthquake_last_cursor.update(0, 0)

    ripples.clear()


# ============================================================
# INITIAL BEAR
# ============================================================

bear_pos = pygame.Vector2(
    WIDTH / 2,
    300
)

bear_velocity = pygame.Vector2(
    0,
    0
)

game_start_time = (
    pygame.time.get_ticks()
    / 1000.0
)


# ============================================================
# MAIN LOOP
# ============================================================

running = True

while running:

    dt = (
        clock.tick(60)
        / 1000.0
    )

    dt = min(
        dt,
        0.033
    )

    time_now = (
        pygame.time.get_ticks()
        / 1000.0
    )

    mouse = pygame.Vector2(
        pygame.mouse.get_pos()
    )


    # ========================================================
    # EVENTS
    # ========================================================

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            running = False

        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and menu_button.collidepoint(event.pos)
        ):
            running = False

        # Escape always closes the program, even during an
        # earthquake or on the game-over screen.
        if (
            event.type == pygame.KEYDOWN
            and
            event.key == pygame.K_ESCAPE
        ):

            running = False


        # ----------------------------------------------------
        # GAME OVER CONTROLS
        # ----------------------------------------------------

        if game_over or game_won:

            if (
                event.type
                == pygame.MOUSEBUTTONDOWN
            ):

                if restart_button.collidepoint(
                    event.pos
                ):

                    reset_game()


            if (
                event.type
                == pygame.KEYDOWN
            ):

                if event.key == pygame.K_r:

                    reset_game()


        # ----------------------------------------------------
        # NORMAL GAME
        # ----------------------------------------------------

        else:

            if (
                event.type
                == pygame.MOUSEBUTTONDOWN
            ):

                if pond_rect.collidepoint(
                    event.pos
                ):

                    ripples.append(
                        {
                            "x":
                                event.pos[0],

                            "y":
                                event.pos[1],

                            "radius": 5,

                            "life": 1.0
                        }
                    )


    # ========================================================
    # UPDATE GAME
    # ========================================================

    if not game_over and not game_won:


        # ====================================================
        # EARTHQUAKE: WIGGLE THE BEAR AND MOUSE CURSOR
        # ====================================================

        if earthquake_active:

            earthquake_elapsed += dt

            # Preserve the player's real mouse movement instead
            # of forcing the cursor back to one fixed point.
            user_mouse_movement = (
                mouse - earthquake_last_cursor
            )

            earthquake_cursor_anchor += (
                user_mouse_movement
            )

            earthquake_cursor_anchor.x = max(
                0,
                min(WIDTH - 1, earthquake_cursor_anchor.x)
            )

            earthquake_cursor_anchor.y = max(
                0,
                min(HEIGHT - 1, earthquake_cursor_anchor.y)
            )

            earthquake_offset.update(
                math.sin(earthquake_elapsed * 49) * 11,
                math.sin(earthquake_elapsed * 67) * 7
            )

            cursor_shake = pygame.Vector2(
                math.sin(earthquake_elapsed * 58) * 9,
                math.cos(earthquake_elapsed * 71) * 7
            )

            shaken_cursor = (
                earthquake_cursor_anchor
                + cursor_shake
            )

            shaken_cursor.x = max(
                0,
                min(WIDTH - 1, shaken_cursor.x)
            )

            shaken_cursor.y = max(
                0,
                min(HEIGHT - 1, shaken_cursor.y)
            )

            # Do not warp the cursor near a window edge. This lets
            # the player move out of the game and click Close.
            cursor_near_edge = (
                earthquake_cursor_anchor.x < 25
                or earthquake_cursor_anchor.x > WIDTH - 25
                or earthquake_cursor_anchor.y < 25
                or earthquake_cursor_anchor.y > HEIGHT - 25
            )

            if cursor_near_edge:

                earthquake_last_cursor.update(
                    mouse.x,
                    mouse.y
                )

            else:

                pygame.mouse.set_pos(
                    (
                        int(shaken_cursor.x),
                        int(shaken_cursor.y)
                    )
                )

                earthquake_last_cursor.update(
                    int(shaken_cursor.x),
                    int(shaken_cursor.y)
                )

                mouse = shaken_cursor

            if earthquake_elapsed >= EARTHQUAKE_DURATION:

                earthquake_active = False
                earthquake_timer = random.uniform(
                    EARTHQUAKE_MIN_WAIT,
                    EARTHQUAKE_MAX_WAIT
                )
                earthquake_offset.update(0, 0)

                pygame.mouse.set_pos(
                    (
                        int(earthquake_cursor_anchor.x),
                        int(earthquake_cursor_anchor.y)
                    )
                )

                mouse = earthquake_cursor_anchor.copy()
                earthquake_last_cursor.update(
                    mouse.x,
                    mouse.y
                )

        else:

            earthquake_timer -= dt

            if earthquake_timer <= 0:

                earthquake_active = True
                earthquake_elapsed = 0.0
                earthquake_cursor_anchor.update(
                    mouse.x,
                    mouse.y
                )
                earthquake_last_cursor.update(
                    mouse.x,
                    mouse.y
                )


        # ====================================================
        # LOOP THROUGH MONDAY TO SUNDAY
        # ====================================================

        active_day_index = int(
            (time_now - game_start_time)
            / DAY_DURATION
        ) % len(DAYS_OF_WEEK)

        if active_day_index != previous_day_index:

            # Stop and clear thunder whenever the day changes.
            thunder_state = "waiting"
            strike_elapsed = 0
            lightning_path = []
            flash_alpha = 0

            # Friday starts with a short pause, then thunder.
            if active_day_index == FRIDAY_INDEX:
                thunder_timer = 0.8

            # Reaching Sunday safely wins the game.
            if active_day_index == 6:
                game_won = True
                wind_active = False
                earthquake_active = False
                earthquake_offset.update(0, 0)

            previous_day_index = active_day_index


        # ====================================================
        # MOVE CLOUDS
        # ====================================================

        for cloud in clouds:

            cloud["x"] += (
                cloud["speed"]
                * dt
            )

            if (
                cloud["x"]
                > WIDTH + 160
            ):

                cloud["x"] = -160


        # ====================================================
        # ARROW KEYS CONTROL THE WIND
        # ====================================================

        keys = pygame.key.get_pressed()

        wind_vector.update(
            int(keys[pygame.K_RIGHT])
            - int(keys[pygame.K_LEFT]),

            int(keys[pygame.K_DOWN])
            - int(keys[pygame.K_UP])
        )

        wind_active = (
            wind_vector.length_squared() > 0
        )

        if wind_active:

            # Diagonal wind has the same overall strength.
            wind_vector.normalize_ip()

            # Wind pushes the bear horizontally or vertically.
            bear_velocity += (
                wind_vector
                * WIND_FORCE
                * dt
            )


        # ====================================================
        # THUNDER STATE MACHINE
        # ====================================================

        if (
            active_day_index == FRIDAY_INDEX
            and
            thunder_state == "waiting"
        ):

            thunder_timer -= dt

            if thunder_timer <= 0:

                # Choose where thunder will land
                target_x = random.randint(
                    90,
                    WIDTH - 90
                )

                thunder_state = "warning"

                thunder_timer = (
                    WARNING_TIME
                )


        elif thunder_state == "warning":

            thunder_timer -= dt

            if thunder_timer <= 0:

                # Create path using CURRENT cloud location
                create_lightning_path()

                strike_elapsed = 0

                thunder_state = "striking"

                flash_alpha = 100


                if (
                    sound_enabled
                    and
                    thunder_sound
                ):

                    thunder_sound.play()


        elif thunder_state == "striking":

            strike_elapsed += dt


            # Wait until bolt finishes,
            # plus short pause.
            if (
                strike_elapsed
                >
                LIGHTNING_TRAVEL_TIME
                +
                LIGHTNING_HOLD_TIME
            ):

                thunder_state = "waiting"

                thunder_timer = (
                    random.uniform(
                        THUNDER_MIN_WAIT,
                        THUNDER_MAX_WAIT
                    )
                )


        # ====================================================
        # CURSOR PULL
        # ====================================================

        direction = (
            mouse
            - bear_pos
        )

        distance = (
            direction.length()
        )

        if (
            distance
            > FOLLOW_DISTANCE
        ):

            bear_velocity += (
                direction
                * CURSOR_PULL
                * dt
            )


        # ====================================================
        # BEAR AVOIDS THUNDER
        # ====================================================

        if thunder_state in (
            "warning",
            "striking"
        ):

            difference = (
                bear_pos.x
                - target_x
            )

            danger_distance = abs(
                difference
            )

            if (
                danger_distance
                < DANGER_RADIUS
            ):

                if difference < 0:

                    escape_direction = -1

                else:

                    escape_direction = 1


                if abs(difference) < 4:

                    escape_direction = (
                        random.choice(
                            [-1, 1]
                        )
                    )


                danger_strength = (
                    1
                    - danger_distance
                    / DANGER_RADIUS
                )


                if thunder_state == "warning":

                    force = (
                        DANGER_FORCE
                        * danger_strength
                    )

                else:

                    force = (
                        EMERGENCY_FORCE
                        * danger_strength
                    )


                bear_velocity.x += (
                    escape_direction
                    * force
                    * dt
                )


        # ====================================================
        # GRAVITY
        # ====================================================

        bear_velocity.y += (
            GRAVITY
            * dt
        )


        # ====================================================
        # AIR RESISTANCE
        # ====================================================

        bear_velocity *= (
            AIR_RESISTANCE
        )


        # ====================================================
        # SPEED LIMIT
        # ====================================================

        if (
            bear_velocity.length()
            > MAX_SPEED
        ):

            bear_velocity.scale_to_length(
                MAX_SPEED
            )


        # ====================================================
        # MOVE BEAR
        # ====================================================

        bear_pos += (
            bear_velocity
            * dt
        )


        # ====================================================
        # GROUND COLLISION
        # ====================================================

        bear_bottom = (
            bear_pos.y
            + BEAR_HEIGHT / 2
        )

        on_ground = False

        if bear_bottom >= GROUND_Y:

            on_ground = True

            bear_pos.y = (
                GROUND_Y
                - BEAR_HEIGHT / 2
            )


            if (
                bear_velocity.y
                > 120
            ):

                bear_velocity.y *= (
                    -BOUNCE
                )

            else:

                bear_velocity.y = 0


            bear_velocity.x *= (
                GROUND_FRICTION
            )


        # ====================================================
        # LEFT WALL
        # ====================================================

        if (
            bear_pos.x
            - BEAR_WIDTH / 2
            < 0
        ):

            bear_pos.x = (
                BEAR_WIDTH / 2
            )

            bear_velocity.x *= (
                -0.25
            )


        # ====================================================
        # RIGHT WALL
        # ====================================================

        if (
            bear_pos.x
            + BEAR_WIDTH / 2
            > WIDTH
        ):

            bear_pos.x = (
                WIDTH
                - BEAR_WIDTH / 2
            )

            bear_velocity.x *= (
                -0.25
            )


        # ====================================================
        # TOP
        # ====================================================

        if (
            bear_pos.y
            - BEAR_HEIGHT / 2
            < 0
        ):

            bear_pos.y = (
                BEAR_HEIGHT / 2
            )

            if bear_velocity.y < 0:

                bear_velocity.y *= (
                    -0.25
                )


        # ====================================================
        # WALKING BOB
        # ====================================================

        walking_bob = 0

        if (
            on_ground
            and
            abs(
                bear_velocity.x
            )
            > 50
        ):

            walking_bob = (
                math.sin(
                    time_now * 12
                )
                * 3
            )


        # ====================================================
        # POND RIPPLE
        # ====================================================

        if pond_rect.collidepoint(
            mouse.x,
            mouse.y
        ):

            if (
                time_now
                - last_ripple_time
                > 0.15
            ):

                ripples.append(
                    {
                        "x": mouse.x,
                        "y": mouse.y,
                        "radius": 3,
                        "life": 1.0
                    }
                )

                last_ripple_time = (
                    time_now
                )


        for ripple in ripples:

            ripple["radius"] += (
                45 * dt
            )

            ripple["life"] -= (
                0.8 * dt
            )


        ripples = [
            r
            for r in ripples
            if r["life"] > 0
        ]


        # ====================================================
        # BEAR HITBOX
        # ====================================================

        bear_hitbox = pygame.Rect(
            0,
            0,

            int(
                BEAR_WIDTH
                * 0.55
            ),

            int(
                BEAR_HEIGHT
                * 0.70
            )
        )

        bear_hitbox.center = (
            int(bear_pos.x),
            int(bear_pos.y)
        )


        # ====================================================
        # CHECK THUNDER COLLISION
        # ====================================================

        if lightning_hits_bear(
            bear_hitbox
        ):

            game_over = True

            flash_alpha = 255


    else:

        walking_bob = 0


    # ========================================================
    # FADE FLASH
    # ========================================================

    if flash_alpha > 0:

        flash_alpha -= (
            350 * dt
        )

        flash_alpha = max(
            0,
            flash_alpha
        )


    # ========================================================
    # DRAW SKY
    # ========================================================

    if thunder_state in (
        "warning",
        "striking"
    ):

        screen.fill(
            SKY_STORM
        )

    else:

        screen.fill(
            SKY_NORMAL
        )


    # ========================================================
    # SUN
    # ========================================================

    pygame.draw.circle(
        screen,
        (
            255,
            235,
            150
        ),
        (
            865,
            90
        ),
        45
    )


    # ========================================================
    # CLOUDS
    # ========================================================

    for cloud in clouds:

        draw_cloud(
            screen,
            cloud
        )


    # ========================================================
    # HILLS
    # ========================================================

    pygame.draw.ellipse(
        screen,
        (
            105,
            170,
            105
        ),
        (
            -160,
            300,
            760,
            400
        )
    )

    pygame.draw.ellipse(
        screen,
        (
            85,
            155,
            90
        ),
        (
            280,
            300,
            870,
            430
        )
    )


    # ========================================================
    # GRASS
    # ========================================================

    pygame.draw.rect(
        screen,
        GRASS,
        (
            0,
            430,
            WIDTH,
            HEIGHT - 430
        )
    )


    # ========================================================
    # GRASS BLADES
    # ========================================================

    for x in range(
        0,
        WIDTH,
        13
    ):

        wind_strength = 5

        if thunder_state in (
            "warning",
            "striking"
        ):

            wind_strength = 11


        wind = (
            math.sin(
                time_now * 3
                + x * 0.05
            )
            * wind_strength
        )


        if (
            abs(
                mouse.x - x
            )
            < 120
        ):

            wind += (
                mouse.x - x
            ) * 0.04


        pygame.draw.line(
            screen,
            DARK_GRASS,
            (
                x,
                525
            ),
            (
                x + wind,
                505
            ),
            2
        )


    # ========================================================
    # POND
    # ========================================================

    pygame.draw.ellipse(
        screen,
        (
            90,
            180,
            215
        ),
        pond_rect
    )

    pygame.draw.ellipse(
        screen,
        (
            170,
            225,
            240
        ),
        pond_rect,
        4
    )


    # ========================================================
    # POND RIPPLES
    # ========================================================

    for ripple in ripples:

        alpha = max(
            0,
            min(
                255,
                int(
                    ripple["life"]
                    * 255
                )
            )
        )

        ripple_layer = pygame.Surface(
            (
                WIDTH,
                HEIGHT
            ),
            pygame.SRCALPHA
        )

        pygame.draw.ellipse(
            ripple_layer,
            (
                230,
                250,
                255,
                alpha
            ),
            (
                ripple["x"]
                - ripple["radius"],

                ripple["y"]
                - ripple["radius"] / 3,

                ripple["radius"] * 2,

                ripple["radius"] * 0.65
            ),
            2
        )

        screen.blit(
            ripple_layer,
            (
                0,
                0
            )
        )


    # ========================================================
    # FLOWERS
    # ========================================================

    for flower in flowers:

        x = flower["x"]
        y = flower["y"]

        sway_speed = 2.5
        sway_amount = 4

        if thunder_state in (
            "warning",
            "striking"
        ):

            sway_speed = 5
            sway_amount = 8


        sway = (
            math.sin(
                time_now
                * sway_speed
                + flower["phase"]
            )
            * sway_amount
        )


        top_x = x + sway

        top_y = (
            y
            - flower["height"]
        )


        pygame.draw.line(
            screen,
            DARK_GRASS,
            (
                x,
                y
            ),
            (
                top_x,
                top_y
            ),
            3
        )


        pygame.draw.circle(
            screen,
            (
                255,
                180,
                210
            ),
            (
                int(top_x - 5),
                int(top_y)
            ),
            5
        )

        pygame.draw.circle(
            screen,
            (
                255,
                180,
                210
            ),
            (
                int(top_x + 5),
                int(top_y)
            ),
            5
        )

        pygame.draw.circle(
            screen,
            (
                255,
                180,
                210
            ),
            (
                int(top_x),
                int(top_y - 5)
            ),
            5
        )

        pygame.draw.circle(
            screen,
            YELLOW,
            (
                int(top_x),
                int(top_y)
            ),
            4
        )


    # ========================================================
    # DAY-OF-WEEK CHART
    # ========================================================

    draw_day_chart(
        active_day_index
    )


    # ========================================================
    # VISIBLE WIND
    # ========================================================

    draw_wind(time_now)

    draw_earthquake_warning()


    # ========================================================
    # WARNING
    # ========================================================

    if thunder_state == "warning":

        draw_target_warning(
            time_now
        )

        draw_thunder_warning()


    # ========================================================
    # BEAR SHADOW
    # ========================================================

    distance_from_ground = max(
        0,

        GROUND_Y
        - (
            bear_pos.y
            + BEAR_HEIGHT / 2
        )
    )

    shadow_width = max(
        25,

        90
        - distance_from_ground
        * 0.15
    )


    shadow = pygame.Surface(
        (
            140,
            35
        ),
        pygame.SRCALPHA
    )

    pygame.draw.ellipse(
        shadow,
        (
            0,
            0,
            0,
            55
        ),
        (
            70
            - shadow_width / 2,

            7,

            shadow_width,

            18
        )
    )

    screen.blit(
        shadow,
        (
            bear_pos.x - 70,
            GROUND_Y - 5
        )
    )


    # ========================================================
    # DRAW BEAR
    # ========================================================

    bear_rect = (
        bear_image.get_rect(
            center=(
                int(
                    bear_pos.x
                    + earthquake_offset.x
                ),

                int(
                    bear_pos.y
                    + walking_bob
                    + earthquake_offset.y
                )
            )
        )
    )

    screen.blit(
        bear_image,
        bear_rect
    )


    # ========================================================
    # DRAW SLOW LIGHTNING
    #
    # IMPORTANT:
    # This is drawn AFTER the bear so you can clearly
    # see the lightning pass over the bear if it gets hit.
    # ========================================================

    if thunder_state == "striking":

        draw_lightning()


    # ========================================================
    # SCREEN FLASH
    # ========================================================

    if flash_alpha > 0:

        flash = pygame.Surface(
            (
                WIDTH,
                HEIGHT
            ),
            pygame.SRCALPHA
        )

        flash.fill(
            (
                255,
                255,
                255,
                int(
                    flash_alpha
                )
            )
        )

        screen.blit(
            flash,
            (
                0,
                0
            )
        )


    menu_hover = menu_button.collidepoint(pygame.mouse.get_pos())
    menu_color = (150, 210, 255) if menu_hover else (100, 170, 245)
    pygame.draw.rect(screen, menu_color, menu_button, border_radius=12)
    pygame.draw.rect(screen, (255, 255, 255), menu_button, 2, border_radius=12)
    menu_text = font_small.render("MENU", True, BLACK)
    screen.blit(menu_text, menu_text.get_rect(center=menu_button.center))

    # ========================================================
    # GAME OVER SCREEN
    # ========================================================

    if game_over:

        # Darken background
        overlay = pygame.Surface(
            (
                WIDTH,
                HEIGHT
            ),
            pygame.SRCALPHA
        )

        overlay.fill(
            (
                0,
                0,
                0,
                145
            )
        )

        screen.blit(
            overlay,
            (
                0,
                0
            )
        )


        # ----------------------------------------------------
        # GAME OVER IMAGE
        # ----------------------------------------------------

        image_rect = (
            game_over_image.get_rect(
                center=(
                    WIDTH // 2,
                    325
                )
            )
        )

        screen.blit(
            game_over_image,
            image_rect
        )


        # ----------------------------------------------------
        # RESTART BUTTON
        # ----------------------------------------------------

        mouse_pos = pygame.mouse.get_pos()

        hovering = (
            restart_button.collidepoint(
                mouse_pos
            )
        )


        if hovering:

            button_color = (
                255,
                220,
                80
            )

        else:

            button_color = (
                245,
                190,
                60
            )


        pygame.draw.rect(
            screen,
            button_color,
            restart_button,
            border_radius=18
        )

        pygame.draw.rect(
            screen,
            (
                255,
                245,
                190
            ),
            restart_button,
            4,
            border_radius=18
        )


        restart_text = (
            font_medium.render(
                "RESTART",
                True,
                BLACK
            )
        )

        restart_text_rect = (
            restart_text.get_rect(
                center=(
                    restart_button.center
                )
            )
        )

        screen.blit(
            restart_text,
            restart_text_rect
        )


        # Keyboard hint
        hint = font_small.render(
            "Click RESTART or press R",
            True,
            WHITE
        )

        hint_rect = hint.get_rect(
            center=(
                WIDTH // 2,
                625
            )
        )

        screen.blit(
            hint,
            hint_rect
        )


    # ========================================================
    # YOU-WIN SCREEN
    # ========================================================

    if game_won:

        overlay = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )

        overlay.fill((0, 35, 15, 150))
        screen.blit(overlay, (0, 0))

        win_rect = win_image.get_rect(
            center=(WIDTH // 2, 320)
        )

        screen.blit(win_image, win_rect)

        mouse_pos = pygame.mouse.get_pos()
        hovering = restart_button.collidepoint(mouse_pos)

        if hovering:
            button_color = (150, 255, 135)
        else:
            button_color = (95, 220, 110)

        pygame.draw.rect(
            screen,
            button_color,
            restart_button,
            border_radius=18
        )

        pygame.draw.rect(
            screen,
            (210, 255, 205),
            restart_button,
            4,
            border_radius=18
        )

        restart_text = font_medium.render(
            "PLAY AGAIN",
            True,
            BLACK
        )

        screen.blit(
            restart_text,
            restart_text.get_rect(
                center=restart_button.center
            )
        )

        hint = font_small.render(
            "Click PLAY AGAIN or press R",
            True,
            WHITE
        )

        screen.blit(
            hint,
            hint.get_rect(
                center=(WIDTH // 2, 625)
            )
        )


    # ========================================================
    # DISPLAY
    # ========================================================

    pygame.display.flip()


pygame.quit()
