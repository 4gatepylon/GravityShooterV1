# Boilerplate from
# https://fastapi.tiangolo.com/advanced/websockets/
# Run with
#  `uvicorn server:app --reload`
# 
# Test if this is running using netcat (https://www.cyberciti.biz/faq/linux-port-scanning/):
#  `nc -z -v localhost 8888`

from __future__ import annotations

from pprint import PrettyPrinter
pp = PrettyPrinter()
pprint = lambda x: pp.pprint(x)

from fastapi import FastAPI, WebSocket, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from game import GameManager, MessageHandler


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
# Deal with debugging

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
# Game state (global) and logic
# You basically initially connect to the WebSocket
# and send your name in a CREATE request
# (all messages go through websockets and all messages have the form declared in game.py, i.e.
# is one of the message types)

gm = GameManager()
handler = MessageHandler(gm)

# This is just an easy way to deal with the wrong shit being sent
FMT_ERR_MSG = lambda err_msg: (
    f"ERROR: bad format on input message, please read the docs. The server-side exception was {err_msg}"
)

# Some example mesaages we can try and send via postman
# This should be quite useful for debugging!
"""
A Create message (just copy):
{
  "type": "CREATE",
  "data": {
      "player_name": "player1"
  }
}

A Join message (replace placeholders and then copy):
{
    "type": "JOIN",
    "data": {
        "player_id": _
    }
}

A guess message (replace placeholders and then copy):
{
    "type": "GUESS",
    "data": {
        "player_id": _,
        "room_id": _
    }
}

A letter message (replace placeholders and then copy):
{
    "type": "LETTER",
    "data": {
        "player_id": _,
        "room_id": _,
        "letter": _
    }
}

A backspace message (replace placeholders and then copy):
{
    "type": "BACKSPACE",
    "data": {
        "player_id": _,
        "room_id": _
    }
}
"""

# This is copied from here:
# https://fastapi.tiangolo.com/advanced/websockets/
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global handler
    
    await websocket.accept()

    keep_open = True
    while keep_open:
        request = await websocket.receive_text()
        try:
            await handler.handle(request, websocket)
        except Exception as e:
            print(f"ERROR:\n{e}")
            await websocket.send_text(FMT_ERR_MSG(e))

        # NOTE there is a bug here where we will keep open the opponent's
        # socket by accident...
        keep_open = handler.keep_open(websocket)
            
