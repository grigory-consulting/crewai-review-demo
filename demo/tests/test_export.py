from shop.cart import Warenkorb
from shop.export import export_csv


def test_export_csv(tmp_path):
    korb = Warenkorb()
    korb.hinzufuegen("Kabel", 4.5, 3)
    ziel = export_csv(korb, str(tmp_path / "korb.csv"))
    zeilen = (tmp_path / "korb.csv").read_text(encoding="utf-8").splitlines()
    assert zeilen[0] == "artikel;einzelpreis;menge;summe"
    assert zeilen[-1].endswith("13.50")
    assert ziel.endswith("korb.csv")
