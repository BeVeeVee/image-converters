import curses
from pathlib import Path
from cairosvg import svg2png


def pick_svg_file(start_dir: str = ".") -> Path | None:
    def _menu(stdscr):
        curses.curs_set(0)
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)

        current_dir = Path(start_dir).resolve()
        index = 0

        while True:
            entries: list[tuple[str, Path, bool]] = []
            if current_dir.parent != current_dir:
                entries.append((".. (up a folder)", current_dir.parent, True))

            items = sorted(
                current_dir.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())
            )
            for item in items:
                if item.is_dir():
                    entries.append((f"{item.name}/", item, True))
                elif item.is_file() and item.suffix.lower() == ".svg":
                    entries.append((item.name, item, False))

            if not entries:
                entries.append(
                    ("(no .svg files or folders here)", current_dir, False))

            index = max(0, min(index, len(entries) - 1))

            stdscr.clear()
            height, width = stdscr.getmaxyx()

            header = f"Folder: {current_dir}  [Up/Down: move, Enter: open/select, q: quit]"
            stdscr.addnstr(0, 0, header, width - 1, curses.A_BOLD)

            max_rows = max(1, height - 3)
            scroll_offset = max(0, index - max_rows + 1)

            for row_idx in range(max_rows):
                entry_idx = row_idx + scroll_offset
                if entry_idx >= len(entries):
                    break

                label, _, _ = entries[entry_idx]
                y = row_idx + 2
                attr = curses.color_pair(
                    1) if entry_idx == index else curses.A_NORMAL
                stdscr.addnstr(y, 0, f"  {label}", width - 1, attr)

            stdscr.refresh()
            key = stdscr.getch()

            if key == curses.KEY_UP:
                index = (index - 1) % len(entries)
            elif key == curses.KEY_DOWN:
                index = (index + 1) % len(entries)
            elif key in (curses.KEY_ENTER, 10, 13):
                label, target, is_dir = entries[index]
                if label.startswith("("):
                    continue
                if is_dir:
                    current_dir = target
                    index = 0
                else:
                    return target
            elif key in (ord("q"), ord("Q"), 27):
                return None

    return curses.wrapper(_menu)


def prompt_output_filename(source_path: Path) -> str:
    """Ask the user for the output PNG filename, defaulting to <stem>.png."""
    default_path = source_path.with_suffix(".png")
    raw = input(
        f"Output PNG filename [{default_path.name}] (in {source_path.parent}): "
    ).strip()

    if not raw:
        return str(default_path)

    chosen = Path(raw)
    if chosen.suffix.lower() != ".png":
        chosen = chosen.with_suffix(".png")

    # If only a filename was typed, save it alongside the source SVG
    if len(chosen.parts) == 1:
        chosen = source_path.parent / chosen

    return str(chosen)


def load_svg(file_path: Path) -> bytes:
    """Read SVG file bytes."""
    return file_path.read_bytes()


def convert_image(svg_code: bytes, filename: str) -> None:
    svg2png(bytestring=svg_code, write_to=filename)
    print(f"Saved PNG to: {filename}")


def main() -> None:
    selected_path = pick_svg_file(".")
    if not selected_path:
        print("No file selected.")
        return

    svg_code = load_svg(selected_path)
    output_filename = prompt_output_filename(selected_path)
    convert_image(svg_code, output_filename)


if __name__ == "__main__":
    main()
