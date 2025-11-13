"""Compatibility entry point for local project checks."""

from manik_bot import __version__


def main() -> None:
    """Print the current application version."""
    print(f"Manik Bot {__version__}")


if __name__ == "__main__":
    main()
