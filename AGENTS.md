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
- No shell commands or command output in concept notes. Walkthrough notes are the exception (see below).
- Use the serial (Oxford) comma.

Accuracy:

- Check every claim against a primary source (man pages, official docs, specs).
- Prefer precise words: "process", not "program"; "instance", not "copy" when it isn't one.
- Don't overgeneralize. If a detail holds only by default or only in one case, say so.

To show a short definition of a term on hover, tap, or keyboard focus, add it to `data/glossary.toml` and write `{{< term kubelet >}}` in the note, or `{{< term kubelet "Kubelet" >}}` to show different text. Mark only terms the note relies on but doesn't explain, and only where the term first appears. Glossary definitions follow the same accuracy rules as notes. Every entry is also listed on the Glossary page (`/glossary/`, `layouts/glossary.html`), sorted by name, each with its own anchor such as `/glossary/#kubelet`. Keep a definition to one or two sentences; a term that needs more gets a note, and the entry's `note` field links to it.

A walkthrough note teaches a group of ideas by building them up and using them, as `content/k8s/deployment/index.md` does for containers, pods, ReplicaSets, and Deployments. It uses `##` headings, and it shows the commands a reader would run. Open with the definition, why the thing exists, and its parts as a few bullets with one diagram. Then give each part or mechanism its own short section, in the order the source teaches them, as `content/k8s/service/index.md` does. Keep sections flat and small rather than growing one long section; repeating a fact in two sections is fine. Write statements of fact, not advice or conversation: no "you should", no "that's enough for most uses", no lookup tables of options. Let components, diagrams, sequences, and tables carry the detail, and keep prose to how things work. Each command goes in a `parts` shortcode, one part per line as `text | explanation`, so the reader can point at a part and see what it does. Start a line with `+ ` for a default the reader can leave out; it stays hidden until they choose Show defaults. Use `{{< parts join="-" >}}` to split a generated name such as a pod name. Explain what each part means and what happens when it's left out, not every flag the command has. Show no command output; describe in prose what it shows.

