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
- RT in NA is around 45ms, definately above 20ms on average (https://www.verizon.com/business/terms/latency/ and LOL experience)
- Transmission error rate is under 99.5% (according to the same source)
- From the above, we know that ERT is at most 48ms (geometric random variable)
- To get 60 FPS we need 0.016s = 16ms ERT + PT
- It is possible to get at most 20 FPS without optimizing (i.e. server sends data every 48ms and it arrives at the client, who is playing 48ms behind)

## How can we get 60 FPS performance?