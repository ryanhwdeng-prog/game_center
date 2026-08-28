from __future__ import annotations

import subprocess
import sys
from getpass import getpass
from pathlib import Path

import pygame

ROOT = Path(__file__).resolve().parent
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
GAME_PASSWORD = "540612"


class GameCard:
    def __init__(self, title: str, folder: str, script_name: str, color):
        self.title = title
        self.folder = folder
        self.script_name = script_name
        self.color = color
        self.rect = pygame.Rect(0, 0, 300, 160)


def find_games():
    games = []
    for folder in sorted(ROOT.iterdir()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        for script in sorted(folder.glob("*.py")):
            if script.name == "game_center.py":
                continue
            name = folder.name.replace("_", " ").title()
            color = (84, 160, 255) if folder.name.lower() == "bear" else (240, 120, 180)
            games.append(GameCard(name, folder.name, script.name, color))
    return games


def launch_game(game_path: Path):
    subprocess.run([sys.executable, str(game_path)], cwd=str(game_path.parent), check=False)


def draw_center_menu(screen, games, hovered_index, selected_index, quit_button):
    screen.fill((18, 25, 40))

    title = pygame.font.SysFont(None, 68, bold=True).render("GAME CENTER", True, (255, 245, 200))
    screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 90)))

    subtitle = pygame.font.SysFont(None, 28).render("Pick a game to play", True, (195, 210, 235))
    screen.blit(subtitle, subtitle.get_rect(center=(WINDOW_WIDTH // 2, 140)))

    start_x = 100
    start_y = 190
    gap_x = 40
    gap_y = 30
    per_row = 2

    for index, game in enumerate(games):
        col = index % per_row
        row = index // per_row
        game.rect.topleft = (
            start_x + col * (game.rect.width + gap_x),
            start_y + row * (game.rect.height + gap_y),
        )

        is_hovered = index == hovered_index
        is_selected = index == selected_index

        card_color = game.color
        if is_hovered:
            card_color = tuple(min(255, value + 30) for value in game.color)
        if is_selected:
            card_color = tuple(min(255, value + 45) for value in game.color)

        pygame.draw.rect(screen, card_color, game.rect, border_radius=22)
        pygame.draw.rect(screen, (255, 255, 255, 120), game.rect, 3, border_radius=22)

        label = pygame.font.SysFont(None, 42, bold=True).render(game.title, True, (20, 20, 30))
        label_rect = label.get_rect(center=game.rect.center)
        label_rect.y -= 10
        screen.blit(label, label_rect)

        detail = pygame.font.SysFont(None, 22).render(game.script_name, True, (35, 45, 60))
        detail_rect = detail.get_rect(center=game.rect.center)
        detail_rect.y += 32
        screen.blit(detail, detail_rect)

        play_text = pygame.font.SysFont(None, 24, bold=True).render("PLAY", True, (255, 255, 255))
        play_rect = play_text.get_rect(center=(game.rect.centerx, game.rect.bottom - 26))
        screen.blit(play_text, play_rect)

    pygame.draw.rect(screen, (240, 80, 80), quit_button, border_radius=16)
    quit_text = pygame.font.SysFont(None, 32, bold=True).render("QUIT", True, (255, 255, 255))
    screen.blit(quit_text, quit_text.get_rect(center=quit_button.center))


def main():
    if getpass("Enter game center password: ") != GAME_PASSWORD:
        print("Incorrect password.")
        return

    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Game Center")
    clock = pygame.time.Clock()

    games = find_games()
    hovered_index = -1
    selected_index = -1
    quit_button = pygame.Rect(410, 610, 180, 52)

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEMOTION:
                hovered_index = -1
                for index, game in enumerate(games):
                    if game.rect.collidepoint(mouse_pos):
                        hovered_index = index
                        break
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if quit_button.collidepoint(mouse_pos):
                    running = False
                    break
                for index, game in enumerate(games):
                    if game.rect.collidepoint(mouse_pos):
                        selected_index = index
                        launch_game(ROOT / games[index].folder / games[index].script_name)
                        selected_index = -1
                        hovered_index = -1
                        break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        draw_center_menu(screen, games, hovered_index, selected_index, quit_button)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
