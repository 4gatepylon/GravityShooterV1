import React, { createContext, useState, ReactNode, useEffect } from "react"

// As of May 31, 2023 we only support circles for all objects. There are (1) players
//
// Welcome page:
// 1. Declare your name
// 2. Move over to lobby
//
// Lobby:
// 1. List of games that are not over and not full (i.e. only a single player)
// 2. If you click on a game you join it and it permanently disappears from the lobby
// 3  If the person in a game leaves (only way is by closing your browser, unless they win in which
//   case this rule won't apply) then the game is removed from the lobby.
//
// Game Page:
//
// Aesthetics:
// 1. Players are blue and green respectively. They are medium circles.
// 2. Stars are opaque (most opaque = white, less opaque = somewhat more black) and on a black background.
//   They are medium-sized circles of random sizes for every game.
// 3. Bullets are red and are small circles.
//
// Kinematics and control:
// 1. Stars' mass exerts a force on the bullets, but not players. However, bullets do NOT
//   exert a force on stars or eachother (and players don't either). Stars are unmoving. They are simply
//   field emitters and the fields can be precomupted.
// 2. Players cannot intersect with stars
// 3. Players are massless and move at a constant velocity which is a step function of whether
//    they are pressing the movement keys.
// 4. Shoot bullets by aiming towards mouse up-click.
// 5. Move character with WASD.
//
// Absorption and innteractions:
// 3. Stars and players both perfectly absorb bullets
// 4. A player who absorbs any bullet immediately dies and thus disappears
// 5. Bullets that go off the map disappear
// 6. Bullets that hit a player disappear
//
// Winning and Game States
// 1. Last player alive wins
// 2. Game ends when last player is alive, you need to go to the main menu and create or join a game, there will be a link to go back
//

interface Vector2 {
    x: number,
    y: number
}

type ObjectType = "player" | "star" | "bullet"
type ShapeType = "circle"
type ShapeParams = CircleParams

class CircleParams {
    public radius: number;
    public color: string;
    constructor(radius: number, color: string) {
        this.radius = radius;
        this.color = color;
    }
}

class ObjectShape {
    public type: ShapeType = "circle";
    private params: ShapeParams;
    constructor(params: ShapeParams) {
        this.params = params
    }
    public radius(): number {
        if (this.type == "circle") {
            return this.params.radius
        } else {
            throw new Error("Unsupported shape type")
        }
    }
    public volume(): number {
        if (this.type == "circle") {
            return Math.PI * this.params.radius * this.params.radius
        } else {
            throw new Error("Unsupported shape type")
        }
    }
    public color(): string {
        if (this.type == "circle") {
            return this.params.color
        } else {
            throw new Error("Unsupported shape type")
        }
    }
}

class Object {
    static readonly PLAYER_RADIUS   = 10;
    static readonly MIN_STAR_RADIUS = 10;
    static readonly MAX_STAR_RADIUS = 30;
    static readonly BULLET_RADIUS   = 5;
    static readonly PLAYER_DENSITY   = 1;
    static readonly MIN_STAR_DENSITY = 1;
    static readonly MAX_STAR_DENSITY = 10;
    static readonly BULLET_DENSITY   = 1;
    static readonly STAR_NORMALIZED_DENSITY_FUNC = (density: number) => density/(Object.MAX_STAR_DENSITY - Object.MIN_STAR_DENSITY);
    static readonly STAR_COLOR = "white";
    static readonly BULLET_COLOR = "red";
    static readonly PLAYER1_COLOR = "blue";
    static readonly PLAYER2_COLOR = "green";

    public id: string;
    // We only support a constant density for now, in the future this could be replaced by
    // a function-like object that takes in a position and returns a density.
    public density: number;
    // We use "normalized-density" to give us a number between 0 and 1 which will be used
    // to choose what opacity to give objects.
    private normalizedDensityFunc: (density: number) => number;

