# Cardboard Circuit

Cardboard Circuit is a fun racing game developed for children aged 6–12.

Instead of a traditional racing track, the race takes place on rotating cardboard disks. The player controls a small toy car using the mouse while managing battery power and avoiding terrain hazards.

The game was designed to be simple, lightweight and easy to play, while still offering a small challenge through battery management and obstacle avoidance.

<img width="860" height="584" alt="Ekran görüntüsü_2026-06-06_01-47-49" src="https://github.com/user-attachments/assets/74797571-0ec5-427f-94f3-014bd9ca482b" />

<img width="1290" height="754" alt="Ekran görüntüsü_2026-06-06_01-48-16" src="https://github.com/user-attachments/assets/6a489c49-982a-4c8a-862b-362a5e6d0a1f" />

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
sudo dpkg -i cardboardcircuit.1.0.0.deb
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
