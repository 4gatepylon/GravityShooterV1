# Boilerplate from
# https://fastapi.tiangolo.com/advanced/websockets/
# Run with
#  `uvicorn server:app --reload`
# 
# Test if this is running using netcat (https://www.cyberciti.biz/faq/linux-port-scanning/):
#  `nc -z -v localhost 8888`
#
# NOTE
# This webserver code is old and expects a different format (i.e. using comma-delimitted)
# and so will not work with the new format. I keep it here in case we want to use the dummy_frontend.html

from __future__ import annotations
from typing import Optional

from pprint import PrettyPrinter
pp = PrettyPrinter()
pprint = lambda x: pp.pprint(x)

from fastapi import FastAPI, WebSocket, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from enum import Enum
import json
import requests

# Middleware is important to allow us to test locally (this is not a production ready app)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

####################################################################################################
# Here we add a logger for when FastAPI is not able to parse the incoming type
# of a message. For example, if the POST request to join a game (get a room id) does not provide the
# right player_id field

async def print_request(request):
    print(f'request header' )
    pprint(dict(request.headers.items()))
    print(f'request query params')
    pprint(dict(request.query_params.items()))
    # NOTE these tend to hang which is quite infurating
    try: 
        print(f'request json')
        pprint(await request.json())
    except Exception as err:
        # could not parse json
        print(f'request body')
        pprint(await request.body())
def register_exception(app: FastAPI):
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
        print(exc_str)
        await print_request(request)
        content = {'status_code': 10422, 'message': exc_str, 'data': None}
        return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
register_exception(app)


####################################################################################################
# This will be a queue of players
players_queue_g = []

def try_to_pair_players(player_id: int) -> Optional[tuple[int, int]]:
    global players_queue_g

    if player_id in players_queue_g:
        raise RuntimeError("Unreachable code: trying to pair players but the queue has the player already in it")
    else:
        # Case 2: not tried yet
        if len(players_queue_g) < 1:
            players_queue_g = [player_id]
            return None
        opponent_id = players_queue_g.pop()
        return (player_id, opponent_id)

# This will map chat room id to clients
rooms_g = {}
rooms_websockets_g = {}

player2rooms_g = {}

# We will simply create uuid's by incrementing this
latest_room_id_g = 0

# We will simply create uuid's here with the same mechanism
latest_player_id_g = 0

def create_room_id() -> int:
    global latest_room_id_g
    latest_room_id_g += 1
    return latest_room_id_g

def create_player_id() -> int:
    global latest_player_id_g
    latest_player_id_g += 1
    return latest_player_id_g

# note that we will expect the client side to allow or disallow guesses based on whether
# they are in the dictionary...
def create_secret_word() -> str:
    words_api = "https://random-word-api.herokuapp.com/word?length=5&number=1"
    return requests.get(words_api).json()[0]

# try to create a room for this player to join with another player, if so
# return the room id and the id of the other player
def try_to_join_room(player_id: int) -> Optional[int]:
    global rooms_g, player2rooms_g

    if player_id in player2rooms_g:
        return player2rooms_g[player_id]

    _opt = try_to_pair_players(player_id)
    if _opt is None:
        return None
    player_id, opponent_id = _opt
    room_id = create_room_id()
    
    # TODO we might want to get the player names in there somehow
    rooms_g[room_id] = {
        # maybe the name will be completely ignored for now
        "player_ids": [player_id, opponent_id],
        "room_id": room_id,
        "guesses": {
            player_id: "",
            opponent_id: ""
        },
        "past_guesses": {
            player_id: [],
            opponent_id: []
        },
        "secret_words": {
            player_id: create_secret_word(),
            opponent_id: create_secret_word()
        },
        "gameover": "false",
        "winner": "none"
    }
    print("********** CREATING GAME **********")
    pprint(rooms_g[room_id])
    print("********** ************* **********")
    rooms_websockets_g[room_id] = []
    player2rooms_g[player_id] = room_id
    player2rooms_g[opponent_id] = room_id

    return room_id

####################################################################################################

# This will serve our client
# FIXME here we will return the index that is output by the React build tooling
# (so basically first build using react, then return that file as HTML here)
html_g = None
with open("dummy_frontend.html", "r") as df:
    html_g = df.read()

@app.get("/dummy_html")
async def dummy_html():
    global html_g
    assert html_g is not None
    return HTMLResponse(html_g)

@app.get("/create_player")
async def create_player():
    return create_player_id()

class JoinRoomReq(BaseModel):
    player_id: str
class JoinRoomFail(Enum):
    NO_OTHER_PLAYER = "NO_OTHER_PLAYER"
    UNK = "UNK"
@app.post("/join_room")
async def join_room(req: JoinRoomReq):
    _opt = try_to_join_room(req.player_id)
    if _opt is None:
        return f"FAIL: {JoinRoomFail.NO_OTHER_PLAYER.value}"
    return f"{_opt}" # This is the room id as a string (but repr. an int)

####################################################################################################

# Busy loop on each connection to the websocket
# In the future we may want to send player ids, but it shouldn't be necessary since each player
# knows who they are, so they can just say which player made the move each time
class ActionType(Enum):
    LETTER = 0
    BACKSPACE = 1
    GUESS = 2

# Just helper methods to deal with lots of error checking
def first_contact_ok(_, room_id, __, ___, websocket=None):
    if room_id not in rooms_g:
        print(f"ERROR: non-idempotent first contact (by {room_id}) message")
        return False
    if len(rooms_websockets_g[room_id]) >= 2:
        print("ERROR: too many players in the game")
        return False # this should not happen, because only two people should be joining
    if websocket and websocket in rooms_websockets_g[room_id]:
        print("ERROR: non-idempotent websocket adding")
        return False # this should not happen, because you should only be adding yourself once...
    return True

