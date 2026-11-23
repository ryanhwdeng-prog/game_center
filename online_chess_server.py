from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import secrets
import string
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Set, Tuple

import chess
from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosed

ROOM_CODE_LENGTH = 6
MAX_ROOMS = 500
MAX_MESSAGE_BYTES = 2048
DISCONNECTED_ROOM_TTL_SECONDS = 60 * 60 * 6
ROOM_CODE_ALPHABET = string.ascii_uppercase.replace("I", "").replace("O", "") + "23456789"
DEFAULT_ALLOWED_ORIGINS = ("http://localhost:8000", "http://127.0.0.1:8000")
LOGGER = logging.getLogger("online_chess")


@dataclass
class Player:
    name: str
    color: chess.Color
    token: str
    connection: Optional[ServerConnection] = None


@dataclass
class ChessRoom:
    code: str
    board: chess.Board = field(default_factory=chess.Board)
    players: Dict[chess.Color, Optional[Player]] = field(
        default_factory=lambda: {chess.WHITE: None, chess.BLACK: None}
    )
    rematch_votes: Set[chess.Color] = field(default_factory=set)
    updated_at: float = field(default_factory=time.monotonic)


class OnlineChessHub:
    def __init__(self) -> None:
        self.rooms: Dict[str, ChessRoom] = {}

    def create_room(self, name: str, connection: ServerConnection) -> Tuple[ChessRoom, Player]:
        self._expire_disconnected_rooms()
        if len(self.rooms) >= MAX_ROOMS:
            raise ValueError("The server is full. Please try again later.")
        code = self._new_room_code()
        room = ChessRoom(code=code)
        player = Player(name=self._validate_name(name), color=chess.WHITE, token=secrets.token_urlsafe(24), connection=connection)
        room.players[chess.WHITE] = player
        self.rooms[code] = room
        return room, player

    def join_room(
        self,
        code: str,
        name: str,
        connection: ServerConnection,
        token: Optional[str] = None,
    ) -> Tuple[ChessRoom, Player]:
        self._expire_disconnected_rooms()
        normalized_code = code.strip().upper() if isinstance(code, str) else ""
        if not re.fullmatch(r"[A-HJ-NP-Z2-9]{6}", normalized_code):
            raise ValueError("Enter a valid six-character room code.")
        if token is not None and (not isinstance(token, str) or len(token) > 128):
            raise ValueError("Invalid reconnect token.")
        room = self.rooms.get(normalized_code)
        if room is None:
            raise ValueError("That room was not found or has expired.")

        if token:
            for existing in room.players.values():
                if existing and secrets.compare_digest(existing.token, token):
                    if existing.connection is not None:
                        raise ValueError("That player is already connected.")
                    existing.connection = connection
                    room.updated_at = time.monotonic()
                    return room, existing
            raise ValueError("That reconnect token is no longer valid.")

        player_name = self._validate_name(name)
        if room.players[chess.BLACK] is None:
            color = chess.BLACK
        elif room.players[chess.WHITE] is None:
            color = chess.WHITE
        else:
            disconnected = next(
                (room.players[color] for color in (chess.WHITE, chess.BLACK)
                 if room.players[color] and room.players[color].connection is None),
                None,
            )
            if disconnected is None:
                raise ValueError("That room already has two players.")
            disconnected.name = player_name
            disconnected.token = secrets.token_urlsafe(24)
            disconnected.connection = connection
            room.updated_at = time.monotonic()
            return room, disconnected

        player = Player(name=player_name, color=color, token=secrets.token_urlsafe(24), connection=connection)
        room.players[color] = player
        room.updated_at = time.monotonic()
        return room, player

    def apply_move(self, room: ChessRoom, player: Player, connection: ServerConnection, uci: object) -> None:
        if room.players[player.color] is not player or player.connection is not connection:
            raise ValueError("You are no longer connected to this room.")
        if not all(room.players[color] and room.players[color].connection for color in (chess.WHITE, chess.BLACK)):
            raise ValueError("Wait for both players to join before moving.")
        if room.board.turn != player.color:
            raise ValueError("It is not your turn.")
        if not isinstance(uci, str) or not re.fullmatch(r"[a-h][1-8][a-h][1-8][qrbn]?", uci):
            raise ValueError("Invalid move format.")
        try:
            move = chess.Move.from_uci(uci)
        except ValueError as error:
            raise ValueError("Invalid move format.") from error
        if move not in room.board.legal_moves:
            raise ValueError("That move is not legal.")
        room.board.push(move)
        room.rematch_votes.clear()
        room.updated_at = time.monotonic()

    def result(self, board: chess.Board) -> Optional[dict]:
        if board.is_checkmate():
            return {
                "type": "checkmate",
                "winner": "black" if board.turn == chess.WHITE else "white",
            }
        if board.is_game_over():
            return {"type": "draw"}
        return None

    def room_state(self, room: ChessRoom, player: Player) -> dict:
        return {
            "type": "room_state",
            "code": room.code,
            "color": "white" if player.color == chess.WHITE else "black",
            "token": player.token,
            "players": {
                "white": self._player_state(room.players[chess.WHITE]),
                "black": self._player_state(room.players[chess.BLACK]),
            },
            "connected": all(
                room.players[color] and room.players[color].connection
                for color in (chess.WHITE, chess.BLACK)
            ),
            "moves": [move.uci() for move in room.board.move_stack],
            "turn": "white" if room.board.turn == chess.WHITE else "black",
            "result": self.result(room.board),
        }

    async def send_room_state(self, room: ChessRoom) -> None:
        for player in room.players.values():
            if player and player.connection:
                try:
                    await self._send(player.connection, self.room_state(room, player))
                except ConnectionClosed:
                    player.connection = None

    async def handler(self, connection: ServerConnection) -> None:
        room: Optional[ChessRoom] = None
        player: Optional[Player] = None
        try:
            async for raw_message in connection:
                if not isinstance(raw_message, str) or len(raw_message.encode("utf-8")) > MAX_MESSAGE_BYTES:
                    await self._send_error(connection, "Message is too large.")
                    continue
                try:
                    message = json.loads(raw_message)
                except json.JSONDecodeError:
                    await self._send_error(connection, "Invalid message.")
                    continue
                if not isinstance(message, dict):
                    await self._send_error(connection, "Invalid message.")
                    continue

                action = message.get("type")
                if room is None:
                    try:
                        if action == "create":
                            room, player = self.create_room(message.get("name"), connection)
                        elif action == "join":
                            room, player = self.join_room(
                                message.get("code"),
                                message.get("name"),
                                connection,
                                message.get("token"),
                            )
                        else:
                            raise ValueError("Create a room or join with a room code.")
                    except ValueError as error:
                        await self._send_error(connection, str(error))
                        continue
                    await self.send_room_state(room)
                    continue

                if action == "move":
                    try:
                        if player is None:
                            raise ValueError("Join a room before moving.")
                        self.apply_move(room, player, connection, message.get("uci"))
                    except ValueError as error:
                        await self._send_error(connection, str(error))
                        continue
                    await self.send_room_state(room)
                elif action == "rematch":
                    if player is None or room.players[player.color] is not player:
                        await self._send_error(connection, "You are no longer connected to this room.")
                        continue
                    room.rematch_votes.add(player.color)
                    room.updated_at = time.monotonic()
                    if room.rematch_votes == {chess.WHITE, chess.BLACK}:
                        room.board.reset()
                        room.rematch_votes.clear()
                        await self.send_room_state(room)
                    else:
                        await self._broadcast(
                            room,
                            {
                                "type": "rematch_pending",
                                "name": player.name,
                            },
                        )
                elif action == "leave":
                    if player and room.players[player.color] is player:
                        room.players[player.color] = None
                        room.rematch_votes.clear()
                        room.updated_at = time.monotonic()
                        await self._send(connection, {"type": "left"})
                        if any(room.players.values()):
                            await self.send_room_state(room)
                        else:
                            self.rooms.pop(room.code, None)
                    room = None
                    player = None
                else:
                    await self._send_error(connection, "Unsupported message type.")
        except ConnectionClosed:
            pass
        finally:
            if room and player and room.players[player.color] is player and player.connection is connection:
                player.connection = None
                room.updated_at = time.monotonic()
                await self._broadcast(
                    room,
                    {
                        "type": "opponent_disconnected",
                        "name": player.name,
                    },
                )

    async def _broadcast(self, room: ChessRoom, message: dict) -> None:
        for player in room.players.values():
            if player and player.connection:
                try:
                    await self._send(player.connection, message)
                except ConnectionClosed:
                    player.connection = None

    async def _send_error(self, connection: ServerConnection, message: str) -> None:
        await self._send(connection, {"type": "error", "message": message})

    async def _send(self, connection: ServerConnection, message: dict) -> None:
        await connection.send(json.dumps(message))

    def _new_room_code(self) -> str:
        for _ in range(20):
            code = "".join(secrets.choice(ROOM_CODE_ALPHABET) for _ in range(ROOM_CODE_LENGTH))
            if code not in self.rooms:
                return code
        raise ValueError("Could not create a room. Please try again.")

    def _expire_disconnected_rooms(self) -> None:
        now = time.monotonic()
        expired = [
            code
            for code, room in self.rooms.items()
            if not any(player and player.connection for player in room.players.values())
            and now - room.updated_at > DISCONNECTED_ROOM_TTL_SECONDS
        ]
        for code in expired:
            self.rooms.pop(code, None)

    @staticmethod
    def _validate_name(name: object) -> str:
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 24:
            raise ValueError("Player name must contain 1 to 24 characters.")
        return name.strip()

    @staticmethod
    def _player_state(player: Optional[Player]) -> Optional[dict]:
        if player is None:
            return None
        return {"name": player.name, "connected": player.connection is not None}


def allowed_origins() -> list[str]:
    configured = os.environ.get("ALLOWED_ORIGINS", "")
    if not configured.strip():
        return list(DEFAULT_ALLOWED_ORIGINS)
    origins = [origin.strip() for origin in configured.split(",") if origin.strip()]
    if not origins:
        raise ValueError("ALLOWED_ORIGINS must contain at least one website origin.")
    return origins


async def run_server() -> None:
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8766"))
    hub = OnlineChessHub()
    async with serve(
        hub.handler,
        host,
        port,
        origins=allowed_origins(),
        max_size=MAX_MESSAGE_BYTES,
        ping_interval=20,
        ping_timeout=20,
    ) as server:
        LOGGER.info("Online Chess WebSocket server listening on %s:%s", host, server.sockets[0].getsockname()[1])
        await asyncio.Future()


def main() -> None:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        LOGGER.info("Stopping Online Chess server")


if __name__ == "__main__":
    main()
