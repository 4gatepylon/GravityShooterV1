# (Original/Deprecated, not checked if up to date) High level view of the backend
You connect to `server.py` which should be hosted somewhere using HTTP to request a group to join.

We will store a queue in a DB. If the DB is non-empty, then we will remove the first person we find and
they will be our pvp opponent. Two 5-letter words will be generated from a dictionary to be the hidden
words for each player.

If you have a pvp opponent, you'll also recieve an ID, which you should store. You will then connect using websockets to the
`ingame_server.py` script. Because we don't handle security, anyone can connect with a websocket. However, if a wrong
ID is passed then nothing will happen or an error will be returned. (Later we can use ID for security.)

Whenever `ingame_server.py` receives a valid websocket message, it will update all other valid connections with the updated
state of the game. The state of the game should include
- The two player names
- The two player ids
- The two player guesses array
- The two player current ongoing guesses
- The two player's hidden words (each player will recieve a unique word)
- Whether the game is over
- The game ID

The possible things a player can send across a websocket are
- Change in letter(s) (right after a player changes their current guess by adding or removign a letter)
- Change in submittal of current guess (right after a player guesses the thing they had)

For each of these the player will send an enum value for which one it is as well as a copy of the game
state. The server is assumed to have the same state, though it will broadcast the new updated state. (We
will just assume that everything is always in sync for now.)

# Sidenote
For future projects we should use `https://socket.io/` because it seems to make life way easier.