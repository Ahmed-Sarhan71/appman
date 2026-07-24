# Project Specification: AppMan (Linux Application Manager)

## Goal

Create a modern Linux application manager similar to Windows "Programs and Features" or Revo Uninstaller.

This is **NOT** a package manager replacement. It is an application inventory and management tool focused on software intentionally installed by the user.

Target platform:

- Arch Linux (first)
    
- Later support Debian/Ubuntu, Fedora, openSUSE
    

Language:

- Python 3.14+
    

License:

- MIT
    

---

# UI

Use **Textual** for a modern terminal interface.

Requirements:

- Instant startup
    
- Keyboard navigation
    
- Mouse support
    
- Live search
    
- Dark mode
    
- Responsive layout
    

Main screen:

```
Search: ____________________

Applications

Name
Version
Source
Category
Installed
Size

Details panel
```

---

# Data Sources

Support:

## Pacman

Read installed packages from the local Pacman database.

Prefer reading:

```
/var/lib/pacman/local/
```

instead of repeatedly executing pacman commands.

Collect:

- name
    
- version
    
- description
    
- install date
    
- install reason
    
- dependencies
    
- installed size
    
- repository
    

---

## AUR

Detect AUR packages.

Possible methods:

- pacman local database
    
- pacman -Qm
    
- pyalpm
    

---

## Flatpak

Use

```
flatpak list
```

or Flatpak APIs.

Collect:

- app id
    
- name
    
- version
    
- size
    

---

## Snap

Use

```
snap list
```

Collect:

- version
    
- publisher
    

---

## AppImages

Search common directories only.

Default:

```
~/Applications
~/AppImages
/opt
```

Do NOT recursively scan the entire home directory.

---

# Package Model

Each application should expose:

```
Application
{
    id
    name
    version
    description
    category
    source
    install_date
    installed_size
    executable
    desktop_file
    homepage
    icon
    dependencies
    uninstall_command
}
```

---

# Filtering

Hide by default:

Libraries

Development headers

Fonts

Firmware

Locales

Documentation packages

Kernel modules

Debug packages

Display applications intentionally installed by the user.

Provide an option to show everything.

---

# Categories

Automatically detect categories.

Examples:

Browsers

Editors

IDEs

Games

Emulators

Virtualization

Networking

Office

Graphics

Video

Audio

Databases

Containers

Programming

Utilities

System

Security

AI

Cloud

Unknown

---

# Search

Search should match:

Package name

Application name

Description

Executable

Desktop file

Category

Search updates live while typing.

---

# Sorting

Allow sorting by:

Name

Size

Install date

Version

Source

Category

---

# Details Page

Display:

Name

Version

Description

Source

Repository

Homepage

Installed size

Install date

Dependencies

Reverse dependencies

Desktop entry

Executable

Icon

Package location

---

# Actions

Open application

Open package homepage

Copy package name

Copy executable path

Show dependencies

Show reverse dependencies

Uninstall

Reinstall

Mark favorite

---

# Uninstall

Run the appropriate backend:

Pacman

```
sudo pacman -Rns package
```

Flatpak

```
flatpak uninstall
```

Snap

```
snap remove
```

AppImage

Delete file after confirmation.

---

# Export

Support:

CSV

JSON

Markdown

---

# Configuration

Store configuration in

```
~/.config/appman/config.toml
```

Options:

Theme

Visible columns

Hidden categories

Search behavior

AppImage paths

Favorites

---

# Performance

Target:

Startup under one second.

Avoid repeatedly spawning pacman.

Cache application metadata.

Use asynchronous loading where appropriate.

---

# Architecture

```
appman/

backend/

ui/

models/

utils/

cache/

config/

assets/

tests/
```

Each backend should implement the same interface.

---

# Testing

Unit tests for:

Pacman parser

Desktop entry parser

Filtering

Category detection

Search

Sorting

---

# Documentation

Generate:

README

Installation guide

Developer guide

Contribution guide

Architecture document

---

# Code Quality

Requirements:

Type hints

Dataclasses

Modular architecture

Logging

Docstrings

Black formatting

Ruff linting

Pytest

No duplicated code

PEP 8 compliant

---

# Future Features

Dependency graph

Disk usage analysis

Orphan package detection

Duplicate AppImage detection

