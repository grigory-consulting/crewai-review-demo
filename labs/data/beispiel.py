"""Kleine Auswertung von Messreihen (Übungsdatei für Lab 1)."""

from statistics import mean


def mittelwert(werte: list[float]) -> float:
    """Arithmetisches Mittel einer nicht leeren Liste."""
    if not werte:
        raise ValueError("Liste ist leer")
    return mean(werte)


def spanne(werte: list[float]) -> float:
    """Differenz zwischen größtem und kleinstem Wert."""
    return max(werte) - min(werte)


class Messreihe:
    """Sammelt Messwerte und liefert einfache Kennzahlen."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.werte: list[float] = []

    def hinzufuegen(self, wert: float) -> None:
        self.werte.append(wert)

    def bericht(self) -> str:
        return f"{self.name}: n={len(self.werte)}, mittel={mittelwert(self.werte):.2f}"


if __name__ == "__main__":
    reihe = Messreihe("Temperatur")
    for w in (21.5, 22.0, 20.8):
        reihe.hinzufuegen(w)
    print(reihe.bericht())
