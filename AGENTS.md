# AGENTS.md

A personal knowledge base about building software, built with Hugo. Notes live in `content/`, grouped by topic (for example `content/k8s/container/namespace.md`).

## Writing notes

Notes explain how a thing really works, from first principles, the way Feynman would. A reader new to the topic should finish one note understanding it.

- Open with one sentence that defines the title's term.
- Say why the thing exists and what the alternative is.
- Build each idea on the one before it, in plain words, then use the proper term.
- Add one concrete example that shows the concept at work, written as prose.
- Keep it short: a few paragraphs, one topic per paragraph, 3–5 sentences each.

Style:

- Short sentences, one idea each, active voice.
- Pick one term for each idea and use it every time.
- Don't explain a term with another unexplained term.
- No bold for terms or emphasis.
- No filler headings. A note normally has only its title.
- No shell commands or command output in concept notes.
- Use the serial (Oxford) comma.

Accuracy:

- Check every claim against a primary source (man pages, official docs, specs).
- Prefer precise words: "process", not "program"; "instance", not "copy" when it isn't one.
- Don't overgeneralize. If a detail holds only by default or only in one case, say so.

References go on the last line and point to primary sources only, never to the book or course being studied.

Guides followed: [Google Technical Writing One](https://developers.google.com/tech-writing/one), [Google developer documentation style guide](https://developers.google.com/style), [Microsoft Writing Style Guide](https://learn.microsoft.com/en-us/style-guide/welcome/), and [Diátaxis explanation](https://diataxis.fr/explanation/).

## Site

- `make serve` previews at localhost:1313, including drafts.
- `make new name=<slug>` creates a draft note in `content/notes/`.
- `make build` builds into `public/`.

Each topic folder has an `_index.md` with its title.

## Git

- Never commit or push without asking first.
- Commit messages have no Co-Authored-By or other AI attribution lines.
- Keep every line of a commit message under 72 characters, subject and body.
