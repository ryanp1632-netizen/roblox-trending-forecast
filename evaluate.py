"""Chronological backtests and output validation, without future training data."""
import argparse
import collections
import json
import math
from pathlib import Path
from main import baseline, forecast, timestamp


def score(prediction, actual):
    lookup = {(row["place"], row["universe_id"]): row["p"] for row in prediction["probabilities"]}
    sums = collections.defaultdict(float)
    names = collections.defaultdict(set)
    for row in prediction["probabilities"]:
        sums[row["place"]] += row["p"]
        names[row["place"]].add(row["universe_id"])
    total = 0
    for row in actual["top_trending"]:
        place = row["rank"]
        if place > 10:
            continue
        unnamed = max(1, len(actual["top_trending"]) - len(names[place] & {r["universe_id"] for r in actual["top_trending"]}))
        p = lookup.get((place, row["universe_id"]), (1 - sums[place]) / unnamed)
        total += math.log(max(.0001, p))
    return total


def validate(prediction):
    assert set(prediction) == {"probabilities", "top10"}
    assert len(prediction["top10"]) == len(set(prediction["top10"])) == 10
    seen = set()
    sums = collections.defaultdict(float)
    counts = collections.Counter()
    for row in prediction["probabilities"]:
        assert set(row) == {"universe_id", "place", "p"}
        key = row["place"], row["universe_id"]
        assert key not in seen and 1 <= row["place"] <= 10
        assert math.isfinite(row["p"]) and 0 <= row["p"] <= 1
        seen.add(key)
        sums[row["place"]] += row["p"]
        counts[row["place"]] += 1
    assert all(0 < value <= 1 for value in sums.values())
    assert all(value <= 100 for value in counts.values())
    assert len(json.dumps(prediction).encode()) <= 1048576


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("history", type=Path)
    args = parser.parse_args()
    history = [json.loads(line) for line in args.history.read_text(encoding="utf-8").splitlines() if line.strip()]
    results = []
    for cutoff in range(8, len(history) - 1):
        past = history[:cutoff]
        now = timestamp(past[-1]["at"])
        future = [row for row in history[cutoff:] if 0 < timestamp(row["at"]) - now <= 86400]
        if not future:
            continue
        prediction = forecast(past)
        validate(prediction)
        assert prediction == forecast(past)
        results.append((sum(score(prediction, row) for row in future) / len(future),
                        sum(score(baseline(past), row) for row in future) / len(future)))
    validate(forecast(history))
    print(json.dumps(dict(cutoffs=len(results), model=sum(a for a, b in results) / len(results),
                         baseline=sum(b for a, b in results) / len(results),
                         wins=sum(a > b for a, b in results)), indent=2))
