# shop

Kleines Beispielpaket für das Seminar: Warenkorb mit Preislogik.

- `shop/pricing.py`: Rundung, Bruttopreis, prozentualer Rabatt
- `shop/cart.py`: `Warenkorb` mit Positionen, Zwischensumme und Gesamtsumme
- `tests/test_cart.py`: Tests (`python -m pytest`)

## Fachliche Regeln

- Alle Beträge werden kaufmännisch auf zwei Nachkommastellen gerundet.
- Geplante Rabattstaffel (noch nicht umgesetzt): ab 100 Euro 5 %, ab 500 Euro 10 %,
  ab 1000 Euro 15 %. "Ab" schließt die Grenze ein: 100,00 Euro erhalten bereits 5 %.