Diagrams are written in [D2](https://d2lang.com/). A note with a diagram is a folder (`content/k8s/architecture/index.md`) holding the `.d2` source and the rendered `.svg`, shown with a Markdown image whose alt text describes the diagram in words. Run `make diagrams` after changing a `.d2` file and commit both files; the site build doesn't need D2. `diagram.d2` at the repo root holds the shared style (dagre layout, the site's greys, light and dark) and is prepended to every source, so diagrams don't set colors. Diagrams render at their natural size and shrink to fit the column; its 22px text keeps large diagrams readable on phones, and small diagrams can set `**.style.font-size: 16` so they don't look heavier than the body text. D2's `**` glob styles shapes only, so arrow labels need `(* -> *)[*].style.font-size`. Diagrams wider than 900px, such as sequence diagrams, scroll sideways on phones instead of shrinking (`layouts/_markup/render-image.html`), so they can use larger text, around 30px. Add a diagram only when a picture shows structure that prose can't, and keep labels short.

References go on the last line and point to primary sources only, never to the book or course being studied.

Guides followed: [Google Technical Writing One](https://developers.google.com/tech-writing/one), [Google developer documentation style guide](https://developers.google.com/style), [Microsoft Writing Style Guide](https://learn.microsoft.com/en-us/style-guide/welcome/), and [Diátaxis explanation](https://diataxis.fr/explanation/).

## Site

- `make serve` builds the search index, then previews at localhost:1313, including drafts. Rerun it to pick up new notes in search.
- `make new note=<topic>/<slug>` creates a draft note, e.g. `make new note=k8s/container/cgroups`.
- `make build` builds the site and search index into `public/`.
- `make diagrams` renders each changed `.d2` file under `content/` to an `.svg` beside it. It needs `d2` installed locally (`brew install d2`).
- `make run-image` builds the Docker image and serves it at localhost:8090. Change the port with `make run-image PORT=9000`.

The `Dockerfile` has two stages. The first runs `make build` with pinned Hugo and Node. The second serves `public/` with nginx (`nginx.conf`). The build copies `.git` on purpose, because "Updated" dates come from git history. Keep the Hugo version there in step with the one used locally.

Search uses [Pagefind](https://pagefind.app/) (pinned in the `Makefile`, run with npx). It indexes only the `<article data-pagefind-body>` of notes and section pages; section pages' child lists are excluded with `data-pagefind-ignore`. Cmd+K (Ctrl+K elsewhere) opens a search overlay, and Pagefind loads only on first use. The Search link goes to the `/search/` page (`content/search.md`, `layouts/search.html`). Both use Pagefind's Component UI, themed through `--pf-*` variables on `body` in `layouts/baseof.html`.

Each topic folder has an `_index.md` with its title.

Notes show "Created" from the `date` front matter, a UTC time that `make new` fills in. "Updated" comes from the file's last git commit (`enableGitInfo`) and appears only when it's a later UTC day than the created date. Pages render both in UTC, and a short script rewrites them in the reader's time zone.

In the tree and on section pages, subtopics sort by title and notes sort by created time, oldest first.


Analytics are off unless the build sets `HUGO_ANALYTICS_SRC` to an analytics script URL, which is configured on the host, not in the repo. `layouts/_partials/analytics.html` loads it. Visiting any page with `?analytics=off` stops counting that browser, and `?analytics=on` restores it.

## Design

The UI is deliberately plain. Keep it that way: no toggles, menus, or JavaScript unless asked.

The one exception is the home page robot (`layouts/_partials/robot.html`, shown only on the home page). Its head turns to follow the pointer. It is a real-time 3D model drawn with three.js: `static/robot/robot.glb` is a skinned glTF exported from the sibling `blender` project (`robot_web.blend`), with Body, Neck, and Head bones, Draco-compressed meshes, and WebP textures whose color, roughness, metalness, normals, and ambient occlusion were baked from the Cycles materials. `static/robot/robot3d.js` loads it when the figure nears the viewport, turns the bones toward the pointer with a spring (the body follows a little, the neck half, the head fully), and glances around on its own when the pointer is idle. The canvas is transparent, so the page background shows through in both color modes. `static/robot/still.webp` shows until the model is ready, and stays when JavaScript or WebGL is unavailable. With reduced motion the robot holds still. three.js 0.170.0 is self-hosted under `static/robot/vendor/three/` (MIT, license alongside) and mapped with an import map; the Draco decoder is in `static/robot/draco/`. Re-export the model from Blender rather than editing the glTF by hand, and keep the import map in step with the vendored version.

- Layout: a left sidebar shows the whole topic tree, always expanded, with the current page in bold. A breadcrumb sits above each title. The page stays left-aligned on wide screens.
- A "Search" link sits under the site title and opens the search page. A muted "⌘K" hint beside it points to the overlay shortcut.
- Phones (under 48rem): the tree is hidden. Navigation is the site title, the Search link, the breadcrumb, and section pages that list their notes.
- Type: Libre Baskerville body at 16px with line height 1.75, Libre Franklin for headings and navigation, JetBrains Mono for code. Fonts are self-hosted in `static/fonts/` (Latin subset, OFL licenses alongside).
- The text column is 36rem, about 65 characters per line.
- Keep WCAG AA: text contrast at least 4.5:1, link targets at least 24px tall.

- Links inside notes are underlined, because color alone isn't enough to mark them. Navigation links aren't underlined.
- An email address is written `{{< email "address" >}}`: the word "email" with a small copy icon. Clicking it copies the address and shows "Copied"; without clipboard access or JavaScript it's a mailto link.
- Command parts (`parts` shortcode) show the command in a code block with each part's explanation listed below it, behind a thin left rule. Pointing at a part, in the command or the list, highlights both. Defaults are muted and hidden behind a Show defaults button; without JavaScript they stay visible.
- Glossary terms have a muted dashed underline. Their definition box is flat, with a border and no shadow, and stays inside the screen. Escape closes it.
- Code blocks use flat grey backgrounds. Syntax colors come from `static/css/syntax.css`, generated with `hugo gen chromastyles` (`github` for light, `github-dark` for dark, each scoped to its color mode, backgrounds removed).

- The site mark is a triangle of three blue scan-line pieces. `static/favicon.svg` is the source; `favicon.ico` (32px), `apple-touch-icon.png` (180px, white background), and `icon-512.png` (profile picture) are rendered from it.

All other styles live in `layouts/baseof.html`. After a UI change, check light mode, dark mode, and phone width.

## Git

- Never commit or push without asking first.
- Commit messages have no Co-Authored-By or other AI attribution lines.
- Keep every line of a commit message under 72 characters, subject and body.
