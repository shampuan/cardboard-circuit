# Cardboard Circuit

Cardboard Circuit is a fun racing game developed for children aged 6–12.

Instead of a traditional racing track, the race takes place on rotating cardboard disks. The player controls a small toy car using the mouse while managing battery power and avoiding terrain hazards.

The game was designed to be simple, lightweight and easy to play, while still offering a small challenge through battery management and obstacle avoidance.

## Features

- 5 different race stages
- Multiple selectable vehicles
- Mouse steering
- Battery management system
- Different terrain types affecting performance
- Stage music and sound effects
- Pause support
- Lightweight and fast
- Designed for Linux desktops
- Free Software (GPLv3)

## Controls

| Key | Action |
|-------|----------|
| W | Start race / Accelerate |
| Mouse | Steering |
| S | Brake |
| P | Pause |
| ESC | Exit game |

## Terrain Types

Different terrain colors affect vehicle performance and battery consumption.

| Terrain | Effect |
|----------|----------|
| Black Road | Normal driving |
| Grey Area | Medium slowdown |
| Green Area | Heavy slowdown |
| Blue Area | Water area, heavy slowdown |
| Red Area | Crash |

Avoid colored areas whenever possible. Braking and difficult terrain consume the battery much faster.

## Requirements

- Python 3.10 or newer
- PyQt6
- pygame
- numpy

## Installation (GitHub Source)

Clone the repository:

```bash
git clone https://github.com/shampuan/cardboard-circuit.git
cd cardboard-circuit
```

Install dependencies:

```bash
pip install .
```

Run:

```bash
cardboard-circuit
```

Alternatively:

```bash
python3 -m cardboardcircuit.main
```

## Debian Package

A ready-to-install Debian package is available in the Releases section.

Download the latest `.deb` package and install it with:

```bash
sudo dpkg -i cardboard-circuit_1.0.0_all.deb
```

If dependency problems occur:

```bash
sudo apt -f install
```

## Project Structure

```text
cardboardcircuit/
├── __init__.py
├── main.py
├── car.py
├── caricon.png
├── cars/
├── disks/
├── effects/
└── sounds/
```

## License

This project is licensed under the GNU General Public License v3.0 (GPLv3).

## Author

A. Serhat KILIÇOĞLU

GitHub:
https://github.com/shampuan

---

Have fun racing on cardboard tracks!
