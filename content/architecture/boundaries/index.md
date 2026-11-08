+++
title = 'Service boundaries'
date = '2026-11-08T06:13:46Z'
+++

Where a system is split decides how much its parts depend on each other. Two measures describe a split, both from Larry Constantine's work on structured design and published by Wayne Stevens, Glenford Myers, and Constantine in 1974. Coupling is how much one part depends on another: with loose coupling, one part can change without the others changing too. Cohesion is how closely the things inside one part belong together: with high cohesion, code that changes together sits together. [Microservices]({{< ref "/architecture/microservices" >}}) aim for loose coupling between services and high cohesion inside each one. The practical test is independent deployability: a change to one service can be released on its own, without releasing any other.

## Split by technical layer

A common design is the three-tier architecture, split by technical function: a presentation tier for the web UI, a business logic tier for the backend, and a data tier for the database. Teams often follow the same split. A frontend team owns the UI, a backend team owns the business logic, and database administrators (DBAs) own the database. Each tier is cohesive in a technical sense: all the UI code is in one place, and all the SQL is in another.

A business change cuts across all three. Adding a gift wrap option to orders needs a new option on the order screen, a price rule in the business logic, and a new column in the orders table:

![Three stacked tiers, each owned by one team. The frontend team owns the web UI and presentation for orders, payments, and shipping. The backend team owns the business logic for orders, payments, and shipping. The DBAs own the database: orders, payments, and shipping tables. One change, adding gift wrap, touches all three tiers: the orders UI, the orders logic, and the orders table each gain gift wrap.](layers.svg)

Three teams have to plan, build, and release that change together, and each tier's release waits for the others. James Lewis and Martin Fowler describe the result: "even simple changes can lead to a cross-team project taking time and budgetary approval."

## Split by business capability

Microservices split along business capabilities instead, such as orders, payments, and shipping. Each service holds all the layers for its capability, its own UI or API, logic, and data, and one cross-functional team owns it. Code that changes together for a business reason sits in one service: microservices prioritize high cohesion of business functionality over high cohesion of technical functionality.

![Three vertical slices, one per team. The orders team owns the orders UI, orders logic, and orders data, and the gift wrap change lands in all three. The payments team owns the payments UI, logic, and data. The shipping team owns the shipping UI, logic, and data.](capabilities.svg)

The same gift wrap change now stays inside the orders service. One team makes it and releases it, and payments and shipping don't change. This mirrors Conway's law, Melvin Conway's 1968 observation that systems copy the communication structure of the organizations that design them: draw the teams around business capabilities, and the services follow.

## Finding the boundaries with domain-driven design

Domain-driven design (DDD), named by Eric Evans in his 2003 book, is the usual method for finding business boundaries. It builds the software around a model of the business domain, worked out with the people who know the business, and carries their words, called the ubiquitous language, into the code. Its key idea for boundaries is the bounded context: a large system can't share one model, because words like "customer" or "product" mean different things in different parts of the business. To sales, a customer is a lead with contact history; to billing, it's an account with a payment method. DDD splits the system into bounded contexts, each with one consistent model and language, and a bounded context is a natural candidate for a service.

## What keeps services loosely coupled

- Own data. Each service keeps its own database, and others reach it only through the service's API. A shared database couples every service that reads a table to that table's design.
- Stable contracts. A service changes its API in backward-compatible ways, such as adding fields instead of renaming them, so callers don't have to change at the same time.
- Events instead of calls where possible. A service that announces "order placed" doesn't need to know who listens, or wait for them.

## What breaks it

- A shared database, so one team's schema change breaks another team's service.
- Chains of synchronous calls, so one slow service slows every service that calls it. See [Distributed systems]({{< ref "/architecture/distributed-systems" >}}).
- Releasing services together. If two services must always be deployed at the same time, they aren't independent, whatever their code looks like.
- A shared library holding business logic, so a change to it means updating and releasing every service that uses it.

References: [Domain-driven design](https://martinfowler.com/bliki/DomainDrivenDesign.html), [Bounded context](https://martinfowler.com/bliki/BoundedContext.html), [Structured Design (Stevens, Myers, and Constantine, 1974)](https://doi.org/10.1147/sj.132.0115), [Microservices, by James Lewis and Martin Fowler](https://martinfowler.com/articles/microservices.html), [How Do Committees Invent? (Conway, 1968)](https://www.melconway.com/Home/Committees_Paper.html)
