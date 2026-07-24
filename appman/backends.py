"""Pacman local-DB backend — reads /var/lib/pacman/local/ directly."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterator

PACMAN_DB = Path("/var/lib/pacman/local")
CACHE_DIR = Path.home() / ".cache" / "appman"
CACHE_FILE = CACHE_DIR / "packages.json"

# Packages to always hide from the user view
FILTER_GROUPS: set[str] = {
    "lib", "python-", "perl-", "ruby-", "lua-", "node-",
    "-docs", "-debug", "-locale",
    "ttf-", "otf-",
    "linux-firmware", "linux-headers",
}


@dataclass
class Package:
    name: str
    version: str
    description: str
    url: str = ""
    installed_size: int = 0
    install_date: int = 0
    install_reason: int = 0  # 0=explicit, 1=dependency
    license_: str = ""
    category: str = "Other"
    source: str = "pacman"


# ── parsers ──────────────────────────────────────────────────────────────

def _parse_sections(text: str) -> dict[str, str]:
    """Split a pacman ``%%KEY%%``-style file into {key: value}."""
    sections: dict[str, str] = {}
    key = None
    parts: list[str] = []
    for line in text.splitlines():
        if line.startswith("%") and line.endswith("%"):
            if key is not None:
                sections[key] = "\n".join(parts)
            key = line.strip("%").lower()
            parts = []
        elif key is not None and line.strip():
            parts.append(line)
    if key is not None:
        sections[key] = "\n".join(parts)
    return sections


def _parse_pkg_dir(pkg_dir: Path) -> Package | None:
    desc_file = pkg_dir / "desc"
    if not desc_file.exists():
        return None
    desc = _parse_sections(desc_file.read_text())
    return Package(
        name=desc.get("name", pkg_dir.name),
        version=desc.get("version", ""),
        description=desc.get("desc", ""),
        url=desc.get("url", ""),
        installed_size=int(desc.get("size", 0)),
        install_date=int(desc.get("installdate", 0)),
        install_reason=int(desc.get("reason", 0)),
        license_=desc.get("license", ""),
    )


# ── filtering ────────────────────────────────────────────────────────────

def _is_user_pkg(pkg: Package) -> bool:
    # Hide anything pulled in as a dependency unless it looks like an app
    if pkg.install_reason == 1:
        return False
    # Also filter explicitly-installed libs, fonts, firmware, docs, headers
    name = pkg.name.lower()
    for prefix in FILTER_GROUPS:
        if name.startswith(prefix) or name.endswith(prefix):
            return False
    return True


_USER_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Browser": ["browser", "firefox", "chromium", "web", "www", "webkit"],
    "Editor": ["editor", "vim", "neovim", "emacs", "nano", "code", "atom", "subl"],
    "Terminal": ["terminal", "alacritty", "kitty", "wezterm", "foot", "ghostty"],
    "Development": ["gcc", "make", "cmake", "git", "build", "compiler", "python", "rust", "golang", "julia"],
    "IDE": ["ide", "pycharm", "intellij", "clion", "vscode", "eclipse", "android-studio"],
    "Graphics": ["gimp", "krita", "inkscape", "blender", "image", "photo", "paint", "draw"],
    "Video": ["vlc", "mpv", "player", "video", "ffmpeg", "obs"],
    "Audio": ["spotify", "mpd", "music", "audio", "player", "pulse", "pipewire"],
    "Game": ["game", "steam", "lutris", "wine", "heroic"],
    "Office": ["office", "libreoffice", "word", "excel", "powerpoint", "pdf", "document"],
    "Communication": ["discord", "telegram", "signal", "whatsapp", "slack", "matrix"],
    "Security": ["vpn", "wireguard", "openvpn", "firewall", "crypt"],
    "System": ["system", "systemd", "util", "manager"],
    "Database": ["sql", "mysql", "postgres", "sqlite", "mongo", "redis"],
    "Cloud": ["cloud", "aws", "gcp", "azure", "docker", "kubernetes"],
}


def _detect_category(pkg: Package) -> str:
    haystack = (pkg.name + " " + pkg.description).lower()
    for cat, keywords in _USER_CATEGORY_KEYWORDS.items():
        if any(k in haystack for k in keywords):
            return cat
    return "Other"


# ── public API ────────────────────────────────────────────────────────────

# ── flatpak ──────────────────────────────────────────────────────────────

def _flatpak_packages() -> list[Package]:
    """Parse `flatpak list` output, return as Packages with source=flatpak."""
    try:
        r = subprocess.run(
            ["flatpak", "list", "--columns=application,version,size,installation"],
            capture_output=True, text=True, timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    pkgs: list[Package] = []
    for line in r.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        app_id = parts[0]
        version = parts[1] if len(parts) > 1 else ""
        size_str = parts[2] if len(parts) > 2 else ""
        install = parts[3] if len(parts) > 3 else "system"
        size_bytes = 0
        if size_str:
            try:
                # flatpak can output "1.4 MB", "502.9 MB", etc.
                num, unit = size_str.split()
                num = float(num)
                size_bytes = int(num * {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}.get(unit, 1))
            except (ValueError, IndexError):
                pass
        # source label: "flatpak:system" vs "flatpak:user"
        source_label = f"flatpak:{install}"
        pkgs.append(Package(
            name=app_id,
            version=version,
            description="",
            installed_size=size_bytes,
            install_date=0,
            source=source_label,
        ))
    return pkgs


# ── combined loader ──────────────────────────────────────────────────────

def get_packages(force_refresh: bool = False) -> list[Package]:
    """Return all packages from all sources, cached."""
    if not force_refresh and CACHE_FILE.exists():
        data = json.loads(CACHE_FILE.read_text())
        pkgs = [Package(**p) for p in data]
        for p in pkgs:
            if not p.category or p.category == "Other":
                p.category = _detect_category(p)
        return pkgs

    pkgs: list[Package] = []
    # pacman
    for entry in sorted(PACMAN_DB.iterdir()):
        pkg = _parse_pkg_dir(entry)
        if pkg is not None:
            pkg.category = _detect_category(pkg)
            pkgs.append(pkg)
    # flatpak
    pkgs.extend(_flatpak_packages())

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _write_cache(pkgs)
    return pkgs


# ponytail: snap & AppImage added when user has them
# ponytail: flatpak size parsing naive (assumes "X.Y UNIT"), misses edge cases


def _write_cache(pkgs: list[Package]) -> None:
    CACHE_FILE.write_text(json.dumps([asdict(p) for p in pkgs], indent=1))


def refresh_cache() -> list[Package]:
    """Force re-read and return."""
    pkgs = get_packages(force_refresh=True)
    _write_cache(pkgs)
    return pkgs


def filtered_packages(pkgs: list[Package] | None = None) -> list[Package]:
    """Return only user-installed applications (hide libs, fonts, etc.)."""
    if pkgs is None:
        pkgs = get_packages()
    return [p for p in pkgs if _is_user_pkg(p)]


# ponytail: no config file yet — add when user wants custom filter rules


def uninstall(pkg: Package) -> subprocess.CompletedProcess:
    """Run ``pacman -Rns`` via sudo."""
    cmd = ["sudo", "pacman", "-Rns", pkg.name]
    return subprocess.run(cmd, check=False)


if __name__ == "__main__":
    pkgs = get_packages()
    user_pkgs = filtered_packages(pkgs)
    print(f"Total: {len(pkgs)}  User-visible: {len(user_pkgs)}")
    cat_counts: dict[str, int] = {}
    for p in user_pkgs:
        cat_counts[p.category] = cat_counts.get(p.category, 0) + 1
    for cat, n in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  {n:4d}  {cat}")
