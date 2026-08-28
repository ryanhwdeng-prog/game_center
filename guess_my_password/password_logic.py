from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_PASSWORD = "0000"
CHEAT_PASSWORD = "2217_540612"
DEFAULT_TITLE = "Guess My Password"


@dataclass
class GamePasswordState:
    path: Path | str = field(default_factory=lambda: Path(__file__).with_name("state.json"))
    password: str = DEFAULT_PASSWORD
    title: str = DEFAULT_TITLE

    def __post_init__(self):
        self.path = Path(self.path)
        if not self.path.exists():
            self.save()

    def is_valid_guess(self, guess: str) -> bool:
        cleaned = (guess or "").strip()
        return cleaned == self.password or cleaned == CHEAT_PASSWORD

    def set_password(self, guess: str, new_password: str | None = None, new_title: str | None = None) -> bool:
        cleaned_guess = (guess or "").strip()
        if not self.is_valid_guess(cleaned_guess):
            return False

        candidate_password = (new_password or "").strip()
        candidate_title = (new_title or self.title).strip()

        if not candidate_password:
            return False
        if candidate_password == CHEAT_PASSWORD:
            return False
        if not candidate_title:
            candidate_title = self.title

        self.password = candidate_password
        self.title = candidate_title
        self.save()
        return True

    def save(self):
        payload = {"password": self.password, "title": self.title}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_state(path: str | Path | None = None) -> GamePasswordState:
    state_path = Path(path) if path is not None else Path(__file__).with_name("state.json")
    state_path = Path(state_path)
    state = GamePasswordState(path=state_path)

    if state_path.exists():
        try:
            payload = json.loads(state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            payload = {}
        state.password = str(payload.get("password", DEFAULT_PASSWORD)).strip() or DEFAULT_PASSWORD
        state.title = str(payload.get("title", DEFAULT_TITLE)).strip() or DEFAULT_TITLE
    else:
        state.password = DEFAULT_PASSWORD
        state.title = DEFAULT_TITLE
        state.save()

    return state


def set_state(path: str | Path | None = None, password: str | None = None, title: str | None = None) -> GamePasswordState:
    state = load_state(path)
    if password is not None:
        state.password = str(password).strip() or DEFAULT_PASSWORD
    if title is not None:
        state.title = str(title).strip() or DEFAULT_TITLE
    state.save()
    return state
