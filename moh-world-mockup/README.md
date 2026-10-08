# MOH World — 3D mockup (temporary home)

A **rough, still-frame mockup** of how MOH World could look. Everything on screen is fake
example data. It does **not** read your Obsidian vault, does not connect to anything, and has
nothing to do with CloudGuard. It lives in this branch only until the `moh-world` repo exists.

## Just look at it

The `renders/` folder has screenshots. GitHub shows them when you click a file:

| File | What it shows |
| --- | --- |
| `phases.png` | The same town at dawn, day, dusk and night |
| `day.png` / `night.png` | The normal view with speech bubbles |
| `day-brief.png` | Town Hall clicked: the morning brief panel |
| `night-school.png` | School clicked at night |
| `close-day.png` / `close-night.png` | Closer view, bubbles hidden |
| `hero-day.png` / `hero-night.png` | Close-up of the Town Hall bot |

## Run it on your laptop (Windows or Mac)

You need [Node.js](https://nodejs.org) 20 or newer (the LTS download is fine) and
[Git](https://git-scm.com).

```bash
git clone https://github.com/Moh109/cloud-monitor.git
cd cloud-monitor
git checkout claude/confident-euler-65tjmy
cd moh-world-mockup
npm install
npm start
```

Then open **http://127.0.0.1:8123** in your browser. The bar at the bottom switches the time
of day, the camera, the side panel and the bubbles. Each click reloads the page with a new
view (it takes a second or two to draw). Stop the server with `Ctrl+C`.

`npm install` downloads one package, [three](https://threejs.org) (the 3D library), into
`node_modules/`. After that it runs fully offline.

### What to expect

- It is one still picture per view. Dragging to rotate, live time and clicking buildings come
  in the real app.
- The server only listens on `127.0.0.1` (your own machine), only serves files from this
  folder, and tells the browser not to load anything from the internet.

## Files

| File | Purpose |
| --- | --- |
| `index.html` | Page layout and styles (top bar, bubbles, panel) |
| `town3d.js` | Builds the 3D town, lights it for the time of day, renders it, places the labels |
| `bots.js` | Builds the residents from Bot Crossing's bot |
| `serve.mjs` | The local-only server (no dependencies) |
| `vendor/bot-crossing/` | Files copied unchanged from Bot Crossing, with their licence |

## Credits and licences

- **Bot Crossing** by Jarren Rocks — the bot's helmet, visor and face code, the tilt-shift and
  contact-shading passes, and the colour grade. MIT licence, kept in `vendor/bot-crossing/LICENSE`.
  "Bot Crossing" is their name, not ours, and the bot is not MOH World's logo or mascot.
- **KayKit Character Animations** by Kay Lousberg — the bot's body and animations (`crew.glb`). CC0.
- **three.js** — MIT.
- Buildings, island, sky and UI are original to this mockup.
