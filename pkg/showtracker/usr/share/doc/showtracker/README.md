# ShowTracker - minimal CLI series progress tracking tool.

(I just wanted to see how much is possible with the free credits of copilot they give you in a day - turns out it's far more than this)

## Usage examples:
  python3 showtracker.py add show "Stranger Things" S3E02
  python3 showtracker.py "Stranger Things"       # increment episode
  python3 showtracker.py "The Hobbit" 12        # set chapter to 12
  python3 showtracker.py "Stranger Things" ns    # start next season

DB: ~/.local/share/showtracker.db (override with SHOWTRACKER_DB)

## Building & installing on Arch (makepkg):
  makepkg        # builds package
  sudo pacman -U ./showtracker-0.1.0-1-any.pkg.tar.zst

## To build and install in one step:
  makepkg -si

## To install without packaging (copy to /usr/local/bin):
  sudo install -Dm755 showtracker.py /usr/local/bin/showtracker

## Development:
  pytest
