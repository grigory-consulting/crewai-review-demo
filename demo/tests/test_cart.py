import pytest

from shop.cart import Warenkorb
from shop.pricing import brutto, rabatt_anwenden


def test_zwischensumme():
    korb = Warenkorb()
    korb.hinzufuegen("Tastatur", 49.99, 2)
    korb.hinzufuegen("Maus", 19.5)
    assert korb.zwischensumme() == 119.48


def test_gesamtsumme_mit_rabatt():
    korb = Warenkorb()
    korb.hinzufuegen("Monitor", 200.0)
    assert korb.gesamtsumme(rabatt_prozent=10) == 180.0


def test_rabatt_grenzen():
    with pytest.raises(ValueError):
        rabatt_anwenden(100.0, 120)


def test_brutto():
    assert brutto(100.0) == 119.0
