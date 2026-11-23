import json
import unittest

from websockets.asyncio.client import connect
from websockets.asyncio.server import serve

from online_chess_server import OnlineChessHub


class OnlineChessServerTests(unittest.IsolatedAsyncioTestCase):
    async def test_rooms_validate_turns_and_broadcast_legal_moves(self):
        hub = OnlineChessHub()
        async with serve(hub.handler, "127.0.0.1", 0) as server:
            port = server.sockets[0].getsockname()[1]
            async with connect("ws://127.0.0.1:{}".format(port)) as white:
                await white.send(json.dumps({"type": "create", "name": "Alice"}))
                white_state = json.loads(await white.recv())
                self.assertEqual(white_state["color"], "white")
                self.assertEqual(len(white_state["code"]), 6)

                async with connect("ws://127.0.0.1:{}".format(port)) as black:
                    await black.send(
                        json.dumps(
                            {
                                "type": "join",
                                "name": "Bob",
                                "code": white_state["code"],
                            }
                        )
                    )
                    black_state = json.loads(await black.recv())
                    updated_white_state = json.loads(await white.recv())
                    self.assertEqual(black_state["color"], "black")
                    self.assertTrue(updated_white_state["connected"])

                    await white.send(json.dumps({"type": "move", "uci": "e2e4"}))
                    white_after_move = json.loads(await white.recv())
                    black_after_move = json.loads(await black.recv())
                    self.assertEqual(white_after_move["moves"], ["e2e4"])
                    self.assertEqual(black_after_move["turn"], "black")

                    await white.send(json.dumps({"type": "move", "uci": "e7e5"}))
                    error = json.loads(await white.recv())
                    self.assertEqual(error["type"], "error")
                    self.assertEqual(error["message"], "It is not your turn.")

                    await black.send(json.dumps({"type": "move", "uci": "e7e5"}))
                    white_after_reply = json.loads(await white.recv())
                    black_after_reply = json.loads(await black.recv())
                    self.assertEqual(white_after_reply["moves"], ["e2e4", "e7e5"])
                    self.assertEqual(black_after_reply["turn"], "white")

                    await black.close()
                    disconnected = json.loads(await white.recv())
                    self.assertEqual(disconnected["type"], "opponent_disconnected")
                    async with connect("ws://127.0.0.1:{}".format(port)) as reconnected_black:
                        await reconnected_black.send(
                            json.dumps(
                                {
                                    "type": "join",
                                    "name": "Bob again",
                                    "code": white_state["code"],
                                }
                            )
                        )
                        reconnected_state = json.loads(await reconnected_black.recv())
                        white_reconnected_state = json.loads(await white.recv())
                        self.assertEqual(reconnected_state["color"], "black")
                        self.assertEqual(reconnected_state["moves"], ["e2e4", "e7e5"])
                        self.assertEqual(white_reconnected_state["players"]["black"]["name"], "Bob again")

                        await white.send(json.dumps({"type": "rematch"}))
                        pending_white = json.loads(await white.recv())
                        pending_black = json.loads(await reconnected_black.recv())
                        self.assertEqual(pending_white["type"], "rematch_pending")
                        self.assertEqual(pending_black["type"], "rematch_pending")
                        await reconnected_black.send(json.dumps({"type": "rematch"}))
                        white_rematch = json.loads(await white.recv())
                        black_rematch = json.loads(await reconnected_black.recv())
                        self.assertEqual(white_rematch["moves"], [])
                        self.assertEqual(black_rematch["turn"], "white")


    async def test_rejects_invalid_name_and_illegal_move(self):
        hub = OnlineChessHub()
        async with serve(hub.handler, "127.0.0.1", 0) as server:
            port = server.sockets[0].getsockname()[1]
            async with connect("ws://127.0.0.1:{}".format(port)) as white:
                await white.send(json.dumps({"type": "create", "name": "   "}))
                error = json.loads(await white.recv())
                self.assertEqual(error["type"], "error")

                await white.send(json.dumps({"type": "create", "name": "Alice"}))
                state = json.loads(await white.recv())
                async with connect("ws://127.0.0.1:{}".format(port)) as black:
                    await black.send(
                        json.dumps(
                            {
                                "type": "join",
                                "name": "Bob",
                                "code": state["code"],
                            }
                        )
                    )
                    await black.recv()
                    await white.recv()

                    await white.send(json.dumps({"type": "move", "uci": "b1b3"}))
                    illegal_move = json.loads(await white.recv())
                    self.assertEqual(illegal_move["type"], "error")
                    self.assertEqual(illegal_move["message"], "That move is not legal.")


if __name__ == "__main__":
    unittest.main()
