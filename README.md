# Roblox chart transition forecast

An offline forecast for make.fun's Roblox Top Trending competition. Python 3.13;
standard library only, no installation, network requests or random numbers.

## Model

Starting from the kit's MIT-licensed persistence baseline, this entry learns
rank transitions from historical snapshot pairs 12–48 hours apart, weighted
toward a 24-hour gap. Nearby source ranks share evidence. A smooth rank prior
regularizes the small sample, and the baseline remains part of the mixture.

Player-count growth is measured relative to the chart's median growth to reduce
time-of-day effects. Its influence is bounded, combined with recent rank changes
and vote growth when available. Candidates include games beyond the top ten and
recently missing top games. Each place assigns 92% to explicit candidates and
leaves 8% for unnamed games, with positive support for all named candidates.

The program reads the task's cutoff and excludes all snapshots at or after it.
It emits one distribution for the entire forecast window, as required by the
competition, rather than fabricating separate hourly answers.

## Run

Set `MAKEFUN_INPUT_DIR` to a directory containing `task.json` and
`history.ndjson`, and `MAKEFUN_OUTPUT_DIR` to an output directory. Run
`python main.py`. In the grading container, the default paths are `/input`
and `/output`. The output filename is read from the task.

## Validation

Run `python evaluate.py PATH/TO/history.ndjson` for chronological expanding-window
backtests. Each prediction uses only the prefix before its test window. Validation
checks determinism, unique game/place pairs, probability sums, row counts, file
size, and ten distinct top predictions. These historical windows overlap and are
not independent evidence of future performance.

The public kit withholds the scorer and reference outcomes. Its `grade-local`
command refuses this competition; the official practice score is available only
after submission to make.fun. Historical backtests do not guarantee a prize or
that the final forecast will beat either house entry.

## License and attribution

MIT. Baseline weighting and the starting license are derived from the official
make.fun `roblox-trending-forecast-01` starter kit. No historical dataset is
embedded in this repository; the grader supplies it at runtime.