def room_and_player_ok(_, room_id, player_id, __):
    global rooms_g
    if not room_id in rooms_g:
        print("ERROR: tried to do something in a non-existent room")
        return False # this should not happen
    if not player_id in rooms_g[room_id]["player_ids"]:
        print("ERROR: tried to do something with a non-existent player in the room")
        return False # this should not happen
    return True

def letter_ok(_, room_id, player_id, payload):
    if len(payload) == 0:
        print("ERROR: empty payload on letter action")
        return False # this should not happen
    if len(payload) == 1 and not ord('a') <= ord(payload) and ord(payload) <= ord('z'):
        print("ERROR: payload not a-z on letter action")
        return False # this should not happen
    if len(rooms_g[room_id]["guesses"][player_id]) == 5:
        print("ERROR: letter, but no more space (len 5)")
        return False # this should not happen
    return True

def backspace_ok(_, room_id, player_id, payload):
    if len(payload) != 0:
        print("ERROR: non-empty payload on backspace action")
        return # this should not happen
    if len(rooms_g[room_id]["guesses"][player_id]) == 0:
        print("ERROR: backspace, but guess is empty")
        return # this should not happen
    return True

def guess_ok(_, room_id, player_id, payload):
    if len(payload) != 0:
        print("ERROR: non-empty payload on guess action")
        return False # this should not happen
    # 5 is the length of any word you'd guess
    if len(rooms_g[room_id]["guesses"][player_id]) != 5:
        print("ERROR: guess, but word isn't complete (len 5)")
        return False # this should not happen
    if len(rooms_g[room_id]["past_guesses"][player_id]) >= 6:
        print("ERROR: at least 6 past guesses strictly, but trying to guess; wtf")
        return False # this should not happen
    return True

# make sure the game ends if it is truly over, return whether its over
def update_with_gameover(room_id: int) -> None:
    global rooms_g
    # setting gameover is idempotent
    if rooms_g[room_id]["gameover"] == "false":
        for i in range(2):
            player_id = rooms_g[room_id]["player_ids"][i]
            if rooms_g[room_id]["secret_words"][player_id] in rooms_g[room_id]["past_guesses"][player_id]:
                rooms_g[room_id]["gameover"] = "true"
                rooms_g[room_id]["winner"] = player_id
                return True
    return False

# somewhat monolithic websocket connection
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global rooms_g, rooms_websockets_g
    try:
        await websocket.accept()

        # We assume that all contacts will send a first text at some point in the near future
        first_contact = await websocket.receive_text()
        try:
            # In the future they'll probably send their name and/or id in comma-delimitted form
            assert "," in first_contact
            first_contact = int(first_contact.split(",")[0])
        except:
            print(f"ERROR: faulty first contact (from {first_contact}) message")
            return # If they don't start out with the room id just fail it
        room_id = first_contact

        if not first_contact_ok(None, room_id, None, None, websocket=websocket):
            return # should not happen
        
        rooms_websockets_g[room_id].append(websocket)
        # Once they join we send them the current state of the room so they can display
        await websocket.send_text(json.dumps(rooms_g[room_id]))
        
        # Now we
        while True:
            request = await websocket.receive_text()

            action, room_id, player_id, payload = None, None, None, None
            try:
                # put , meaninglessly at the end if backspace or guess
                assert "," in request
                action, room_id, player_id, payload = request.split(",")
                action = ActionType(int(action))
                payer_id = int(player_id)
                room_id = int(room_id)
                assert len(payload) <= 1
            except:
                print("ERROR: invalid action/payload")
                return # this should not happen, we can just quit this connection and cry about it

            if not room_and_player_ok(None, room_id, player_id, None):
                return # this should not happen
            
            if action == ActionType.LETTER: # IN THE CASE OF A LETTER WE JUST ADD THE PAYLOAD TO THE GUESS
                if not letter_ok(None, room_id, player_id, payload):
                    return # should not happen
                rooms_g[room_id]["guesses"][player_id] += payload
            elif action == ActionType.BACKSPACE: # IN THE CASE OF A BACKSPACE WE REMOVE THE LAST CHAR OF THE GUESS
                if not backspace_ok(None, room_id, player_id, payload):
                    return # should not happen
                rooms_g[room_id]["guesses"][player_id] = rooms_g[room_id]["guesses"][player_id][:-1]
            else: # IN THE CASE OF A GUESS WE CLEAR THE GUESS AND PUSH THAT GUESS TO THE PAST GUESSES
                assert action == ActionType.GUESS
                if not guess_ok(None, room_id, player_id, payload):
                    return # should not happen
                rooms_g[room_id]["past_guesses"][player_id].append(rooms_g[room_id]["guesses"][player_id])
                rooms_g[room_id]["guesses"][player_id] = ""
            
            game_is_over = update_with_gameover(room_id)
            
            # any client can know if the game is over by just checking whether the past guesses are 6 or one is correct
            assert len(rooms_websockets_g[room_id]) == 2
            for i in range(2):
                await rooms_websockets_g[room_id][i].send_text(json.dumps(rooms_g[room_id]))
            
            # The players should know the game is over and we can close the socket
            if game_is_over:
                print("game is over, disconnecting!")
                return
            
    except Exception as e:
        # debugging situations :/
        print(f"FAIL in websocket handler with error `{e}`")
        print("************** GAME STATES BELOW ************")
        pprint(rooms_g)
        print("************** PLAYER ROOMS BELOW ************")
        pprint(player2rooms_g)
    finally:
        # TODO we will want to figure out how to do some cleanup here
        # I think we could technically just use the room_id we got at the very beginning but that seems highly shitty...
        # I guess everything about this is shitty though
        return