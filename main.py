"""Offline, deterministic rank-transition forecast. Python 3.13, stdlib only."""

import datetime as dt
import json
import math
import os
from pathlib import Path
import statistics


def timestamp(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def chart(snapshot):
    return {int(row["universe_id"]): row for row in snapshot["top_trending"]}


def baseline(history, places=10):
    rows = sorted(history[-1]["top_trending"], key=lambda row: row["rank"])
    result = []
    for place in range(1, places + 1):
        for rank, probability in ((place, .5), (place - 1, .15),
                                  (place + 1, .3 if place == 1 else .15)):
            if 1 <= rank <= len(rows):
                result.append(dict(universe_id=int(rows[rank - 1]["universe_id"]),
                                   place=place, p=probability))
    return dict(probabilities=result,
                top10=[int(row["universe_id"]) for row in rows[:places]])


def transition_counts(charts, times, places):
    """Aggregate by source rank once, including games that leave the chart."""
    counts = {}
    totals = {}
    for i, old in enumerate(charts):
        for j in range(i + 1, len(charts)):
            hours = (times[j] - times[i]) / 3600
            if not 12 <= hours <= 48:
                continue
            pair_weight = math.exp(-abs(hours - 24) / 16)
            pair_weight *= math.exp(-(times[-1] - times[j]) / (10 * 86400))
            for uid, row in old.items():
                rank = int(row["rank"])
                target = charts[j].get(uid, {}).get("rank", 101)
                evidence = counts.setdefault(rank, [0.0] * places)
                totals[rank] = totals.get(rank, 0.0) + pair_weight
                for place in range(1, places + 1):
                    evidence[place - 1] += pair_weight * math.exp(
                        -.5 * ((place - target) / .65) ** 2) / 1.63
    return counts, totals


def forecast(history, places=10, persistence=.3, momentum_strength=.8):
    """Combine smoothed transitions, bounded momentum and persistence."""
    times = [timestamp(snapshot["at"]) for snapshot in history]
    charts = [chart(snapshot) for snapshot in history]
    latest = charts[-1]
    candidates = set(sorted(latest, key=lambda uid: (latest[uid]["rank"], uid))[:70])
    for old in charts[-5:-1]:
        candidates.update(uid for uid, row in old.items() if row["rank"] <= 15)
    candidates = sorted(candidates, key=lambda uid: (
        latest.get(uid, {}).get("rank", 101), uid))[:90]
    candidates.sort()
    if len(candidates) < places:
        raise ValueError("History must contain enough distinct games for top10")
    reference_index = min(range(len(times)), key=lambda i: abs(
        times[-1] - times[i] - 24 * 3600))
    previous = charts[reference_index]
    elapsed = max(1.0, (times[-1] - times[reference_index]) / 3600)
    momentum_scale = min(2.0, 24.0 / elapsed)
    changes = [
        math.log((row.get("playing") or 0) + 100) -
        math.log((previous[uid].get("playing") or 0) + 100)
        for uid, row in latest.items() if uid in previous
    ]
    market_change = statistics.median(changes) if changes else 0
    counts, totals = transition_counts(charts, times, places)
    scores = {place: {} for place in range(1, places + 1)}
    for uid in candidates:
        row = latest.get(uid, {})
        rank = int(row.get("rank", 85))
        old_row = previous.get(uid)
        shift = 0.0
        if old_row and row:
            growth = (math.log((row.get("playing") or 0) + 100) -
                      math.log((old_row.get("playing") or 0) + 100) -
                      market_change) * momentum_scale
            shift = momentum_strength * max(-2, min(2, growth))
            shift += .12 * max(-4, min(4, old_row["rank"] - rank))
            if row.get("up_votes") is not None and old_row.get("up_votes") is not None:
                votes = math.log((row["up_votes"] + 100) / (old_row["up_votes"] + 100))
                shift += .2 * max(-1, min(1, votes))
        center = max(1, rank - shift)
        width = 1.6 + .10 * min(rank, 30)
        evidence = [0.0] * places
        total_weight = 0.0
        for source_rank in range(max(1, rank - 2), rank + 3):
            weight = math.exp(-abs(source_rank - rank))
            total_weight += weight * totals.get(source_rank, 0.0)
            for index, value in enumerate(counts.get(source_rank, [0.0] * places)):
                evidence[index] += weight * value
        for place in scores:
            prior = math.exp(-.5 * ((place - center) / width) ** 2)
            prior /= width * math.sqrt(2 * math.pi)
            empirical = (evidence[place - 1] + 8 * prior) / (total_weight + 8)
            stay = .5 if rank == place else (
                .3 if place == 1 and rank == 2 else
                .15 if abs(rank - place) == 1 else 0)
            scores[place][uid] = persistence * stay + (
                1 - persistence) * (.65 * empirical + .35 * prior)
    probabilities = []
    named_mass = .92
    candidate_floor_share = .015
    for place, weights in scores.items():
        denominator = sum(weights.values())
        for uid in candidates:
            probability = named_mass * (
                (1 - candidate_floor_share) * weights[uid] / denominator +
                candidate_floor_share / len(candidates))
            probabilities.append(dict(
                universe_id=uid, place=place, p=round(probability, 12)))
    chosen = []
    for place in scores:
        uid = max((uid for uid in candidates if uid not in chosen),
                  key=lambda uid: (scores[place][uid], -uid))
        chosen.append(uid)
    return dict(probabilities=probabilities, top10=chosen)


def main():
    input_dir = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
    output_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    task = json.loads((input_dir / "task.json").read_text(encoding="utf-8"))
    history = [json.loads(line) for line in (input_dir / "history.ndjson").read_text(encoding="utf-8").splitlines() if line.strip()]
    cutoff = timestamp(task["history_until"])
    history = sorted((row for row in history if row.get("ok", True) and timestamp(row["at"]) < cutoff),
                     key=lambda row: timestamp(row["at"]))
    if not history:
        raise ValueError("No valid pre-cutoff chart history")
    result = forecast(history, int(task["places"]))
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / task["output"]).write_text(json.dumps(result, separators=(",", ":"), allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
