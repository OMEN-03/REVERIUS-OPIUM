import sys

from core import app as reverius_app


def main() -> int:
    try:
        reverius_app.apply_theme(reverius_app.current_personality)
    except Exception:
        pass
    reverius_app.start_omen()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
