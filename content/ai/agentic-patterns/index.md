+++
title = 'Agentic design patterns'
date = '2026-11-08T18:27:04Z'
+++

An agentic workflow is an application that completes a task through several steps with a {{< term llm >}}, instead of one prompt and one reply. A single reply has to be right on the first pass, with only what the model already knows. Splitting the work into steps lets the application check a draft, fetch facts, run code, and hand parts of the task to differently prompted calls. Anthropic draws a line inside this: in a workflow, "LLMs and tools are orchestrated through predefined code paths"; in an agent, "LLMs dynamically direct their own processes and tool usage."

![Three stages from left to right in control. One call: prompt in, reply out. Add steps, checks, and tools, and it becomes a workflow, where the developer fixes the steps in code. Let the model decide the steps, and it becomes an agent, where the model chooses the next step.](overview.svg)

Four patterns cover most ways the steps are combined:

- Reflection: the model checks its own output and revises it.
- Tool use: the model calls functions that the application runs, such as web search or code execution.
- Planning: the model decides which steps to take, and in what order.
- Multi-agent collaboration: several model calls, each prompted with its own role, work on one task.

The patterns combine. A critic in reflection can be a second agent, and the check can be a tool that runs tests. Each pattern adds calls, so it adds cost and time, and the gain is measured with [evaluations]({{< ref "/ai/evals" >}}) on the real task.

## Reflection

Reflection feeds a model's output back to it with a request to find problems, then asks for a revision that fixes them. It takes three prompts, each sent in its own call. For code, the first prompt asks for a function. The second, the reflection prompt, contains that code and asks for a critique:

```text
Here is code intended for this task: remove duplicate emails
from a list, keeping the first of each.

<code from the first reply>

Check the code carefully for correctness, style, and efficiency,
and give constructive criticism for how to improve it.
```

The third, the revision prompt, contains the code and the critique and asks for a fixed version:

```text
Task: remove duplicate emails from a list, keeping the first of each.

Code:
<code from the first reply>

Feedback:
<critique from the second reply>

Rewrite the code so that it addresses the feedback.
```

The reflection prompt alone is an ordinary [single-call prompt]({{< ref "/ai/prompting" >}}). Reflection is the loop around it, with the critique going into the revision. The same model often finds mistakes in a draft that it didn't avoid while writing it.

![A loop. A task, write a function, goes to the LLM, which writes or revises the code. The code, version 1, version 2, and so on, goes to a check: an LLM critique or running the tests. The check sends a critique or test errors back to the LLM. When no issues are left, or a round limit is reached, the final code comes out.](reflection.svg)

The feedback gets better when it comes from outside the model. Running the code and returning the error message, or the failing unit tests, gives the model facts instead of opinions. Self-Refine (2023) used one model to write, critique, and revise, and reported scores about 20 percentage points higher on average than [zero-shot]({{< ref "/ai/prompting" >}}) output, the model's first answer, across seven tasks. Reflexion (2023) added test results and kept the model's written reflections across attempts, and reported 91% pass@1 on the HumanEval coding benchmark, against 80% for GPT-4 alone. Reflection doesn't fix every error: a model can miss its own mistakes, or approve a wrong answer.

## Tool use

A tool is a function that the application offers to the model, described by a name, a purpose, and its parameters. The model doesn't run anything itself. It replies with a tool call, the function's name and arguments, and the application runs the function and sends the result back as more text. The model then continues, either with another call or with the answer. Choosing which tool to call, and when, is the model's part.

![A sequence diagram. The user asks the application what 100 dollars at 5% a year for 10 years becomes. The application sends the question to the LLM with a tool list holding run_python. The LLM replies with a call to run_python with the code print(100 * 1.05 ** 10). The application runs the code in a code runner, which returns 162.8894626777442. The application sends the result to the LLM, which answers about 162.89 dollars, and the application passes that to the user.](tools.svg)

Tools give a model what its weights can't hold: current facts through web search, exact arithmetic through code, private data through database queries, and actions through email or calendar APIs. Toolformer (2023) trained a model to insert calls to a calculator, a search engine, a translator, and a calendar. Model APIs now take a list of tool definitions with each request. The Model Context Protocol (MCP), published by Anthropic in 2024, is a standard way for an application to offer tools from separate servers.

## Planning

In planning, the model writes the sequence of steps, instead of the developer writing them in code. HuggingGPT (2023) shows it with four stages: an LLM plans the subtasks for a request, picks a model from Hugging Face for each one by its description, runs them, and summarizes the results. Asked for an image of a girl reading a book in the same pose as a boy in a photo, then a spoken description, it plans four steps, each using the output of the one before.

![A request: an image of a girl reading, in the same pose as the boy in boy.jpg, then describe it aloud. The LLM plans the steps and picks a model for each. Step 1, pose detection on boy.jpg, passes the pose to step 2, pose-to-image, a girl reading a book. It passes the image to step 3, image-to-text, which captions the new image. It passes the caption to step 4, text-to-speech, which reads the caption. The audio goes back to the LLM, which sums up the results for the user.](planning.svg)

ReAct (2022) plans one step at a time instead of all at once: the model writes a short reasoning step, takes an action, reads the result, and updates its plan. Because the steps aren't known before the run, a planning agent is harder to test and to keep within bounds than a fixed workflow.

## Multi-agent collaboration

In multi-agent collaboration, an agent is an LLM call with its own role prompt, and often its own tools. Several agents pass work between them, as people with different jobs do. A marketing brochure can go to a research agent with a web search tool, then a marketer agent that writes the copy, then an editor agent that sends changes back or approves it. The agents can all be the same model; the role prompt is what differs.

![A task, a marketing brochure, goes to a research agent with a web search tool. It passes findings to a marketer agent, which writes the copy. The marketer passes a draft to an editor agent, which polishes the text. The editor either sends changes requested back to the marketer, or passes the approved brochure out.](agents.svg)

ChatDev (2023) runs a simulated software company, with agents in roles such as CEO, CTO, programmer, and reviewer, through designing, coding, testing, and documenting. Multiagent debate (2023) has several instances of one model answer, read each other's answers, and revise over a few rounds; it made biographies more factual and chess moves more often valid. The order in which agents talk is set either by the developer or by the agents, and the second is harder to predict.

## Other names

Anthropic's "Building effective agents" names five workflow patterns that overlap with these four:

- Prompt chaining: a fixed sequence of calls, each working on the last one's output.
- Routing: one call sorts the input and sends it to a specialized prompt.
- Parallelization: several calls work at once, on separate parts or on the same question for a vote.
- Orchestrator-workers: one model splits the task and hands parts to others, which is planning combined with multiple agents.
- Evaluator-optimizer: one call writes and another judges, in a loop, which is reflection.

References: [Building effective agents (Anthropic, 2024)](https://www.anthropic.com/engineering/building-effective-agents), [Self-Refine (Madaan et al., 2023)](https://arxiv.org/abs/2303.17651), [Reflexion (Shinn et al., 2023)](https://arxiv.org/abs/2303.11366), [Toolformer (Schick et al., 2023)](https://arxiv.org/abs/2302.04761), [Model Context Protocol](https://modelcontextprotocol.io/), [HuggingGPT (Shen et al., 2023)](https://arxiv.org/abs/2303.17580), [ReAct (Yao et al., 2022)](https://arxiv.org/abs/2210.03629), [ChatDev (Qian et al., 2023)](https://arxiv.org/abs/2307.07924), [Multiagent debate (Du et al., 2023)](https://arxiv.org/abs/2305.14325)
