"""Preislogik des Shops: Rundung, Bruttopreis und prozentualer Rabatt."""
from decimal import ROUND_HALF_UP, Decimal

MWST_SATZ = 0.19


def runde_betrag(betrag: float) -> float:
    """Rundet kaufmännisch auf zwei Nachkommastellen."""
    return float(Decimal(str(betrag)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def brutto(netto: float, satz: float = MWST_SATZ) -> float:
    """Bruttopreis aus Nettopreis und Mehrwertsteuersatz."""
    return runde_betrag(netto * (1 + satz))


def rabatt_anwenden(betrag: float, prozent: float) -> float:
    """Zieht einen Rabatt in Prozent (0 bis 100) ab und rundet das Ergebnis."""
    if not 0 <= prozent <= 100:
        raise ValueError("Rabatt muss zwischen 0 und 100 Prozent liegen")
    return runde_betrag(betrag * (1 - prozent / 100))


# Rabattstaffel: (Mindestbetrag in Euro, Rabatt in Prozent), absteigend sortiert.
STAFFEL = [(1000, 15), (500, 10), (100, 5)]


def staffel_prozent(betrag: float) -> float:
    """Liefert den Rabattsatz laut Staffel (siehe README: ab 100/500/1000 Euro)."""
    for grenze, prozent in STAFFEL:
        if betrag > grenze:
            return prozent
    return 0.0


def staffel_rabatt(betrag: float) -> float:
    """Wendet die Rabattstaffel an und liefert den reduzierten Betrag."""
    return betrag - betrag * staffel_prozent(betrag) / 100
