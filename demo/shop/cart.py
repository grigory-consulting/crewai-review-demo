"""Warenkorb mit Positionen, Zwischensumme und Gesamtsumme."""
from dataclasses import dataclass, field

from shop.pricing import rabatt_anwenden, runde_betrag, staffel_rabatt


@dataclass
class Position:
    artikel: str
    einzelpreis: float
    menge: int = 1

    def summe(self) -> float:
        return runde_betrag(self.einzelpreis * self.menge)


@dataclass
class Warenkorb:
    positionen: list[Position] = field(default_factory=list)

    def hinzufuegen(self, artikel: str, einzelpreis: float, menge: int = 1) -> None:
        if menge < 1:
            raise ValueError("Menge muss mindestens 1 sein")
        self.positionen.append(Position(artikel, einzelpreis, menge))

    def zwischensumme(self) -> float:
        return runde_betrag(sum(p.summe() for p in self.positionen))

    def gesamtsumme(self, rabatt_prozent: float = 0.0) -> float:
        """Zwischensumme abzüglich eines manuell vergebenen Rabatts."""
        return rabatt_anwenden(self.zwischensumme(), rabatt_prozent)

    def gesamtsumme_mit_staffel(self) -> float:
        """Zwischensumme abzüglich des automatischen Staffelrabatts."""
        return staffel_rabatt(self.zwischensumme())