    public location: Vector2;
    public velocity: Vector2;
    public type: ObjectType;
    public shape: ObjectShape;
    constructor(
        id: string,
        location: Vector2,
        velocity: Vector2,
        type: ObjectType,
        player1: boolean = false
    ) {
        this.id = id;
        this.location = location;
        this.velocity = velocity;
        this.type = type;
        this.density = this.type == "player" ? Object.PLAYER_DENSITY : (
            this.type == "star" ? Object.MIN_STAR_DENSITY : Object.BULLET_DENSITY
        );

        // All objects have opacity one except for stars
        this.normalizedDensityFunc = this.type == "star" ? Object.STAR_NORMALIZED_DENSITY_FUNC : (density: number) => 1;

        const color = this.type == "player" ? (player1 ? Object.PLAYER1_COLOR : Object.PLAYER2_COLOR) : (
            this.type == "star" ? Object.STAR_COLOR : Object.BULLET_COLOR
        );
        const radius = this.type == "player" ? Object.PLAYER_RADIUS : (
            this.type == "star" ? Object.MIN_STAR_RADIUS : Object.BULLET_RADIUS
        );
        this.shape = new ObjectShape(new CircleParams(radius, color));
    }

    public noramlizedDensity(): number {
        return this.normalizedDensityFunc(this.density)
    }
}

// Player, Bullet, and Star are just convenience classes tbh
class Player extends Object {
    public name: string;
    public dead: boolean;
    constructor(
        id: string,
        name: string,
        location: Vector2,
        velocity: Vector2,
        dead: boolean = false
    ) {
        // When you construct a game you need to give the players the ids
        // 1. "player1"
        // 2. "player2"
        // And then everything else should just be an arbitrary unique id, i.e.
        // "1", "2", ... "12", ... "a1", ..
        super(id, location, velocity, "player", id == "player1");
        this.name = name;
        this.dead = dead;
    }
}

class Bullet extends Object {
    constructor(
        id: string,
        location: Vector2,
        velocity: Vector2,
    ) {
        super(id, location, velocity, "bullet");
    }
}

class Star extends Object {
    constructor(
        id: string,
        location: Vector2,
        velocity: Vector2,
    ) {
        super(id, location, velocity, "star");
    }
}

// TODO convert these to classes

interface GameContext {
    over: boolean
    winner: string

    // All these three are lists of objects, but only bullets will follow
    // physical laws.
    players: Array<Player>
    stars: Array<Object>
    bullets: Array<Object>
    // A field can be used to precompute the "voltage" (if this makes any sense) at every point to some granularity level,
    // where we assume the granularity is simply the number of squares in the square grid for the field (NOTE we assume that
    // the map is square). Thus, if we have N x N pixels and M granularity, it means that we have N / M pixels sharing the
    // same field value.
    //
    // The "voltage" is a vector that is gotten by taking G * M / r^2 r_hat summed over all stars (vector addition) where
    // r_hat is a unit vector pointing inwards to the star and r is the literal distance.
    field?: Array<Array<Vector2>>
    fieldGranularity?: number
}

interface LobbyContext {
}


// Dummy default that is not used to make Typescript not yell at us
const defaultContext: ContextIF = {
    gotMatch: false,
    gotName: false,
    thisPlayerName: "",
    thisPlayerId: "",
    otherPlayerName: "",
    otherPlayerId: "",

    // Key game state information
    isGameOver: false,
    winner: "",

    // Player-specific information
    guess: (player: string) => "",
    pastGuesses: (player: string) => [],
    secretWord: (player: string) => "",

    // Modify pre-game
    getName: (playerName: string) => {},
    getMatch: () => {},

    // Modify in-game
    guessLetter: (letter: string) => {},
    guessWord: () => {},
    backspaceLetter: () => {},
}

// Context for the guesses that we are making
export const Context = createContext<ContextIF>(defaultContext);

// Game state object interface mirroring that documented on the server
export interface GameStateIF {
    player_ids: Array<string>,
    player_names: {
        [key: string]: string
    },
    room_id: string,
    guesses: {
        [key: string]: string
    },
    past_guesses: {
        [key: string]: Array<string>
    },
    secret_words: {
        [key: string]: string
    },
    is_right: {
        [key: string]: boolean
    }
    game_over: boolean,
    winner: string
}

