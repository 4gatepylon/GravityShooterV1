# This file basically contains methods to update and read to/from the game state machine.
# You use it by writing a server that handles reading/writing from http and then you use
# the methods below to update the game state machine.
#
# The import components are the following:
# - Game: a class that manages a single game's state
# - GameManager: a class that manages multiple games and maps each to a websocket that can be updated with game state each time
# - MessageType: a type declaring the types of messages that we may take in from clients and may return to clients
# - MessageHandler: a type that will handle a message of a given type by parsing out its data and then giving
#   updating the corresponding game (or doing something else) if necessary
# - MessageCreator: creates the messages sent on the wire (i.e. encoding)

import json
import requests
import uuid

from fastapi import WebSocket
from typing import List, Dict, Union, Optional, Set, Any
from enum import Enum

# The client will use the CREATE through LEAVE message types in all its messages to
# ask the server to let it join a room or make different moves in that room.
# The server always returns either an error or a game state.
class MessageType(Enum):
    # Send create from client, always receive creation (creates player with id)
    CREATE = "CREATE"
    CREATION = "CREATION"

    # Send join from client, usually receive ERROR_NOT_ENOUGH_PLAYERS or eventually GAME_STATE
    JOIN = "JOIN"
    ERROR_NOT_ENOUGH_PLAYERS = "ERROR_NOT_ENOUGH_PLAYERS"
    GAME_STATE = "GAME_STATE"

    # Send guess, letter and backspace, recieve game state (above)
    GUESS = "GUESS"
    LETTER = "LETTER"
    BACKSPACE = "BACKSPACE"

    # Note used yet, but in a future version would handle the closing of a ws more elegantly
    LEAVE = "LEAVE"
    ERROR_UNK = "ERROR_UNK"

# Each message will be of the format
# {
#   "type": MessageType,
#   "data": any
# }

# The data will take on different forms depending on the type of message.
#
# If the message is CREATE,
# "data" : {
#   "player_name": str
# }
# 
# If the message is JOIN (note that the room id could be empty string if no room to join),
# "data" : {
#   "player_id": str,
# }
#
# If the message is GUESS,
# "data" : {
#   "player_id": str,
#   "room_id": str,
# }
#
# If the message is LETTER,
# "data" : {
#   "player_id": str,
#   "room_id": str,
#   "letter": str
# }
#
# If the message is BACKSPACE,
# "data" : {
#   "player_id": str,
#   "room_id": str
# }
#
# LEAVE is not used yet
#
# If the message is CREATION (noting that the room id could be "" if there is no room to join),
# "data" : {
#   "player_id": str,
# }
# 
# If the message is GAME_STATE,
# "data" : {
#   "game": serialized game object (look at game documentation)
# }
#
# If the message is ERROR_NOT_ENOUGH_PLAYERS,
# "data" : {
#  "queued": bool
#}
#
# If the message is ERROR_UNK,
# "data" : {
#   "error": str
# }

# Meant to help us create a single secret random word for the game
def gen_word(length: int = 5, number: int = 1, unwrap: bool = True) -> Union[str, List[str]]:
    if number < 1:
        raise ValueError("Number of words must be at least 1")
    if length < 1:
        raise ValueError("Length of words must be at least 1")
    if unwrap and number > 1:
        raise ValueError("Cannot unwrap multiple words")
    
    words_api = f"https://random-word-api.herokuapp.com/word?length={length}&number={number}"
    resp = requests.get(words_api).json()
    return resp[0] if unwrap else resp

