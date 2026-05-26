from pathlib import Path

from SAIN_OMEGA_CINEMA_ENGINE.ui.app import SAINOmegaUI
from SAIN_OMEGA_CINEMA_ENGINE.storage.paths import SAINPaths


def run() -> None:
    paths = SAINPaths(root=Path(__file__).resolve().parent)
    paths.bootstrap()
    app = SAINOmegaUI(paths=paths)
    app.launch()


if __name__ == '__main__':
    run()