// Necessary apparently to help Typescript stop yelling at us
interface ContextProviderIF { children: ReactNode }
interface EventWithDataIF { data : any }
// Context provider is a REact context prover (something wrap around the things
// in which you want to get some hooks from useContext calls with)
export function ContextProvider(props: ContextProviderIF) {
    // These are dummy initial values
    const [thisGameState, setThisGameState] = useState<GameStateIF>({
        "player_ids": ["", "_"],
        "room_id": "",
        "guesses": {
            "": "",
            "_": "",
        },
        "player_names": {
            "": "",
            "_": ""
        },
        "past_guesses": {
            "": [],
            "_": []
        },
        "secret_words": {
            "": "trees",
            "_": "hellp"
        },
        "is_right": {
            "": false,
            "_": false
        },
        "game_over": false,
        "winner": "none"
    })
    const [thisPlayerName, setThisPlayerName] = useState("")
    const [thisPlayerId, setThisPlayerId] = useState("")
    const [thisRoomId, setThisRoomId] = useState("")

    // NOTE: because there is no conditional rendering for this, this should
    // automatically connect to the websocket upon starting the application
    const SERVER_URL = "ws://127.0.0.1:8000/ws"
    const [socket, _] = useState(new WebSocket(SERVER_URL))

    // Register handlers for the websocket reading
    const DEBUG = true
    const CREATION = "CREATION"
    const GAME_STATE = "GAME_STATE"
    useEffect(() => {
        socket.onmessage  = function(event: EventWithDataIF) {
            // It comes in as a string
            const response = JSON.parse(event.data);
            if (DEBUG) {
                console.log(`received a message!\n${JSON.stringify(response)}`);
            }
            if (response !== undefined) {
                if (response.type == GAME_STATE) {
                    setThisRoomId(response.data["room_id"])
                    setThisGameState(response.data)
                } else if (response.type == CREATION) {
                    // Debug please remove...
                    console.log(`Setting player id to ${response.data["player_id"]}`)
                    console.log(`thisPlayerName is ${thisPlayerName}`)
                    // ...
                    setThisPlayerId(response.data["player_id"])
                } else {
                    // Do nothing, we don't actually respond to any other type of response from
                    // the server (errors are ignored)
                }
            }             
        }
    }, [])

    // For displaying the children
    const children = props.children;

    // (Per the documentation on the server)
    // Creates requests of one of the following types:
    const CREATE = "CREATE"
    const JOIN = "JOIN"
    const LETTER = "LETTER"
    const GUESS = "GUESS"
    const BACKSPACE = "BACKSPACE"
    function createSerializedRequest(request_type: string, request_data: any): string {
        if (
            request_type != CREATE &&
            request_type != JOIN &&
            request_type != LETTER &&
            request_type != BACKSPACE &&
            request_type != GUESS
        ) {
            console.log(`ERROR: tried to make a request of a non-supported type ${request_type}, please look at code`)
            return ""
        } else {
            let req = JSON.stringify({
                "type" : request_type,
                "data" : request_data
            })
            console.log(`SENDING ${req}`)
            return req
        }
    }
    const otherPlayerId = thisGameState["player_ids"].filter((id: string) => id != thisPlayerId)[0]
    return (
        // Store the values that we want to be able to extract from
        // `useContext` inside the `value` element
        // Forced to inline the value because otherwise we get type issues
        <Context.Provider 
            value = {{
                gotMatch: thisRoomId != "",
                gotName: thisPlayerName != "",
                thisPlayerName: thisGameState["player_names"][thisPlayerId],
                thisPlayerId: thisPlayerId,
                otherPlayerName: thisGameState["player_names"][otherPlayerId],
                otherPlayerId: otherPlayerId,
        
                // Key game state information
                isGameOver: thisGameState["game_over"],
                winner: thisGameState["winner"],
        
                // Player-specific information
                guess: (player: string) => thisGameState["guesses"][player],
                pastGuesses: (player: string) => thisGameState["past_guesses"][player],
                secretWord: (player: string) => thisGameState["secret_words"][player],
        
                // Modify pre-game
                getName: (playerName: string) => {
                    setThisPlayerName(playerName)
                    const req = createSerializedRequest(CREATE, { "player_name": playerName })
                    socket.send(req)
                },
                getMatch: () => {
                    const req = createSerializedRequest(JOIN, { "player_id": thisPlayerId })
                    socket.send(req)
                },
        
                // Modify in-game (request, note that we only modify once we receive a broadcast from the server, basically...)
                // NOTE: this could could be made shorter and should
                guessLetter: (letter: string) => {
                    const req = createSerializedRequest(LETTER, {
                        "player_id": thisPlayerId,
                        "room_id": thisRoomId,
                        "letter": letter
                    })
                    socket.send(req)
                },
                guessWord: () => {
                    const req = createSerializedRequest(GUESS, {
                        "player_id": thisPlayerId,
                        "room_id": thisRoomId,
                    })
                    socket.send(req)
                },
                backspaceLetter: () => {
                    const req = createSerializedRequest(BACKSPACE, {
                        "player_id": thisPlayerId,
                        "room_id": thisRoomId,
                    })
                    socket.send(req)
                },
            }}>
            {children}
        </Context.Provider>
    );
}