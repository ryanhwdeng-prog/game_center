from __future__ import annotations

import sys
from pathlib import Path

import pygame

try:
    from .password_logic import CHEAT_PASSWORD, GamePasswordState, load_state
except ImportError:  # pragma: no cover - direct script execution
    from password_logic import CHEAT_PASSWORD, GamePasswordState, load_state


STATE_PATH = Path(__file__).with_name("state.json")
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 650


class PasswordGame:
    def __init__(self):
        self.state = load_state(STATE_PATH)
        self.active_field = "guess"
        self.guess = ""
        self.new_password = ""
        self.new_title = self.state.title
        self.message = "Enter the current password to change the game."
        self.unlocked = False
        self.current_guess = ""

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.submit()
                return
            if event.key == pygame.K_TAB:
                self.active_field = "new_password" if self.active_field == "guess" else "guess"
                return
            if event.key == pygame.K_BACKSPACE:
                self._delete_from_active_field()
                return
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            if event.unicode and event.unicode.isprintable():
                self._append_to_active_field(event.unicode)

    def _append_to_active_field(self, value):
        if self.active_field == "guess":
            self.guess += value
        elif self.active_field == "new_password":
            self.new_password += value
        else:
            self.new_title += value

    def _delete_from_active_field(self):
        if self.active_field == "guess":
            self.guess = self.guess[:-1]
        elif self.active_field == "new_password":
            self.new_password = self.new_password[:-1]
        else:
            self.new_title = self.new_title[:-1]

    def submit(self):
        if not self.unlocked:
            guess = self.guess.strip()
            if guess == CHEAT_PASSWORD or self.state.is_valid_guess(guess):
                self.unlocked = True
                self.current_guess = guess
                self.message = "Password accepted. Choose a new password and title."
                self.guess = ""
                self.active_field = "new_password"
                return
            self.message = "Incorrect password. Try again or use the cheat code."
            self.guess = ""
            return

        outcome = self.state.set_password(
            guess=self.current_guess,
            new_password=self.new_password.strip(),
            new_title=self.new_title.strip(),
        )
        if outcome:
            self.message = f"Saved! The password is now {self.state.password} and the game is named {self.state.title}."
            self.unlocked = False
            self.current_guess = ""
            self.guess = ""
            self.new_password = ""
            self.new_title = self.state.title
            self.active_field = "guess"
            return

        self.message = "The cheat password cannot be used as the new password. Please pick a different one."
        self.new_password = ""
        self.new_title = self.state.title

    def draw(self, screen):
        screen.fill((15, 19, 34))

        title = pygame.font.SysFont(None, 70, bold=True).render(self.state.title, True, (255, 245, 200))
        screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 88)))

        subtitle = pygame.font.SysFont(None, 28).render("Guess the secret code to rename the game and change the password.", True, (177, 201, 250))
        screen.blit(subtitle, subtitle.get_rect(center=(WINDOW_WIDTH // 2, 132)))

        panel = pygame.Rect(100, 170, 700, 400)
        pygame.draw.rect(screen, (28, 35, 52), panel, border_radius=22)
        pygame.draw.rect(screen, (125, 165, 255), panel, 2, border_radius=22)

        accent = pygame.font.SysFont(None, 26, bold=True).render("CURRENT PASSWORD", True, (156, 182, 255))
        screen.blit(accent, (140, 200))
        guess_box = pygame.Rect(140, 230, 620, 50)
        box_color = (62, 72, 102) if self.active_field == "guess" else (44, 52, 75)
        pygame.draw.rect(screen, box_color, guess_box, border_radius=10)
        if self.unlocked:
            visible = "Unlocked"
        else:
            visible = self.guess
        guess_text = pygame.font.SysFont(None, 34).render(visible, True, (243, 246, 255))
        screen.blit(guess_text, (160, 238))

        if self.unlocked:
            new_password_label = pygame.font.SysFont(None, 26, bold=True).render("NEW PASSWORD", True, (156, 182, 255))
            screen.blit(new_password_label, (140, 300))
            new_password_box = pygame.Rect(140, 330, 620, 50)
            pygame.draw.rect(screen, (62, 72, 102) if self.active_field == "new_password" else (44, 52, 75), new_password_box, border_radius=10)
            password_text = pygame.font.SysFont(None, 34).render(self.new_password, True, (243, 246, 255))
            screen.blit(password_text, (160, 338))

            new_title_label = pygame.font.SysFont(None, 26, bold=True).render("NEW GAME NAME", True, (156, 182, 255))
            screen.blit(new_title_label, (140, 400))
            new_title_box = pygame.Rect(140, 430, 620, 50)
            pygame.draw.rect(screen, (62, 72, 102) if self.active_field == "new_title" else (44, 52, 75), new_title_box, border_radius=10)
            title_text = pygame.font.SysFont(None, 34).render(self.new_title, True, (243, 246, 255))
            screen.blit(title_text, (160, 438))

        cheat = pygame.font.SysFont(None, 26).render(f"Cheat password: {CHEAT_PASSWORD}", True, (255, 214, 102))
        screen.blit(cheat, (140, 510))

        message = pygame.font.SysFont(None, 28).render(self.message, True, (255, 255, 255))
        screen.blit(message, message.get_rect(midleft=(140, 565)))

        button = pygame.Rect(675, 540, 150, 42)
        pygame.draw.rect(screen, (102, 222, 116), button, border_radius=14)
        button_text = pygame.font.SysFont(None, 28, bold=True).render("SAVE" if self.unlocked else "TRY", True, (13, 22, 27))
        screen.blit(button_text, button_text.get_rect(center=button.center))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Guess My Password")
    clock = pygame.time.Clock()
    game = PasswordGame()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                button = pygame.Rect(675, 540, 150, 42)
                if button.collidepoint(pos):
                    game.submit()
            else:
                game.handle_event(event)

        game.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
