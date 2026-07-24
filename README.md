# AppMan

A Linux application inventory manager — think "Programs and Features" for the terminal.

## Usage

```bash
./appman.sh
# or
.venv/bin/python -m appman
```

## Controls

| Key | Action |
|---|---|
| `↑` `↓` | Navigate list |
| `Enter` | Select package (show details) |
| `/` | Focus search |
| `u` | Uninstall selected (prints command) |
| `o` | Open homepage |
| `c` | Copy package name |
| `F5` | Refresh from pacman DB |
| `Esc` | Clear search / unfocus |
| `q` | Quit |

## Data sources

- **Pacman** (v1) — reads `/var/lib/pacman/local/` directly, caches to `~/.cache/appman/packages.json`

## Files

```
appman/
  backends.py   — pacman DB parser, cache, filtering, categories
  app.py        — Textual TUI
  __main__.py   — entry point for `python -m appman`
```

Skipped for v1 (per ponytail): Flatpak/Snap/AUR/AppImage backends, config file, export, favorites, reverse deps. Add when needed.
