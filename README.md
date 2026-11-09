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

## Run on Windows

Install Python 3.13, then open PowerShell in this repository.
Point the input variable to the kit's input folder.
Choose a separate output directory for the generated forecast.
The output filename comes from the supplied task, usually forecast.json.

```powershell
$env:MAKEFUN_INPUT_DIR = 'C:/path/to/kit/input'
$env:MAKEFUN_OUTPUT_DIR = 'C:/path/to/forecast-output'
python main.py
```

## Run on Linux or in the grader

The grader invokes Python with the repository as a read-only bot directory.
Input defaults to /input and output defaults to /output.
No dependency installation or downloaded data is needed.
For a local run, override both paths as shown below.

```sh
MAKEFUN_INPUT_DIR=/path/to/kit/input MAKEFUN_OUTPUT_DIR=/tmp/forecast python3 main.py
```

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

### Historical measurements

The supplied practice history contains 26 chart snapshots.
Evaluation starts after the first eight observations.
Each cutoff forecasts reads in its following 24 hours.
There are 17 usable cutoffs under this procedure.
The model wins at 12 cutoffs against persistence.
Its average score is -18.691347 nats.
The starter's average score is -22.085969 nats.
Higher scores are better under this metric.
These figures are backtests, not the official practice grade.
Two full program runs also produced byte-identical forecast files.

### Distribution details

The explicit candidate set has at most 90 games per place.
Latest-chart candidates come from its first 70 ranks.
Recent top-15 games can return even after disappearing.
Every named candidate receives positive probability.
The explicit probability mass is 0.92 at each place.
The remaining 0.08 supports unnamed games under the competition's rules.
Candidate probabilities are rounded to twelve decimal places.
Only the prescribed probabilities and top10 keys are written.
The top10 list uses distinct games and deterministic tie breaking.
Transition counts include departures instead of conditioning only on survivors.
Player growth is scaled to a day when read intervals differ.

## License and attribution

MIT. Baseline weighting and the starting license are derived from the official
make.fun `roblox-trending-forecast-01` starter kit. No historical dataset is
embedded in this repository; the grader supplies it at runtime.
