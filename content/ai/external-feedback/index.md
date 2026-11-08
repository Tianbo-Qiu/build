+++
title = 'External feedback'
date = '2026-11-08T19:01:22Z'
+++

External feedback is information about a model's output that comes from outside the model, such as an error message, a word count, or a search result. A {{< term llm >}} knows only what its weights hold and what its prompt contains. Asked to critique its own draft, as in [reflection]({{< ref "/ai/agentic-patterns" >}}), it reads the same draft with the same knowledge, so it can miss the same mistakes it made while writing. A check outside the model adds facts the model didn't have, and the revision can use them.

![Two loops side by side. Self-critique: a draft goes to the LLM, which critiques it with the same weights and the same prompt, and the revision has no new facts. External feedback: a draft goes to a check outside the LLM, which runs, matches, counts, or looks up, and the revision has new facts.](feedback.svg)

## What the research found

- Huang et al. (2023) tested models correcting their own reasoning with no outside input, and found that "LLMs struggle to self-correct their responses without external feedback." Their scores sometimes fell after the correction.
- CRITIC (Gou et al., 2023) had the model check its output with tools, a search engine for facts and a code interpreter for programs, and revise from what the tools returned. It improved results on question answering, math programs, and reducing toxic text.
- A survey by Kamoi et al. (2024) concluded that self-correction "works well in tasks that can use reliable external feedback," while no prior work showed it working with feedback from prompted LLMs alone, except on tasks unusually suited to it.

When tuning prompts or adding self-critique stops improving an application's [eval]({{< ref "/ai/evals" >}}) scores, a source of new facts can still raise them.

## Kinds of checks

- Run it: execute generated code and return its output, error message, or failing tests. Self-Debugging (Chen et al., 2023) and Reflexion (Shinn et al., 2023) work this way.
- Match it: search the output for text it must not contain, such as competitors' names, with a regular expression.
- Count it: measure the output against a limit, such as words or characters. Models write in tokens, not words, so code counts words more reliably than the model does.
- Look it up: compare a claim with a trusted source, through web search or a database.

A lookup example: a draft says the Taj Mahal was built in 1648. A search returns UNESCO's description, that it was built "between 1631 and 1648" by order of the Mughal emperor Shah Jahan. Given that text, the revision can give the full period instead of the end year.

## Turning checks into feedback

Each check returns a short message, and the messages go into the revision prompt. This Python check tests a sales email for two competitors' names and a 40-word limit:

```python
import re

COMPETITORS = ["Globex", "Initech"]
LIMIT = 40

def check(draft):
    problems = []
    for name in COMPETITORS:
        if re.search(rf"\b{name}\b", draft, re.IGNORECASE):
            problems.append(f"mentions the competitor {name}")
    words = len(draft.split())
    if words > LIMIT:
        problems.append(f"{words} words, limit {LIMIT}")
    return problems
```

On a draft that says "Unlike Globex, our kettles keep water hot for six hours…", it returns `['mentions the competitor Globex', '47 words, limit 40']`. The revision prompt then reads:

```text
Rewrite this email to fix these problems:
- mentions the competitor Globex
- 47 words, limit 40

<the draft>
```

The loop repeats until the check returns no problems, or a round limit is reached. An empty list is a fact, not the model's opinion that the draft is fine.

## Related ideas

- [Evals]({{< ref "/ai/evals" >}}): the same check can grade outputs across a test set. In an eval it scores a version of the application; as feedback it fixes one output while the application runs.
- [Tool use]({{< ref "/ai/agentic-patterns" >}}): outside information can also arrive before the model writes, as a tool result or as documents retrieved for the prompt. Supplying facts up front is called grounding; feedback supplies them after a draft.

References: [Large Language Models Cannot Self-Correct Reasoning Yet (Huang et al., 2023)](https://arxiv.org/abs/2310.01798), [CRITIC (Gou et al., 2023)](https://arxiv.org/abs/2305.11738), [When Can LLMs Actually Correct Their Own Mistakes? (Kamoi et al., 2024)](https://arxiv.org/abs/2406.01297), [Teaching Large Language Models to Self-Debug (Chen et al., 2023)](https://arxiv.org/abs/2304.05128), [Reflexion (Shinn et al., 2023)](https://arxiv.org/abs/2303.11366), [Taj Mahal (UNESCO World Heritage List)](https://whc.unesco.org/en/list/252/)
