+++
title = 'Evaluating LLM applications'
date = '2026-11-08T18:55:11Z'
+++

An eval is a fixed set of test inputs, run through an application built on a {{< term llm >}}, with a way to score each output. It exists because changes to such an application don't have predictable effects. A reworded prompt or an added [reflection step]({{< ref "/ai/agentic-patterns" >}}) can help some inputs and hurt others, and each added step costs calls and time. Trying a few inputs by hand shows only those inputs. An eval gives one number per version, so two versions can be compared on the same inputs.

An eval has three parts:

- Test set: inputs that look like real use, often a few dozen to start, each with the expected answer if one exists.
- Grader: the check that scores each output, written as code, done by a person, or done by another LLM.
- Score: the share of outputs that pass, or the average of their grades, reported for each version.

## Objective evals

An objective eval has a right answer for each input, so code can grade it. Take an application that answers questions about a store's sales by having an LLM write an SQL query. The test set pairs each question with its ground truth, the answer computed by hand from the data. The grader runs each version's query and compares the result with the ground truth.

Here are two versions of the query for one question, "Which color has the highest total sales?", run on a small table of nine sales:

```sql
-- version A: counts sales records
SELECT p.color, COUNT(*) AS sales
FROM sales s JOIN products p ON p.id = s.product_id
GROUP BY p.color ORDER BY sales DESC LIMIT 1;

-- version B: sums sales in dollars
SELECT p.color, SUM(s.qty * p.price) AS revenue
FROM sales s JOIN products p ON p.id = s.product_id
GROUP BY p.color ORDER BY revenue DESC LIMIT 1;
```

Version A returns red, which has the most sales records, 4. Version B returns black, which has the most sales in dollars, 205. Black is the ground truth, so A fails and B passes. Over three questions, the results are:

| Question | Ground truth | A | B |
|---|---|---|---|
| Color with the highest total sales | black | red | black |
| Items sold in May 2025 | 11 | 6 | 11 |
| Most expensive item | grinder, 80 | grinder, 80 | grinder, 80 |

Version A counted sales records in the two questions that asked for amounts, so it scores 1 of 3, and version B scores 3 of 3. The table and queries were written for this example; in a real eval, version B would be the query after a reflection step, and the test set would have more questions.

![A test set of 3 questions with ground-truth answers goes to two versions: version A, the query as first written, and version B, the query after reflection. Both send their answers to code that compares each answer with the ground truth. The scores come out as A, 1 of 3 right, and B, 3 of 3 right.](compare.svg)

Once the test set exists, every new prompt, for the first draft or for the reflection, is scored the same way. Anthropic's eval docs call code-based grading the "fastest and most reliable" method, though it "lacks nuance" for judgments that rules can't capture.

## Subjective evals

A subjective eval has no single right answer, such as whether a chart is clear. People can grade it, but slowly. The other way is an LLM as a judge: a second model, prompted to grade the output.

Asking a judge which of two outputs is better is unreliable. Zheng et al. (2023) measured three biases in LLM judges:

- Position bias: favoring the answer in one position, such as the first, regardless of its quality.
- Verbosity bias: favoring the longer answer.
- Self-enhancement bias: favoring answers the judge model wrote itself.

A common fix is to grade one output at a time against a rubric of specific checks, each passed or failed, and add up the passes:

```text
Grade the attached chart. Answer yes or no for each item.
1. The chart has a title.
2. Both axes have labels.
3. The chart type suits the data (for example, a line for a trend).
4. The legend names every series.
5. No text overlaps.
```

The score is the number of yes answers, out of 5. A judge also needs tuning: its grades are checked against a person's grades on a sample before its scores are trusted. Anthropic's docs recommend "detailed, clear rubrics", grades that are specific such as "correct" or "incorrect", and a grader that reasons before it scores. Zheng et al. found that strong judges such as GPT-4 agreed with human preferences more than 80% of the time, about as often as people agree with each other.

## Objective compared with subjective

- Objective eval: a ground-truth answer per input, graded by code. Cheap, fast, and the same every run.
- Subjective eval: no single right answer, graded by people or an LLM judge with a rubric. The judge needs its own checks against human grades.

References: [Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena (Zheng et al., 2023)](https://arxiv.org/abs/2306.05685), [Define success criteria and build evaluations (Anthropic)](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests), [Evaluation best practices (OpenAI)](https://developers.openai.com/api/docs/guides/evaluation-best-practices)
