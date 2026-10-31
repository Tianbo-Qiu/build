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

- `make serve` builds the search index, then previews at localhost:1313, including drafts. Rerun it to pick up new notes in search.
- `make new note=<topic>/<slug>` creates a draft note, e.g. `make new note=k8s/container/cgroups`.
- `make build` builds the site and search index into `public/`.

Search uses [Pagefind](https://pagefind.app/) (pinned in the `Makefile`, run with npx). It indexes only the `<article data-pagefind-body>` of notes and section pages; section pages' child lists are excluded with `data-pagefind-ignore`. Cmd+K (Ctrl+K elsewhere) opens a search overlay, and Pagefind loads only on first use. The Search link goes to the `/search/` page (`content/search.md`, `layouts/search.html`). Both use Pagefind's Component UI, themed through `--pf-*` variables on `body` in `layouts/baseof.html`.

Each topic folder has an `_index.md` with its title.

## Design

The UI is deliberately plain. Keep it that way: no toggles, menus, or JavaScript unless asked.

- Layout: a left sidebar shows the whole topic tree, always expanded, with the current page in bold. A breadcrumb sits above each title. The page stays left-aligned on wide screens.
- A "Search" link sits under the site title and opens the search page. A muted "⌘K" hint beside it points to the overlay shortcut.
- Phones (under 48rem): the tree is hidden. Navigation is the site title, the Search link, the breadcrumb, and section pages that list their notes.
- Type: Libre Baskerville body at 16px with line height 1.75, Libre Franklin for headings and navigation, JetBrains Mono for code. Fonts are self-hosted in `static/fonts/` (Latin subset, OFL licenses alongside).
- The text column is 36rem, about 65 characters per line.
- Keep WCAG AA: text contrast at least 4.5:1, link targets at least 24px tall.

- Links inside notes are underlined, because color alone isn't enough to mark them. Navigation links aren't underlined.
- Code blocks use flat grey backgrounds. Syntax colors come from `static/css/syntax.css`, generated with `hugo gen chromastyles` (`github` for light, `github-dark` for dark, each scoped to its color mode, backgrounds removed).

All other styles live in `layouts/baseof.html`. After a UI change, check light mode, dark mode, and phone width.

## Git

- Never commit or push without asking first.
- Commit messages have no Co-Authored-By or other AI attribution lines.
- Keep every line of a commit message under 72 characters, subject and body.
