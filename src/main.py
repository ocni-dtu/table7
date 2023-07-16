import csv
import io
import json
import uuid
from datetime import datetime
from pathlib import Path

from epdx.pydantic import EPD, Standard, SubType, Unit


class EPDx(EPD):

    @classmethod
    def from_dict(cls, table7_object: dict):
        declared_factor = float(table7_object.get("Deklareret faktor (FU)"))
        epd = cls(
            id=convert_lcabyg_id(table7_object.get("Sorterings ID")),
            format_version="0.2.8",
            name=table7_object.get("Navn DK"),
            version="version 2 - 201222",
            declared_unit=convert_unit(table7_object.get("Deklareret enhed (FU)")),
            valid_until=datetime(year=2025, month=12, day=22),
            published_date=datetime(year=2020, month=12, day=22),
            source="BR18 - Tabel 7",
            standard=Standard.EN15804A1,
            subtype=convert_subtype(table7_object.get("Data type")),
            comment=table7_object.get("Sorterings ID"),
            reference_service_life=None,
            location="DK",
            conversions=[
                {"to": Unit.KG,
                 "value": float(table7_object.get("Masse faktor")) * declared_factor}
            ],
            gwp={
                "a1a3": convert_gwp(
                    table7_object.get("Global Opvarmning, modul A1-A3"),
                    float(table7_object.get("Deklareret faktor (FU)"))
                ),
                "a4": None,
                "a5": None,
                "b1": None,
                "b2": None,
                "b3": None,
                "b4": None,
                "b5": None,
                "b6": None,
                "b7": None,
                "c1": None,
                "c2": None,
                "c3": convert_gwp(table7_object.get("Global Opvarmning, modul C3"), declared_factor),
                "c4": convert_gwp(table7_object.get("Global Opvarmning, modul C4"), declared_factor),
                "d": convert_gwp(table7_object.get("Global Opvarmning, modul D"), declared_factor),
            },
            meta_fields={"data_source": table7_object.get("Url (link)")},
        )
        return epd


def main(path: Path, out_path: Path):
    reader = csv.DictReader(io.StringIO(path.read_text()))

    for row in reader:
        parse_row(row, out_path)


def parse_row(row: dict, out_path: Path):
    if row.get("Sorterings ID").startswith("#S"):
        return
    epd = EPDx.from_dict(row)

    (out_path / f"{epd.id}.json").write_text(epd.json(ensure_ascii=False, indent=2))


def convert_lcabyg_id(bpst_id: str) -> str:
    _map = json.loads(Path("lcabyg_tabel7_map.json").read_text())
    return _map.get(bpst_id, str(uuid.uuid4()))


def convert_unit(unit: str) -> Unit:
    match unit:
        case "STK":
            return Unit.PCS
        case "M":
            return Unit.M
        case "M2":
            return Unit.M2
        case "M3":
            return Unit.M3
        case "KG":
            return Unit.KG
        case "L":
            return Unit.L
        case _:
            return Unit.UNKNOWN


def convert_subtype(subtype: str) -> SubType:
    _map = {
        "Generisk data": SubType.Generic,
        "Branche data": SubType.Industry,
    }
    return _map.get(subtype)


def convert_gwp(gwp: str, declared_factor: float) -> float | None:
    if gwp == "-":
        return None
    else:
        return float(gwp) / declared_factor


if __name__ == "__main__":
    p = Path("tabel7.csv")
    out = Path(__file__).parent.parent / "table7"
    main(p, out)