Package history

Update manager

Plugin system

Support additional Linux distributions

Package statistics dashboard


# UI Mockups

## Main Dashboard

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ AppMan v1.0                                                     Arch Linux              🔄 Refresh │
├──────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 🔍 Search: pcsx                                                                         Filters ▼   │
├──────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Name                 Version      Source      Category       Size       Installed                  │
├──────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 🎮 PCSX2            2.7.479      AUR         Emulator      174 MB     2026-07-16                 │
│ 🎮 Dolphin          2506         Official    Emulator       32 MB     2026-07-20                 │
│ 🎮 Cemu             2.6          AUR         Emulator       81 MB     2026-07-18                 │
│ 🎮 Ryujinx          1.3          AppImage    Emulator      142 MB     2026-07-17                 │
│ 🌐 Firefox          141.0        Official    Browser       280 MB     2026-07-01                 │
│ 💻 Visual Studio    1.103        Official    IDE           410 MB     2026-07-21                 │
│ 🛠 DBeaver          25.1         Official    Database      220 MB     2026-07-21                 │
│ 🎵 Spotify          1.2          Flatpak     Music         350 MB     2026-07-05                 │
│ 📦 Docker Desktop   4.x          Official    Containers    520 MB     2026-07-12                 │
└──────────────────────────────────────────────────────────────────────────────────────────────────────┘

Selected: PCSX2
```

---

## Details Panel

```text
┌──────────────────────────────────────────────────────────────┐
│ 🎮 PCSX2                                              ☆      │
├──────────────────────────────────────────────────────────────┤
│ Version          2.7.479                               │
│ Source           AUR                                   │
│ Repository       AUR                                   │
│ Category         Emulator                              │
│ Installed        2026-07-16                            │
│ Installed Size   174 MB                                │
│ Executable       /usr/bin/pcsx2                        │
│ Homepage         https://pcsx2.net                     │
│ Desktop Entry    pcsx2.desktop                         │
├──────────────────────────────────────────────────────────────┤
│ Description                                         │
│ PlayStation 2 emulator                              │
├──────────────────────────────────────────────────────────────┤
│ Dependencies                                        │
│ qt6-base                                            │
│ ffmpeg                                              │
│ sdl2                                                │
│ ...                                                 │
└──────────────────────────────────────────────────────────────┘
```

---

## Keyboard Shortcuts

```text
Enter      Open details
Ctrl+F     Focus search
U          Uninstall
R          Reinstall
I          Package information
H          Homepage
F          Favorite
D          Dependencies
O          Reverse dependencies
E          Export
S          Sort
C          Change columns
Space      Multi-select
Delete     Remove selected
F5         Refresh
Ctrl+R     Reload package database
Esc        Clear search
Q          Quit
```

---

## Filter Sidebar

```text
Sources
☑ Official
☑ AUR
☑ Flatpak
☐ Snap
☑ AppImage

Categories
☑ Browsers
☑ IDEs
☑ Databases
☑ Emulators
☑ Games
☑ Containers
☑ Office
☑ Graphics
☑ Audio
☑ Video
☑ AI
☑ Utilities

Status
☑ Installed
☐ Updates Available
☐ Favorites
☐ Recently Installed
```

---

## Planned Features

- Instant fuzzy search
    
- Beautiful Textual interface
    
- Mouse and keyboard navigation
    
- Package icons
    
- Dark and light themes
    
- Dependency tree viewer
    
- Reverse dependency viewer
    
- Application launcher
    
- One-click uninstall with confirmation
    
- Package homepage viewer
    
- Export to CSV, JSON, and Markdown
    
- Package statistics dashboard
    
- Recently installed timeline
    
- Favorites
    
- Package notes
    
- Update center
    
- Plugin system
    
- Cross-distribution backend support (Arch, Debian/Ubuntu, Fedora, openSUSE)
    

---

## Design Goals

The application should feel like a native Linux equivalent of Windows "Programs and Features" or Revo Uninstaller while remaining lightweight, fast, and keyboard-friendly.

Performance targets:

- Startup in under one second.
    
- Smooth scrolling with thousands of packages.
    
- Live search without noticeable delay.
    
- Minimal memory usage.
    
- Avoid repeated package manager invocations by caching metadata and reading local package databases where possible.


