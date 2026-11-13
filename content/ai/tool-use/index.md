+++
title = 'Tool use'
date = '2026-11-08T19:05:56Z'
+++

Tool use, also called function calling, lets a {{< term llm >}} ask the application around it to run a function and send back the result. A model only produces text. It can't search the web, query a database, or send an email by itself, and its weights hold no facts newer than its training. Tool use keeps the model producing text but gives some of that text a fixed shape: a request to call a named function with given arguments. The application runs the function, and the model reads the result and continues.

Tool use has four parts:

- Tool definition: a name, a description, and a JSON Schema for the arguments, sent with each request.
- Tool call: a block in the model's reply naming the tool and giving arguments that fit the schema.
- Tool result: the function's output, sent back to the model in the next request.
- Loop: the application repeats call, run, and return until the model replies without a tool call.

![A sequence diagram. The user asks the application whether more items sold in May or June. The application sends the question to the LLM with the definition of items_sold. The LLM replies with two calls, items_sold for 2025-05 and items_sold for 2025-06. The application runs the function twice, which returns 11 and then 10, and sends both results back to the LLM. The LLM answers May, 11 against 10, and the application passes the answer to the user.](loop.svg)

## Defining a tool

A tool definition tells the model what a function does and what arguments it takes. The model never sees the function's code, only this definition, so the description decides when the model calls the tool. The input schema is JSON Schema, the same format used to validate JSON elsewhere. This definition is in the format of Anthropic's Messages API; OpenAI's and Google's APIs use the same three parts under slightly different field names.

```json
{
  "name": "items_sold",
  "description": "Items sold in one month. Use it for sales volume questions.",
  "input_schema": {
    "type": "object",
    "properties": {
      "month": {
        "type": "string",
        "description": "Month as YYYY-MM, e.g. 2025-05"
      }
    },
    "required": ["month"]
  }
}
```

The function behind it is ordinary code. This one queries a small SQLite table of sales, and passes the month as a query parameter rather than pasting it into the SQL:

```python
def items_sold(month):
    (n,) = db.execute(
        "SELECT COALESCE(SUM(qty), 0) FROM sales "
        "WHERE substr(sold_on, 1, 7) = ?",
        (month,),
    ).fetchone()
    return {"month": month, "items_sold": n}
```

Run on that table, it returns 11 for 2025-05 and 10 for 2025-06.

## One round trip

The application sends the user's message with the tool definitions. When the model decides to use a tool, its reply ends with the stop reason `tool_use` and contains one `tool_use` block per call. A model can make several calls in one reply, called parallel tool calls, when they don't depend on each other:

```json
{
  "role": "assistant",
  "stop_reason": "tool_use",
  "content": [
    {"type": "tool_use", "id": "toolu_01", "name": "items_sold",
     "input": {"month": "2025-05"}},
    {"type": "tool_use", "id": "toolu_02", "name": "items_sold",
     "input": {"month": "2025-06"}}
  ]
}
```

The application runs each call and sends every result back in one message. Each `tool_result` carries the `id` of the call it answers:

```json
{
  "role": "user",
  "content": [
    {"type": "tool_result", "tool_use_id": "toolu_01",
     "content": "{\"month\": \"2025-05\", \"items_sold\": 11}"},
    {"type": "tool_result", "tool_use_id": "toolu_02",
     "content": "{\"month\": \"2025-06\", \"items_sold\": 10}"}
  ]
}
```

The ids are shortened here. The model now has both numbers and answers in text, with the stop reason `end_turn`, which ends the loop. Each request carries the whole conversation so far, including earlier calls and results, because the model keeps no state between requests.

## Errors and control

- Failed calls: when a function fails, its result is sent back marked as an error, with the message, such as `is_error: true` in Anthropic's API. The model can then retry with other arguments or tell the user.
- Tool choice: a request setting decides whether the model may call tools. `auto` lets it choose, and `none` turns tools off for that request. Some models also accept a setting that forces a call to a named tool.
- Round limit: the application caps the number of rounds, so a model that keeps calling tools can't loop forever.

## Where tools run

- Client tools run in the application, as in the example above. The application owns the code, the credentials, and the decision to run each call.
- Server tools run on the model provider's servers, such as web search or code execution offered by the API itself. The application declares them, and their results arrive in the same reply without a round trip through its own code.

## Model Context Protocol

Every application used to define its own tools in its own code. The Model Context Protocol (MCP), published by Anthropic in November 2024, is an open standard that lets one program offer tools to any application that speaks it. It is built on JSON-RPC, a format for sending requests and responses as JSON:

- Host: the application the user works in, such as a chat app or a coding agent. It talks to the model and decides what runs.
- Client: a connection inside the host, one per server.
- Server: a separate program that offers tools, such as access to files or a database. It can run on the same machine or remotely.

![A host, such as a chat app or coding agent, holds a connection to the LLM and two MCP clients. Client 1 connects to an MCP server for files and git, and client 2 connects to an MCP server for a sales database. Each client sends tools/list and tools/call to its server.](mcp.svg)

The client asks a server for its tools with `tools/list`, and the server answers with definitions that hold a name, a description, and an `inputSchema`, the same three parts as above. When the model calls one of them, the client sends `tools/call` with the name and arguments, and the server returns the result. The host passes the definitions to the model and the results back to it, as in any tool loop.

## Risks

- Untrusted results: a tool result goes into the model's context as text, and the model can follow instructions written in it. Greshake et al. (2023) showed attacks that plant instructions in web pages and emails that an application later retrieves, called indirect prompt injection.
- Side effects: a tool that sends email, moves money, or deletes data acts in the world. The MCP specification says there "SHOULD always be a human in the loop with the ability to deny tool invocations," with confirmation prompts for such operations.
- Arguments as input: arguments come from the model, so the function validates them like any outside input. The `items_sold` function above passes the month as a query parameter, so a strange argument can't change the SQL.

## How it developed

- 2022, [ReAct](https://arxiv.org/abs/2210.03629) (paper). Models wrote reasoning steps and actions in turn, reading each action's result before the next step.
- 2023, [Toolformer](https://arxiv.org/abs/2302.04761) (paper). A model trained itself to insert calls to a calculator, search engines, a translator, and a calendar.
- 2023, [Function calling](https://openai.com/index/function-calling-and-other-api-updates/) (product, OpenAI, June). Tool definitions as JSON Schema in the API, with calls returned as structured data.
- 2024, [Model Context Protocol](https://www.anthropic.com/news/model-context-protocol) (standard, Anthropic, November). One protocol for offering tools to many applications.

Tool use is the base of the other [agentic design patterns]({{< ref "/ai/agentic-patterns" >}}): planning chooses which tools to call, and [external feedback]({{< ref "/ai/external-feedback" >}}) often arrives as a tool result.

References: [Tool use (Anthropic docs)](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview), [Function calling (OpenAI docs)](https://developers.openai.com/api/docs/guides/function-calling), [MCP specification: tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools), [MCP specification: architecture](https://modelcontextprotocol.io/specification/2025-06-18/architecture), [Not what you've signed up for (Greshake et al., 2023)](https://arxiv.org/abs/2302.12173), [JSON Schema](https://json-schema.org/)
