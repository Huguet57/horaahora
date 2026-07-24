from backend.domain.calculator.table import ScoreTable


class CastellNormalizer:
    EXPLICIT_ALIASES = {
        "4de9net": "4de9sf",
        "2de8net": "2de8sf",
        "3de9net": "3de9sf",
        "pde7net": "Pde7sf",
        "4de9af": "4de9fa",
        "3de9af": "3de9fa",
        "2de9f": "2de9sm",
        "3de10f": "3de10sm",
        "4de10f": "4de10sm",
    }
    CONVENTIONAL_OMISSIONS = {
        "2de8": "2de8f",
        "3de9": "3de9f",
        "4de9": "4de9f",
        "5de9": "5de9f",
        "7de9": "7de9f",
        "9de9": "9de9f",
        "Pde7": "Pde7f",
        "2de9": "2de9fm",
        "Pde8": "Pde8fm",
        "3de10": "3de10fm",
        "4de10": "4de10fm",
        "2de10": "2de10fmp",
        "Pde9": "Pde9fmp",
    }

    def __init__(self, table: ScoreTable) -> None:
        self.table = table
        self.aliases = dict(self.EXPLICIT_ALIASES)
        for canonical in table.scores:
            lower = canonical.lower()
            if lower.endswith("fa"):
                stem = lower[:-2]
                for suffix in ("fp", "af", "pf"):
                    self.aliases[stem + suffix] = canonical
            elif lower.endswith("a"):
                self.aliases[lower[:-1] + "p"] = canonical

            if lower.endswith("sf"):
                stem = lower[:-2]
                self.aliases[stem + "net"] = canonical
                self.aliases[stem + "n"] = canonical

    def normalize(self, notation: str) -> str | None:
        value = notation.strip().lower().replace(" ", "")
        value = value.replace("/", "d").replace("x", "d").replace("×", "d")
        if value.startswith("tde"):
            value = "2de" + value[3:]
        elif value.startswith("td"):
            value = "2d" + value[2:]
        elif value.startswith("t") and len(value) > 1 and value[1].isdigit():
            value = "2d" + value[1:]

        if value.startswith("pd") and not value.startswith("pde"):
            value = "pde" + value[2:]
        elif value.startswith("p") and len(value) > 1 and value[1].isdigit():
            value = "pde" + value[1:]
        else:
            head, separator, tail = value.partition("d")
            if separator and not value.startswith("p") and not value.startswith(f"{head}de"):
                value = f"{head}de{tail}"

        value = self.aliases.get(value, value)
        canonical = "P" + value[1:] if value.startswith("pde") else value
        canonical = self.CONVENTIONAL_OMISSIONS.get(canonical, canonical)
        return canonical if self.table.contains(canonical) else None

    @staticmethod
    def structure_key(canonical: str) -> str:
        shared_structures = {
            "4de9f": "4de9",
            "4de9sf": "4de9",
            "2de8f": "2de8",
            "2de8sf": "2de8",
            "3de9f": "3de9",
            "3de9sf": "3de9",
            "Pde7f": "Pde7",
            "Pde7sf": "Pde7",
            "2de9fm": "2de9",
            "2de9sm": "2de9",
            "3de10fm": "3de10",
            "3de10sm": "3de10",
            "4de10fm": "4de10",
            "4de10sm": "4de10",
        }
        return shared_structures.get(canonical, canonical)
