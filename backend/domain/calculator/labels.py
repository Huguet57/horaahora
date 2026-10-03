from collections import defaultdict

from backend.domain.calculator.models import Outcome, ParsedPerformance


def meaningful_performance_labels(performances: list[ParsedPerformance]) -> list[str]:
    if len(performances) < 2:
        return [performance.label for performance in performances]

    notation_sets = [
        {_compact(castell.notation) for castell in performance.castells}
        for performance in performances
    ]
    labels: list[str | None] = []
    used = {
        _compact(performance.label) for performance in performances if not _is_generic(performance)
    }

    for index, performance in enumerate(performances):
        if not _is_generic(performance):
            labels.append(performance.label.strip())
            continue
        other_notations = set().union(
            *(values for other_index, values in enumerate(notation_sets) if other_index != index)
        )
        distinctive = next(
            (
                castell.notation.strip()
                for castell in performance.castells
                if _compact(castell.notation) not in other_notations
            ),
            None,
        )
        proposed = f"Amb {distinctive}" if distinctive else None
        if proposed and _compact(proposed) not in used:
            labels.append(proposed)
            used.add(_compact(proposed))
        else:
            labels.append(None)

    for index, label in enumerate(labels):
        if label is not None:
            continue
        fallback_index = index
        while True:
            fallback = (
                chr(ord("A") + fallback_index) if fallback_index < 26 else f"A{fallback_index + 1}"
            )
            if _compact(fallback) not in used:
                break
            fallback_index += 1
        labels[index] = fallback
        used.add(_compact(fallback))
    return _tell_apart_repeated(performances, [label for label in labels if label is not None])


def _tell_apart_repeated(performances: list[ParsedPerformance], labels: list[str]) -> list[str]:
    """Variants the model names alike («Nosaltres» ×4) get what sets each one apart."""
    groups: dict[str, list[int]] = defaultdict(list)
    for index, label in enumerate(labels):
        groups[_compact(label)].append(index)
    result = list(labels)
    for indexes in groups.values():
        if len(indexes) < 2:
            continue
        notation_sets = [
            {_compact(castell.notation) for castell in performances[index].castells}
            for index in indexes
        ]
        if all(notations == notation_sets[0] for notations in notation_sets):
            proposed = [
                f"{labels[index]}: {_outcomes_described(performances[index])}" for index in indexes
            ]
        else:
            proposed = []
            for position, index in enumerate(indexes):
                others = set().union(
                    *(values for other, values in enumerate(notation_sets) if other != position)
                )
                distinctive = next(
                    (
                        castell.notation.strip()
                        for castell in performances[index].castells
                        if _compact(castell.notation) not in others
                    ),
                    None,
                )
                proposed.append(f"{labels[index]} amb {distinctive}" if distinctive else "")
        if all(proposed) and len({_compact(label) for label in proposed}) == len(proposed):
            for index, label in zip(indexes, proposed, strict=True):
                result[index] = label
        else:
            for position, index in enumerate(indexes):
                result[index] = f"{labels[index]} ({chr(ord('A') + position % 26)})"
    return result


def _outcomes_described(performance: ParsedPerformance) -> str:
    parts = []
    for outcome, singular, plural in (
        (Outcome.LOADED, "carregat", "carregats"),
        (Outcome.ATTEMPT, "intent", "intents"),
    ):
        notations = [
            castell.notation.strip()
            for castell in performance.castells
            if castell.outcome is outcome
        ]
        if notations:
            names = (
                notations[0]
                if len(notations) == 1
                else ", ".join(notations[:-1]) + f" i {notations[-1]}"
            )
            parts.append(f"{names} {singular if len(notations) == 1 else plural}")
    return ", ".join(parts) or "tot descarregat"


def _is_generic(performance: ParsedPerformance) -> bool:
    compact = _compact(performance.label)
    if not compact:
        return True
    if len(compact) == 1 and compact.isalpha():
        return True
    parts = compact.split()
    if len(parts) == 2 and parts[0] in {
        "costat",
        "opció",
        "opcio",
        "actuació",
        "actuacio",
    }:
        return parts[1].isdigit() or (len(parts[1]) == 1 and parts[1].isalpha())
    notations = {_compact(item.notation).replace(" ", "") for item in performance.castells}
    return compact.replace(" ", "") in notations


def _compact(value: str) -> str:
    return " ".join(value.casefold().split())
