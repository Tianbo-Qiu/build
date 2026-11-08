+++
title = 'Prompting techniques'
date = '2026-11-08T18:36:16Z'
+++

A prompting technique is a way of wording the text sent to a {{< term llm >}} so that one call gives a better answer. The model's weights don't change. Only the prompt does, and the model continues whatever text it's given. The three common techniques are zero-shot, few-shot, and chain-of-thought prompting. They all stay within one call. [Agentic design patterns]({{< ref "/ai/agentic-patterns" >}}) such as reflection go further, with several calls.

![Four ways to get an answer. Zero-shot, 1 call: an instruction goes to the LLM, which gives an answer. Few-shot, 1 call: examples plus an instruction go to the LLM, which gives an answer. Chain-of-thought, 1 call: an instruction plus "think step by step" goes to the LLM, which writes its reasoning, then the answer. Reflection, 3 calls: the LLM answers, the LLM critiques the answer, and the LLM writes a revised answer.](calls.svg)

## Zero-shot

A zero-shot prompt states the task with no examples. The model relies on what it learned in training to know what kind of answer fits. Chat models are post-trained to follow instructions, so zero-shot is the usual way they're used. It's also the baseline that other techniques are measured against. This prompt is the zero-shot example from the GPT-3 paper:

```text
Translate English to French:
cheese =>
```

## Few-shot

A few-shot prompt puts a few worked examples before the task, so the model continues the pattern. The examples show the format, the style, and the kind of answer wanted, which an instruction alone can leave unclear. The GPT-3 paper (2020) made this widely known: the model was given "tasks and few-shot demonstrations specified purely via text interaction," with no fine-tuning. One example is called one-shot. The examples take up room in the context window, and the model can copy their quirks along with their pattern.

```text
Translate English to French:
sea otter => loutre de mer
peppermint => menthe poivrée
plush giraffe => girafe peluche
cheese =>
```

## Chain-of-thought

A chain-of-thought prompt gets the model to write its reasoning steps before the answer. Each token the model writes becomes input for the next one, so written steps let it work through a problem it would otherwise answer in one jump. Wei et al. (2022) gave the model eight examples with worked reasoning, a few-shot form. Kojima et al. (2022) found that adding only "Let's think step by step" works zero-shot: with InstructGPT, accuracy on the MultiArith math problems rose from 17.7% to 78.7%.

```text
Q: A juggler can juggle 16 balls. Half of the balls
are golf balls, and half of the golf balls are blue.
How many blue golf balls are there?
A: Let's think step by step.
```

This example is from Kojima et al. Asked for the answer directly, the model gave 8, which is wrong. With the added phrase, it wrote that 16 balls include 8 golf balls, and half of those are blue, so 4 blue golf balls, which is right. Reasoning models, from 2024 on, are trained to write such steps without being asked.

A prompt can also ask the model to check its own work within the same reply, such as "check your answer before giving it". That is still one call, and it works like chain-of-thought: the checking is more written steps before the answer. It differs from the reflection pattern, where a separate reflection prompt critiques a finished answer and a further call revises it.

## Zero-shot compared with reflection

Zero-shot and reflection differ in how many chances the model gets. A zero-shot answer is final: whatever the model writes first is what the user sees. Reflection takes that answer and spends more calls on it: one to critique it, and one to revise it, repeated as needed. Self-Refine (2023) compared the two with the same model and reported scores about 20 percentage points higher on average for reflection, across seven tasks. The cost is about three times the calls and the waiting, or more with extra rounds.

- Zero-shot: one call, no examples, the first answer is final.
- Few-shot: one call, with examples in the prompt.
- Chain-of-thought: one call, with reasoning written before the answer.
- Reflection: several calls, each answer checked and revised.

## Where to read real prompts

Model makers publish prompts they use, and guides with worked examples. Real prompts show the parts that recur: a role, rules, examples, handling of edge cases, and the output format.

Prompts in use:

- [Claude system prompts](https://platform.claude.com/docs/en/release-notes/system-prompts): Anthropic publishes the full system prompts of the Claude apps, version by version, so changes can be compared.
- [Codex CLI](https://github.com/openai/codex): OpenAI's open-source coding agent keeps its prompts as Markdown files in `codex-rs/core/`.
- [Gemini CLI](https://github.com/google-gemini/gemini-cli): Google's open-source coding agent builds its prompt in `packages/core/src/prompts/snippets.ts`.

Guides from the makers:

- [Claude prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) (Anthropic).
- [Prompt engineering](https://developers.openai.com/api/docs/guides/prompt-engineering) and the [GPT-5 prompting guide](https://developers.openai.com/cookbook/examples/gpt-5/gpt-5_prompting_guide) (OpenAI).
- [Prompting strategies](https://ai.google.dev/gemini-api/docs/prompting-strategies) (Google).
- [Prompt engineering interactive tutorial](https://github.com/anthropics/prompt-eng-interactive-tutorial) (Anthropic): nine chapters of exercises in Jupyter notebooks, which need an API key.

Whether a prompt is better shows only in its outputs: two versions are run on the same set of inputs and compared, as in an [eval]({{< ref "/ai/evals" >}}).

References: [Language Models are Few-Shot Learners (Brown et al., 2020)](https://arxiv.org/abs/2005.14165), [Chain-of-Thought Prompting (Wei et al., 2022)](https://arxiv.org/abs/2201.11903), [Large Language Models are Zero-Shot Reasoners (Kojima et al., 2022)](https://arxiv.org/abs/2205.11916), [Self-Refine (Madaan et al., 2023)](https://arxiv.org/abs/2303.17651)
