+++
title = 'Microservices'
date = '2026-11-08T05:46:21Z'
+++

Microservices are a way to build one application as a set of small services, each running as its own process, owning its own data, and deployed on its own. The services talk over the network, usually through HTTP APIs or messages. The alternative is a monolith: one program, built and deployed as a single unit, usually with one shared database. A monolith keeps calls between its parts cheap and simple. Microservices give up some of that simplicity so that each part can be changed, deployed, and scaled without touching the rest, which matters most when many teams work on one large system.

## Components

A microservice system has a few parts:

- Services, each built around one business capability, such as orders or payments, and owned by one team.
- A database per service. Other services read that data only through the owning service's API, never from its tables.
- An API gateway: the single entry point for outside clients, which routes each request to the right service.
- Communication between services, either a request and reply, such as HTTP or gRPC, or events sent through a message broker.
- A platform that runs and connects the services, such as containers on Kubernetes.

![A client calls an API gateway over HTTPS. The gateway routes requests to the users service and the orders service. The orders service sends a request to the payments service, and publishes an "order placed" event to a message broker, drawn dashed, which delivers it to the shipping service. Each of the four services has its own database.](overview.svg)

## Monolith and microservices

The same features can be built either way. The difference is where the boundaries are and what crosses them:

![On the left, a monolith: one application process holds orders, users, and payments modules, where orders calls payments by a function call, and all share one database. On the right, microservices: separate orders, users, and payments services, each with its own database, where orders calls payments by a network call.](compare.svg)

| | Monolith | Microservices |
|---|---|---|
| Unit of deployment | The whole application | One service |
| Call between parts | A function call in memory | A network call that can be slow or fail |
| Data | One shared database, joined freely | One database per service, combined through APIs |
| Scaling | Copies of the whole application | Copies of only the busy services |
| A crash | Stops the whole application | Stops one service; its callers must handle the failure |
| Consistency | One database transaction across parts | No transaction across services; data agrees eventually |

A network call can time out, arrive twice, or reach a service that has just restarted, none of which a function call does. So a microservice system is a [distributed system]({{< ref "/architecture/distributed-systems" >}}), and much of its machinery, such as retries, timeouts, and tracing, exists to handle that.

## Key terms

Structure:

- Service: a separately deployed program that does one job for the rest of the system, behind an API.
- Business capability: something the business does, such as taking orders or billing. Services are split along these, not along technical layers.
- Bounded context: the part of a system within which a model and its words have one meaning. A service's boundary often matches one.
- Modular monolith: a monolith split internally into modules with strict boundaries, deployed as one unit.
- Hexagonal architecture: a way to structure the inside of one service so its business logic doesn't depend on its database or framework. See [SOA and hexagonal architecture]({{< ref "/architecture/styles" >}}).

Communication:

- gRPC: a remote procedure call system that lets a program call methods on another machine as if they were local, using Protocol Buffers to define the interface and encode messages.
- Message broker: a server that receives messages from senders and delivers them to receivers, so the two needn't be running at the same time. Kafka and RabbitMQ are examples.
- Event: a message that something happened, such as "order placed". The sender doesn't know or wait for who receives it.
- Service discovery: how a service finds the current address of another. In Kubernetes, a [Service]({{< ref "/k8s/service" >}}) gives a set of pods one stable name and address.
- Service mesh: a layer of proxies, one beside each service, that handles retries, encryption, and metrics for all calls between services.

Data:

- Eventual consistency: data in different services may disagree for a while, then agree. See [Distributed systems]({{< ref "/architecture/distributed-systems" >}}).
- Saga: a long operation split into a sequence of local transactions, one per service. If a step fails, compensating transactions undo the steps before it.

Operations:

- Independent deployment: releasing a new version of one service without redeploying the others.
- Observability: being able to tell what a system is doing from its logs, metrics, and traces.
- Distributed tracing: following one request through every service it touches, with a shared ID passed along each call.
- Circuit breaker: a wrapper around remote calls that stops making them after repeated failures, so a failing service doesn't tie up its callers.

## Origins

- 1968: Melvin Conway observes that organizations which design systems produce designs that copy their own communication structures, later called [Conway's law](https://www.melconway.com/Home/Committees_Paper.html). Microservices apply it on purpose: one team per service.
- 2000s: [service-oriented architecture]({{< ref "/architecture/styles" >}}) (SOA) splits large systems into services joined by a central enterprise service bus.
- 2011–2012: software architects at a workshop near Venice discuss the style and settle on the name "microservices".
- 2014: James Lewis and Martin Fowler publish ["Microservices"](https://martinfowler.com/articles/microservices.html), which defines the style and its characteristics, such as "smart endpoints and dumb pipes": logic lives in the services, and the network only carries messages, unlike SOA's service bus.

References: [Microservices, by James Lewis and Martin Fowler](https://martinfowler.com/articles/microservices.html), [How Do Committees Invent? (Conway, 1968)](https://www.melconway.com/Home/Committees_Paper.html), [Bounded context](https://martinfowler.com/bliki/BoundedContext.html), [Circuit breaker](https://martinfowler.com/bliki/CircuitBreaker.html), [gRPC introduction](https://grpc.io/docs/what-is-grpc/introduction/)
