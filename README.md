# GravityShooterV1
A little gravity shooter to play with your friends in the browser, projectiles are bent by planets and you die when hit by projectile.

# Important Performance Notes - Latency and FPS
## Definitions and Declarations
- Frames per second, or how many different images can be displayed, changing, over the course of a second, is called FPS
- Round trip time of a packet defines RT
- Processing time of all computation on the server defines PT
- There is one server and multiple clients connected by websockets WS over TCP
- As a first order model, TCP requires a packet to be sent and then acknowledged until the next packet can be sent, we call this the proper "tranmission" of a package (tranmission requires the acknowledgement as well). That is why we care about round-trip time. Moroever, we say that in TCP if transmission fails, it will be attempted again.
- Call ERT the expected RT including failures for any single packet.
- We want the highest possible FPS
- We want to minimize the expected ERT over all possible error sequences (i.e. Error, Error, No Error) because we will be sending many packages. Due to Chernoff (applicable here) we expect w.h.p. any proportion o the packets (i.e. 90%) to be close to the expected ERT.
- We assume that processing is instant on the Client

## Data and Conclusions
- RT in NA is around 45ms, definately above 20ms on average (https://www.verizon.com/business/terms/latency/, LOL experience, `ping google.com`)
- Transmission error rate is under 99.5% (according to the same source)
- From the above, we know that ERT is at most 48ms (geometric random variable)
- To get 60 FPS we need 0.016s = 16ms ERT + PT
- It is possible to get at most 20 FPS without optimizing (i.e. server sends data every 48ms and it arrives at the client, who is playing 48ms behind)
- If we can't get 60 FPS we want to at least get 30 FPS because below that the eye can tell (https://www.healthline.com/health/human-eye-fpshttps://www.healthline.com/health/human-eye-fps)

### Other Data
- Human reaction time is close to 250ms (https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4456887/)
- A 48ms, close to 50ms, delay is going to remain playable but not look so smooth

## How can we get 60 FPS performance?
- If we decrease time to be single-trip then we can achieve under 23ms performance, which is enough for roughly 45 FPS. Maybe this is already OK since the game state will propagate?
- If we set up a UDP server we can get slightly better performance
- Avoid encryption (etc)... decrease processing time
- WebRTC? It has a Data Channel: https://webrtc.org/getting-started/data-channels?hl=en
- Host on a nearby VM (i.e. close to Praveen, Sagar, Edgar, and I)

Do we even need to really increase performance? By how much?

## To Figure Out How To Increase Performance We'll Need to Benchmark
### Benchmark #1: Sliding Rectangle Over WS
- On button clicks send request to server to change location of rectangle
- Server is streaming current location of rectangle
- Client displays based on server location

Goal of the first benchmark is to understand whether it is possible to create an object that stays in sync with controls AND moves smoothly. If this works, then we are done and can just proceed to build the gane,