MAX_NUM_GUESSES = 6
MAX_GUESS_LEN = 5
class Game:
    def __init__(self, player_names: Optional[List[str]] = None, player_ids: Optional[List[str]] = None, room_id: Optional[str] = None):
        _none_kwargs_msg = "These are None by default to force you to use kwargs. Please provide valid inputs for player_names, player_ids, and room_id."
        if player_names is None:
            raise ValueError("player_names must not be None. " + _none_kwargs_msg)
        if player_ids is None:
            raise ValueError("player_ids must not be None. " + _none_kwargs_msg)
        if room_id is None:
            raise ValueError("room_id must not be None. " +  + _none_kwargs_msg)
        
        self.player_names = {player_id: player_name for player_id, player_name in zip(player_ids, player_names)}
        self.player_ids = player_ids
        self.room_id = room_id
        self.guesses: Dict[str, str] = {player_id: "" for player_id in player_ids}
        self.past_guesses: Dict[str, List[str]] = {player_id: [] for player_id in player_ids}
        self.secret_words = {player_id : gen_word(length=5, number=1, unwrap=True) for player_id in player_ids}
        self.is_right = {player_id : False for player_id in player_ids}
        self.game_over: bool = False
        # Note that if both players fail to guess, no one wins
        self.winner: str = ""


    def _update_game_state_guess(self, player_id: str, guess: str) -> None:
        self.guesses[player_id] = ""
        self.past_guesses[player_id].append(guess)
        
        if guess == self.secret_words[player_id]:
            self.is_right[player_id] = True
            # If they are the first to guess correctly, they win
            if not all(self.is_right.values()):
                self.winner = player_id

        # If everyone has already guessed all they can, the game is over
        if min(map(len, self.past_guesses.values())) == MAX_NUM_GUESSES or any(self.is_right.values()):
            self.game_over = True
    
    def _update_game_state_letter(self, player_id: str, letter: str) -> None:
        self.guesses[player_id] += letter

    def _update_game_state_backspace(self, player_id: str) -> None:
        self.guesses[player_id] = self.guesses[player_id][:-1]
        
    def update_game_state(self, message_type: MessageType, data: Dict[str, any]) -> None:
        if message_type == MessageType.GUESS:
            player_id = data["player_id"]
            if len(self.past_guesses[player_id]) >= MAX_NUM_GUESSES:
                raise ValueError(f"Player has already guessed the maximum number of times (={MAX_NUM_GUESSES})")
                
            guess = self.guesses[player_id]
            if len(guess) != MAX_GUESS_LEN:
                raise ValueError(f"Guess must be of length {MAX_GUESS_LEN}")
            self._update_game_state_guess(player_id, guess)
                
        elif message_type == MessageType.LETTER:
            player_id = data["player_id"]
            letter = data["letter"]
            if len(letter) != 1:
                raise ValueError("Letter must be a single character")
            if len(self.guesses[player_id]) >= MAX_GUESS_LEN:
                raise ValueError(f"Guess must be of length < {MAX_GUESS_LEN}")
            self._update_game_state_letter(player_id, letter)
        
        elif message_type == MessageType.BACKSPACE:
            player_id = data["player_id"]
            if len(self.guesses[player_id]) == 0:
                raise ValueError("Cannot backspace an empty guess")
            self._update_game_state_backspace(player_id)

    
    def to_json(self, as_string: bool = False) -> Dict[str, any]:
        jdict: Dict[str, any] = {
            "player_names": self.player_names,
            "player_ids": self.player_ids,
            "room_id": self.room_id,
            "guesses": self.guesses,
            "past_guesses": self.past_guesses,
            "secret_words": self.secret_words,
            "is_right": self.is_right,
            "game_over": self.game_over,
            "winner": self.winner
        }
        if as_string:
            return json.dumps(jdict)
        return jdict

class IdManager:
    def __init__(self):
        self.used_ids: Set[str] = set()

    def generate_id(self) -> str:
        new_id: str = str(uuid.uuid4())
        while new_id in self.used_ids:
            new_id = str(uuid.uuid4())
        self.used_ids.add(new_id)
        return new_id

class GameManager:
    def __init__(self):
        # Sockets is from player_id to socket
        self.sockets: Dict[str, WebSocket] = {}

        # List of player ids queuing
        self.players_queueing: List[List[str]] = []

        # Map player ids to player names
        self.names: Dict[str, str] = {}

        # Get unique uuids
        self.player_id_manager = IdManager()
        self.room_id_manager = IdManager()

        # From room id to game
        self.games: Dict[str, Game] = {}
        self.player2game: Dict[str, str] = {}

    # Create a player, returning a player id (take in a player name that the user requested)
    def create_player(self, player_name: str, websocket: WebSocket) -> str:
        player_id = self.player_id_manager.generate_id()
        self.sockets[player_id] = websocket
        self.names[player_id] = player_name
        return player_id
        
    # Create a game and update the games map
    def create_game(self, player1_id: str, player2_id: str) -> str:
        room_id: str = self.room_id_manager.generate_id()
        
        player1_name = self.names[player1_id]
        player2_name = self.names[player2_id]
        game: Game = Game([player1_name, player2_name], [player1_id, player2_id], room_id)
        self.games[room_id] = game
        self.player2game[player1_id] = room_id
        self.player2game[player2_id] = room_id
        return room_id

    def pair_players(self, player_id: str) -> Optional[str]:
        player_name = self.names[player_id]
        
        if len(self.players_queueing) == 0:
            self.players_queueing.append([player_name, player_id])
            return None
        else:
            other_player_name, other_player_id = self.players_queueing.pop()
            return self.create_game(player_id, other_player_id)

