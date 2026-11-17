"""Start the SmartMetro desktop simulator."""


def main() -> None:
    try:
        from ui.main_window import SmartMetroApp
    except ModuleNotFoundError as exc:
        if exc.name in {"customtkinter", "PIL"}:
            raise SystemExit(
                "Install dependencies with: python -m pip install -r requirements.txt"
            ) from exc
        raise
    SmartMetroApp().mainloop()


if __name__ == "__main__":
    main()