# Create messages that are serializable onto the wire (for the client)
class MessageCreator:
    @staticmethod
    def creation(player_id: str) -> Dict[str, any]:
        return {
            "type": MessageType.CREATION.value,
            "data": {
                "player_id": player_id
            }
        }
    @staticmethod
    def error_not_enough_players(queued: bool = False) -> Dict[str, any]:
        return {
            "type": MessageType.ERROR_NOT_ENOUGH_PLAYERS.value,
            "data": {
                "queued": queued
            }
        }
    @staticmethod
    def game_state(game: Game) -> Dict[str, any]:
        return {
            "type": MessageType.GAME_STATE.value,
            "data": game.to_json(as_string = False)
        }
    


class MessageHandler:
    def __init__(self, game_manager: GameManager):
        self.game_manager = game_manager

        # So that creation is idempotent (works because socket object stays the same)
        self.socket2player_id = {}
        # So that JOIN is idempotent and GUESS, LETTER, BACKSPACE don't go to non-existent games
        self.player_id2found_game = set()

    # These methods allow you to update players in or not in games
    async def update_player_websocket(self, player_id, msg: Any) -> None:
        ws = self.game_manager.sockets[player_id]
        await ws.send_text(json.dumps(msg))
    async def update_game_websockets(self, room_id: str, message: Any) -> None:
        for player_id in self.game_manager.games[room_id].player_ids:
            await self.update_player_websocket(player_id, message)
    async def update_game_websockets_with_gamestate(self, room_id: str) -> None:
        await self.update_game_websockets(room_id, MessageCreator.game_state(self.game_manager.games[room_id]))

    # Create a response to write on the wire
    # If no return then do nothing (might be broadcasting or something else)
    async def response(self, message: Any, websocket: WebSocket) -> Optional[Any]:
        message_type = MessageType(message["type"])
        data = message["data"]

        # Create a player
        # - Give them an id
        # - Map the id to this socket
        if message_type == MessageType.CREATE:
            player_name = data["player_name"]
            if not websocket in self.socket2player_id:
                self.socket2player_id[websocket] = self.game_manager.create_player(player_name, websocket)
            return MessageCreator.creation(self.socket2player_id[websocket])

        # Join a game
        # - Try to pair with last in queue or append to queue
        # - If paired, return room id and make sure to update games of players map in gm (and other data structures)
        elif message_type == MessageType.JOIN:
            player_id = data["player_id"]
            room_id = None
            if not player_id in self.player_id2found_game:
                room_id = self.game_manager.pair_players(player_id)
            else:
                room_id = self.game_manager.player2game[player_id]
            
            if room_id:
                self.player_id2found_game.add(player_id)
                await self.update_game_websockets_with_gamestate(room_id)
            else:
                return MessageCreator.error_not_enough_players(queued = True)
            
        # Deal with moves inside a game
        # - update the game
        # - broadcast update to each player
        elif message_type in [MessageType.GUESS, MessageType.LETTER, MessageType.BACKSPACE]:
            room_id = data["room_id"]
            game = self.game_manager.games[room_id]
            game.update_game_state(message_type, data)
            await self.update_game_websockets_with_gamestate(room_id)

        # Unsupported
        else:
            raise ValueError(f"Unsupported message type {message_type}")

    # This function helps us decide when to close a socket if necessary
    # NOTE that we have a memory leak: the game is not actually cleaned up,
    # in a production setting we should obviously delete the game
    def keep_open(self, websocket: WebSocket) -> bool:
        player_id = self.socket2player_id[websocket]
        if player_id in self.player_id2found_game:
            room_id = self.game_manager.player2game[player_id]
            return not self.game_manager.games[room_id].game_over
        return True

            
    # Return whether to close the socket or not
    async def handle(self, _request: Union[Any, str], websocket: WebSocket) -> None:
        # Parse request as is possible
        request = None
        try:
            request = json.loads(_request)
        except Exception as e:
            print(f"WARNING: could not decode request\n{_request}\n(ERROR WAS\n{e}\n)")
            request = _request
        if not request:
            raise ValueError("Request was never set!")

        # Respond
        resp = await self.response(request, websocket)
        if resp:
            await websocket.send_text(json.dumps(resp))


