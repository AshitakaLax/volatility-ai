# Risk overlay measurement

## grid

### tiers

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| tiers grid none | 8.5% | 38.4% | 0.22 | +0.00 | +0.00 | +0.00 |
| tiers grid pause random 13% | 7.6% | 34.4% | 0.22 | -0.00 | -0.01 | -0.01 |
| tiers grid x0.25 | 2.8% | 15.5% | 0.18 | -0.04 | +0.02 | -0.00 |
| tiers grid x0.5 | 5.0% | 26.0% | 0.19 | -0.03 | +0.01 | -0.00 |
| tiers grid x0.75 | 6.7% | 33.6% | 0.20 | -0.02 | +0.01 | -0.01 |
| tiers grid x1.0 | 8.1% | 39.3% | 0.21 | -0.02 | +0.01 | -0.01 |
| tiers grid ceiling50 | 7.6% | 41.2% | 0.18 | -0.04 | -0.01 | -0.03 |

### oracle

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| oracle grid none | 8.5% | 38.4% | 0.22 | +0.00 | +0.00 | +0.00 |
| oracle grid worst 20% pause | 9.1% | 9.3% | 0.98 | +0.76 | +0.73 | +1.24 |
| oracle grid worst 10% pause | 9.9% | 9.3% | 1.06 | +0.84 | +0.79 | +1.37 |
| oracle grid worst 5% pause | 10.0% | 9.9% | 1.00 | +0.78 | +0.72 | +1.11 |
| oracle grid worst 10% x0.5 | 9.2% | 16.8% | 0.55 | +0.33 | +0.37 | +0.26 |
| oracle grid worst 20% x0.5 | 8.8% | 17.9% | 0.49 | +0.27 | +0.35 | +0.21 |
| oracle grid worst 5% x0.5 | 9.3% | 19.4% | 0.48 | +0.26 | +0.34 | +0.22 |

### matrix

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| matrix grid none | 8.5% | 38.4% | 0.22 | +0.00 | +0.00 | +0.00 |
| matrix grid tier0 pause | 7.2% | 39.5% | 0.18 | -0.04 | -0.08 | +0.01 |
| matrix grid tier1 pause | 6.4% | 22.3% | 0.29 | +0.07 | -0.04 | +0.05 |
| matrix grid tier3 pause | 7.2% | 36.9% | 0.20 | -0.03 | +0.13 | -0.01 |
| matrix grid tier2 pause | 7.3% | 42.3% | 0.17 | -0.05 | +0.00 | -0.03 |
| matrix grid tier2 x0.5 | 7.8% | 40.5% | 0.19 | -0.03 | -0.01 | -0.02 |
| matrix grid tier2 x0.75 | 8.1% | 39.7% | 0.20 | -0.02 | -0.01 | -0.01 |
| matrix grid tier1 x0.25 | 7.0% | 23.0% | 0.30 | +0.08 | -0.03 | +0.04 |
| matrix grid tier1 x0.75 | 8.0% | 33.1% | 0.24 | +0.02 | -0.01 | +0.01 |
| matrix grid tier3 x0.5 | 7.7% | 37.8% | 0.20 | -0.02 | +0.08 | -0.01 |
| matrix grid tier3 x0.75 | 8.0% | 38.2% | 0.21 | -0.01 | +0.05 | -0.01 |
| matrix grid tier0 x0.25 | 7.5% | 39.1% | 0.19 | -0.03 | -0.05 | +0.01 |
| matrix grid tier0 x0.75 | 8.2% | 38.6% | 0.21 | -0.01 | -0.02 | +0.00 |
| matrix grid tier3 x0.25 | 7.5% | 37.4% | 0.20 | -0.02 | +0.12 | -0.01 |
| matrix grid tier2 x0.25 | 7.6% | 41.4% | 0.18 | -0.04 | -0.00 | -0.03 |
| matrix grid tier1 x0.5 | 7.5% | 27.5% | 0.27 | +0.05 | -0.02 | +0.02 |
| matrix grid tier0 x0.5 | 7.9% | 38.9% | 0.20 | -0.02 | -0.03 | +0.01 |

### proxy

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| proxy grid none | 8.5% | 38.4% | 0.22 | +0.00 | +0.00 | +0.00 |
| proxy grid graded | 5.9% | 32.6% | 0.18 | -0.04 | +0.09 | -0.02 |
| proxy grid binary | 7.1% | 37.7% | 0.19 | -0.03 | +0.10 | -0.01 |
| proxy grid continuous | 6.5% | 36.0% | 0.18 | -0.04 | +0.07 | -0.02 |
| proxy grid ceiling | 7.8% | 39.3% | 0.20 | -0.02 | +0.09 | -0.01 |

### spacing

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| spacing grid none | 8.5% | 38.4% | 0.22 | +0.00 | +0.00 | +0.00 |
| spacing grid B + tiers | 5.7% | 32.5% | 0.17 | -0.05 | +0.09 | -0.03 |
| spacing grid B e1.0 max2.0 follow=True | 9.1% | 42.9% | 0.21 | -0.01 | -0.03 | +0.00 |
| spacing grid B e1.0 max4.0 follow=False | 7.7% | 39.4% | 0.20 | -0.03 | +0.01 | -0.01 |
| spacing grid B e0.5 max2.0 follow=False | 7.9% | 39.2% | 0.20 | -0.02 | +0.01 | -0.01 |
| spacing grid B e1.0 max2.0 follow=False | 7.7% | 39.3% | 0.20 | -0.03 | +0.01 | -0.01 |
| spacing grid B e0.5 max4.0 follow=True | 8.6% | 41.0% | 0.21 | -0.01 | +0.00 | -0.00 |
| spacing grid B e0.5 max4.0 follow=False | 7.9% | 39.2% | 0.20 | -0.02 | +0.01 | -0.01 |
| spacing grid B e1.0 max4.0 follow=True | 9.2% | 42.5% | 0.22 | -0.00 | -0.02 | +0.00 |
| spacing grid B e0.5 max2.0 follow=True | 8.6% | 41.0% | 0.21 | -0.01 | +0.00 | -0.00 |

### weekly

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| weekly grid none | 8.5% | 38.4% | 0.22 | +0.00 | +0.00 | +0.00 |
| weekly grid all levers | 5.7% | 32.5% | 0.17 | -0.05 | +0.09 | -0.03 |
| weekly grid G next_month slope 0.5 | 8.1% | 39.3% | 0.21 | -0.02 | +0.01 | -0.01 |
| weekly grid G max slope 0.5 | 8.1% | 39.3% | 0.21 | -0.02 | +0.01 | -0.01 |
| weekly grid G max slope 1.0 | 8.1% | 39.4% | 0.20 | -0.02 | +0.01 | -0.01 |
| weekly grid G next_month slope 0.25 | 8.1% | 39.3% | 0.21 | -0.02 | +0.01 | -0.01 |
| weekly grid G next_month slope 1.0 | 8.1% | 39.4% | 0.20 | -0.02 | +0.01 | -0.01 |
| weekly grid G next_quarter slope 1.0 | 8.1% | 39.3% | 0.21 | -0.02 | +0.01 | -0.01 |
| weekly grid G next_quarter slope 0.25 | 8.1% | 39.3% | 0.21 | -0.02 | +0.01 | -0.01 |
| weekly grid G next_quarter slope 0.5 | 8.1% | 39.3% | 0.21 | -0.02 | +0.01 | -0.01 |
| weekly grid G max slope 0.25 | 8.1% | 39.3% | 0.21 | -0.02 | +0.01 | -0.01 |
| weekly grid G every five sessions | 8.1% | 39.3% | 0.21 | -0.02 | +0.01 | -0.01 |

### null

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| null grid none | 8.5% | 38.4% | 0.22 | +0.00 | +0.00 | +0.00 |
| null grid tiers real | 5.9% | 32.6% | 0.18 | -0.04 | +0.09 | -0.02 |
| null grid tiers shift 16 | 5.3% | 41.2% | 0.13 | -0.09 | +0.06 | -0.08 |
| null grid tiers shift 06 | 6.1% | 30.1% | 0.20 | -0.02 | +0.13 | +0.00 |
| null grid tiers shift 12 | 5.9% | 21.1% | 0.28 | +0.06 | -0.06 | +0.03 |
| null grid tiers shift 05 | 5.7% | 36.6% | 0.16 | -0.07 | -0.05 | -0.07 |
| null grid tiers shift 04 | 6.1% | 27.4% | 0.22 | +0.00 | -0.07 | -0.01 |
| null grid tiers shift 14 | 6.4% | 26.1% | 0.25 | +0.03 | -0.04 | +0.04 |
| null grid tiers shift 13 | 6.8% | 27.4% | 0.25 | +0.03 | -0.14 | +0.08 |
| null grid tiers shift 07 | 6.2% | 27.6% | 0.22 | +0.00 | -0.10 | -0.00 |
| null grid tiers shift 09 | 5.9% | 27.0% | 0.22 | -0.00 | -0.08 | -0.03 |
| null grid tiers shift 19 | 6.7% | 20.9% | 0.32 | +0.10 | -0.06 | +0.12 |
| null grid tiers shift 02 | 7.6% | 38.9% | 0.19 | -0.03 | +0.07 | +0.04 |
| null grid tiers shift 18 | 5.6% | 44.3% | 0.13 | -0.09 | -0.05 | -0.07 |
| null grid tiers shift 21 | 5.9% | 27.2% | 0.21 | -0.01 | -0.03 | -0.02 |
| null grid tiers shift 01 | 6.1% | 39.6% | 0.15 | -0.07 | -0.06 | -0.03 |
| null grid tiers shift 10 | 5.7% | 38.7% | 0.15 | -0.07 | +0.00 | -0.06 |
| null grid tiers shift 20 | 5.6% | 44.3% | 0.13 | -0.09 | -0.05 | -0.07 |
| null grid tiers shift 11 | 6.0% | 43.7% | 0.14 | -0.08 | +0.02 | -0.06 |
| null grid tiers shift 03 | 6.0% | 43.7% | 0.14 | -0.08 | +0.10 | -0.06 |
| null grid tiers shift 08 | 6.7% | 39.2% | 0.17 | -0.05 | +0.22 | -0.00 |
| null grid tiers shift 17 | 5.8% | 42.2% | 0.14 | -0.08 | +0.03 | -0.03 |
| null grid tiers shift 15 | 6.2% | 44.4% | 0.14 | -0.08 | -0.11 | -0.04 |
| null grid tiers shift 00 | 6.2% | 36.9% | 0.17 | -0.05 | +0.23 | -0.02 |
| null grid tiers shift 22 | 6.1% | 35.8% | 0.17 | -0.05 | -0.08 | -0.04 |
| null grid tiers shift 24 | 6.0% | 35.5% | 0.17 | -0.05 | +0.01 | -0.03 |
| null grid tiers shift 28 | 6.7% | 29.9% | 0.22 | +0.00 | -0.11 | +0.04 |
| null grid tiers shift 32 | 5.9% | 23.0% | 0.26 | +0.04 | -0.09 | -0.00 |
| null grid tiers shift 31 | 5.8% | 38.7% | 0.15 | -0.07 | +0.11 | -0.03 |
| null grid tiers shift 23 | 5.9% | 39.1% | 0.15 | -0.07 | -0.10 | -0.04 |
| null grid tiers shift 29 | 6.7% | 26.1% | 0.26 | +0.04 | -0.06 | +0.06 |
| null grid tiers shift 25 | 6.7% | 26.1% | 0.26 | +0.04 | -0.06 | +0.06 |
| null grid tiers shift 37 | 5.9% | 35.2% | 0.17 | -0.05 | -0.02 | -0.04 |
| null grid tiers shift 33 | 6.2% | 20.5% | 0.30 | +0.08 | -0.08 | +0.08 |
| null grid tiers shift 27 | 6.4% | 35.0% | 0.18 | -0.04 | +0.00 | -0.01 |
| null grid tiers shift 34 | 7.2% | 32.2% | 0.22 | +0.00 | -0.03 | +0.04 |
| null grid tiers shift 26 | 6.5% | 42.6% | 0.15 | -0.07 | +0.01 | -0.03 |
| null grid tiers shift 38 | 6.5% | 34.3% | 0.19 | -0.03 | +0.19 | +0.01 |
| null grid tiers shift 36 | 6.0% | 23.6% | 0.25 | +0.03 | -0.13 | +0.11 |
| null grid spacing shift 00 | 7.6% | 41.6% | 0.18 | -0.04 | +0.05 | -0.01 |
| null grid tiers shift 35 | 5.7% | 39.8% | 0.14 | -0.08 | +0.11 | -0.05 |
| null grid spacing shift 02 | 8.9% | 40.4% | 0.22 | +0.00 | +0.01 | +0.04 |
| null grid tiers shift 30 | 5.7% | 34.8% | 0.16 | -0.06 | +0.15 | -0.05 |
| null grid spacing shift 01 | 7.7% | 41.4% | 0.19 | -0.04 | -0.02 | -0.01 |
| null grid spacing real | 7.7% | 39.4% | 0.20 | -0.03 | +0.01 | -0.01 |
| null grid spacing shift 03 | 7.8% | 41.1% | 0.19 | -0.03 | +0.01 | -0.02 |
| null grid tiers shift 39 | 6.4% | 26.1% | 0.25 | +0.03 | -0.04 | +0.04 |
| null grid spacing shift 04 | 7.7% | 39.0% | 0.20 | -0.02 | -0.00 | -0.02 |
| null grid spacing shift 05 | 7.6% | 38.4% | 0.20 | -0.02 | -0.01 | -0.02 |
| null grid spacing shift 06 | 7.8% | 40.3% | 0.19 | -0.03 | +0.05 | -0.01 |
| null grid spacing shift 07 | 7.6% | 37.7% | 0.20 | -0.02 | -0.02 | -0.02 |
| null grid spacing shift 09 | 7.6% | 36.8% | 0.21 | -0.01 | -0.02 | -0.01 |
| null grid spacing shift 08 | 7.9% | 41.4% | 0.19 | -0.03 | +0.07 | -0.00 |
| null grid spacing shift 13 | 7.7% | 39.0% | 0.20 | -0.02 | -0.06 | +0.01 |
| null grid spacing shift 12 | 7.8% | 38.5% | 0.20 | -0.02 | +0.00 | -0.01 |
| null grid spacing shift 10 | 7.6% | 39.9% | 0.19 | -0.03 | -0.02 | -0.02 |
| null grid spacing shift 15 | 7.7% | 41.4% | 0.19 | -0.03 | -0.05 | -0.01 |
| null grid spacing shift 11 | 7.7% | 41.2% | 0.19 | -0.03 | -0.02 | -0.02 |
| null grid spacing shift 16 | 7.5% | 40.5% | 0.19 | -0.04 | +0.06 | -0.03 |
| null grid spacing shift 17 | 7.4% | 41.7% | 0.18 | -0.04 | +0.00 | -0.01 |

*The first 60 of 124 runs; every run is in results.jsonl, and the lines below count them all.*

tiers: the real schedule beats 20 of 40 shifted copies on Calmar.

spacing: the real schedule beats 18 of 40 shifted copies on Calmar.

weekly: the real schedule beats 13 of 40 shifted copies on Calmar.

### robust

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| robust grid none | 8.5% | 38.4% | 0.22 | +0.00 | +0.00 | +0.00 |
| robust grid thresholds -0.05 | 5.2% | 33.0% | 0.16 | -0.06 | +0.04 | -0.04 |
| robust grid without tail | 5.9% | 38.0% | 0.16 | -0.06 | +0.11 | -0.04 |
| robust grid without volatility | 5.4% | 35.9% | 0.15 | -0.07 | +0.09 | -0.04 |
| robust grid reversals not exempt | 5.9% | 32.6% | 0.18 | -0.04 | +0.09 | -0.02 |
| robust grid without regime | 5.8% | 35.8% | 0.16 | -0.06 | +0.01 | -0.03 |
| robust grid thresholds +0.05 | 6.3% | 36.4% | 0.17 | -0.05 | +0.13 | -0.03 |
| robust grid without catalyst | 5.3% | 34.1% | 0.16 | -0.06 | +0.01 | -0.04 |
| robust grid without gap | 5.9% | 35.2% | 0.17 | -0.05 | +0.02 | -0.03 |

### stress

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| stress grid none | 8.5% | 38.4% | 0.22 | +0.00 | +0.00 | +0.00 |
| stress grid fast none | 8.5% | 38.3% | 0.22 | +0.00 | +0.00 | +0.00 |
| stress grid deeper none | 7.8% | 35.4% | 0.22 | +0.00 | -0.00 | -0.03 |
| stress grid twice none | 3.1% | 87.5% | 0.04 | -0.19 | +0.00 | -0.17 |
| stress grid grind none | 4.5% | 82.4% | 0.05 | -0.17 | -0.01 | -0.16 |
| stress grid fast tiers | 5.9% | 32.6% | 0.18 | -0.04 | +0.09 | -0.02 |
| stress grid deeper tiers | 5.2% | 29.9% | 0.17 | -0.05 | +0.09 | -0.06 |
| stress grid twice tiers | 2.4% | 79.6% | 0.03 | -0.19 | +0.09 | -0.16 |
| stress grid grind tiers | 3.4% | 66.0% | 0.05 | -0.17 | +0.08 | -0.15 |

fast: the tiers move max DD by -5.7 points.

deeper: the tiers move max DD by -5.5 points.

twice: the tiers move max DD by -8.0 points.

grind: the tiers move max DD by -16.4 points.

### perturb

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| perturb grid always3 | 0.0% | 0.0% | nan | +nan | +nan | +nan |
| perturb grid none | 8.5% | 38.4% | 0.22 | +0.00 | +0.00 | +0.00 |
| perturb grid inverted | 5.1% | 26.6% | 0.19 | -0.03 | -0.12 | +0.02 |
| perturb grid random 50% | 6.1% | 35.5% | 0.17 | -0.05 | -0.04 | -0.01 |
| perturb grid random 10% | 6.0% | 31.7% | 0.19 | -0.03 | +0.08 | -0.01 |
| perturb grid always0 | 8.1% | 39.3% | 0.21 | -0.02 | +0.01 | -0.01 |
| perturb grid random 25% | 5.6% | 38.8% | 0.14 | -0.08 | +0.32 | -0.05 |

### catalysts

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| catalysts grid none | 8.5% | 38.4% | 0.22 | +0.00 | +0.00 | +0.00 |
| catalysts grid blackout 15m | 8.1% | 39.4% | 0.20 | -0.02 | +0.01 | -0.01 |
| catalysts grid blackout 30m | 8.0% | 39.5% | 0.20 | -0.02 | +0.01 | -0.01 |
| catalysts grid blackout 10m | 8.1% | 39.4% | 0.20 | -0.02 | +0.01 | -0.01 |

### priority

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| priority grid none | 8.5% | 38.4% | 0.22 | +0.00 | +0.00 | +0.00 |
| priority grid supersedes neither | 6.0% | 32.2% | 0.19 | -0.04 | +0.11 | -0.02 |
| priority grid supersedes both | 5.9% | 32.6% | 0.18 | -0.04 | +0.09 | -0.02 |
| priority grid supersedes governor | 6.0% | 32.2% | 0.19 | -0.04 | +0.11 | -0.02 |

### advisory

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| advisory grid none | 8.5% | 38.4% | 0.22 | +0.00 | +0.00 | +0.00 |
| advisory grid follow 0.5 after 0m seed 7 | 7.8% | 39.8% | 0.20 | -0.03 | +0.10 | -0.02 |
| advisory grid follow 0.5 after 0m seed 16 | 7.8% | 38.4% | 0.20 | -0.02 | +0.07 | -0.01 |
| advisory grid follow 0.5 after 0m seed 17 | 7.6% | 37.5% | 0.20 | -0.02 | +0.04 | -0.01 |
| advisory grid follow 0.5 after 0m seed 14 | 8.1% | 35.4% | 0.23 | +0.01 | +0.16 | +0.02 |
| advisory grid follow 0.5 after 0m seed 2 | 8.0% | 40.1% | 0.20 | -0.02 | +0.06 | -0.01 |
| advisory grid follow 0.5 after 0m seed 15 | 8.2% | 37.1% | 0.22 | -0.00 | +0.10 | +0.01 |
| advisory grid follow 0.5 after 0m seed 19 | 7.9% | 37.1% | 0.21 | -0.01 | +0.09 | +0.00 |
| advisory grid follow 0.5 after 0m seed 6 | 8.1% | 39.9% | 0.20 | -0.02 | +0.06 | +0.00 |
| advisory grid follow 0.5 after 0m seed 12 | 7.8% | 39.8% | 0.20 | -0.03 | +0.08 | -0.01 |
| advisory grid follow 0.5 after 30m seed 0 | 8.0% | 36.9% | 0.22 | -0.00 | +0.04 | +0.01 |
| advisory grid follow 0.5 after 0m seed 4 | 8.0% | 39.3% | 0.20 | -0.02 | +0.05 | -0.01 |
| advisory grid follow 0.5 after 30m seed 2 | 8.0% | 40.1% | 0.20 | -0.02 | +0.06 | -0.01 |
| advisory grid follow 0.5 after 0m seed 5 | 7.7% | 34.4% | 0.22 | +0.00 | +0.01 | +0.00 |
| advisory grid follow 0.5 after 0m seed 11 | 7.9% | 41.6% | 0.19 | -0.03 | +0.08 | -0.01 |
| advisory grid follow 0.5 after 0m seed 9 | 7.9% | 35.4% | 0.22 | +0.00 | -0.02 | +0.01 |
| advisory grid follow 0.5 after 0m seed 3 | 8.0% | 40.3% | 0.20 | -0.02 | +0.03 | -0.01 |
| advisory grid follow 0.5 after 0m seed 13 | 7.7% | 35.5% | 0.22 | -0.01 | +0.06 | -0.00 |
| advisory grid follow 0.5 after 0m seed 0 | 8.0% | 37.0% | 0.22 | -0.00 | +0.04 | +0.01 |
| advisory grid follow 0.5 after 0m seed 1 | 7.7% | 40.2% | 0.19 | -0.03 | +0.07 | -0.02 |
| advisory grid follow 0.5 after 0m seed 18 | 7.9% | 37.9% | 0.21 | -0.01 | +0.08 | -0.00 |
| advisory grid follow 0.5 after 0m seed 8 | 8.1% | 40.8% | 0.20 | -0.02 | +0.03 | -0.00 |
| advisory grid follow 0.5 after 30m seed 1 | 7.7% | 40.2% | 0.19 | -0.03 | +0.07 | -0.02 |
| advisory grid follow 0.5 after 0m seed 10 | 7.9% | 35.9% | 0.22 | -0.00 | -0.04 | +0.00 |
| advisory grid follow 0.5 after 30m seed 3 | 8.0% | 40.3% | 0.20 | -0.02 | +0.03 | -0.00 |
| advisory grid follow 0.5 after 30m seed 9 | 7.9% | 35.4% | 0.22 | +0.00 | -0.02 | +0.01 |
| advisory grid follow 0.5 after 30m seed 5 | 7.8% | 34.5% | 0.22 | +0.00 | +0.01 | +0.00 |
| advisory grid follow 0.5 after 30m seed 4 | 8.0% | 39.3% | 0.20 | -0.02 | +0.06 | -0.01 |
| advisory grid follow 0.5 after 30m seed 6 | 8.2% | 39.9% | 0.20 | -0.02 | +0.06 | +0.00 |
| advisory grid follow 0.5 after 30m seed 10 | 7.9% | 35.9% | 0.22 | -0.00 | -0.04 | +0.01 |
| advisory grid follow 0.5 after 30m seed 11 | 7.9% | 41.6% | 0.19 | -0.03 | +0.08 | -0.01 |
| advisory grid follow 0.5 after 30m seed 7 | 7.8% | 39.8% | 0.20 | -0.02 | +0.10 | -0.01 |
| advisory grid follow 0.5 after 30m seed 15 | 8.2% | 37.1% | 0.22 | -0.00 | +0.10 | +0.01 |
| advisory grid follow 0.5 after 30m seed 14 | 8.1% | 35.4% | 0.23 | +0.01 | +0.16 | +0.02 |
| advisory grid follow 0.5 after 30m seed 8 | 8.2% | 40.8% | 0.20 | -0.02 | +0.03 | -0.00 |
| advisory grid follow 0.5 after 30m seed 19 | 7.9% | 37.0% | 0.21 | -0.01 | +0.10 | +0.00 |
| advisory grid follow 0.5 after 30m seed 12 | 7.8% | 39.8% | 0.20 | -0.03 | +0.08 | -0.01 |
| advisory grid follow 0.5 after 90m seed 2 | 8.0% | 40.0% | 0.20 | -0.02 | +0.06 | -0.01 |
| advisory grid follow 0.5 after 30m seed 17 | 7.6% | 37.5% | 0.20 | -0.02 | +0.04 | -0.01 |
| advisory grid follow 0.5 after 30m seed 16 | 7.8% | 38.5% | 0.20 | -0.02 | +0.08 | -0.01 |
| advisory grid follow 0.5 after 30m seed 18 | 7.9% | 37.9% | 0.21 | -0.01 | +0.08 | -0.00 |
| advisory grid follow 0.5 after 90m seed 4 | 8.1% | 39.3% | 0.21 | -0.02 | +0.06 | -0.00 |
| advisory grid follow 0.5 after 90m seed 5 | 7.8% | 34.6% | 0.22 | +0.00 | +0.00 | +0.00 |
| advisory grid follow 0.5 after 90m seed 0 | 8.0% | 37.0% | 0.22 | -0.00 | +0.03 | +0.01 |
| advisory grid follow 0.5 after 90m seed 3 | 8.0% | 40.4% | 0.20 | -0.02 | +0.03 | -0.00 |
| advisory grid follow 0.5 after 90m seed 1 | 7.7% | 40.3% | 0.19 | -0.03 | +0.07 | -0.02 |
| advisory grid follow 0.5 after 30m seed 13 | 7.7% | 35.5% | 0.22 | -0.00 | +0.06 | -0.00 |
| advisory grid follow 0.5 after 90m seed 6 | 8.2% | 39.9% | 0.21 | -0.02 | +0.06 | +0.00 |
| advisory grid follow 0.5 after 90m seed 7 | 7.8% | 39.9% | 0.20 | -0.02 | +0.09 | -0.01 |
| advisory grid follow 0.5 after 90m seed 9 | 7.9% | 35.5% | 0.22 | +0.00 | -0.02 | +0.01 |
| advisory grid follow 0.5 after 90m seed 10 | 7.9% | 35.8% | 0.22 | -0.00 | -0.05 | +0.01 |
| advisory grid follow 0.8 after 0m seed 1 | 7.7% | 36.9% | 0.21 | -0.01 | +0.03 | +0.00 |
| advisory grid follow 0.5 after 90m seed 8 | 8.2% | 40.7% | 0.20 | -0.02 | +0.03 | -0.00 |
| advisory grid follow 0.5 after 90m seed 14 | 8.1% | 35.4% | 0.23 | +0.01 | +0.16 | +0.02 |
| advisory grid follow 0.8 after 0m seed 3 | 7.4% | 37.2% | 0.20 | -0.02 | +0.09 | -0.01 |
| advisory grid follow 0.5 after 90m seed 15 | 8.2% | 37.0% | 0.22 | +0.00 | +0.09 | +0.01 |
| advisory grid follow 0.8 after 0m seed 2 | 7.7% | 37.8% | 0.20 | -0.02 | +0.10 | +0.00 |
| advisory grid follow 0.5 after 90m seed 12 | 7.8% | 39.9% | 0.20 | -0.03 | +0.08 | -0.01 |
| advisory grid follow 0.8 after 0m seed 7 | 7.4% | 36.1% | 0.20 | -0.02 | +0.17 | -0.01 |
| advisory grid follow 0.5 after 90m seed 11 | 8.0% | 41.6% | 0.19 | -0.03 | +0.08 | -0.01 |

*The first 60 of 181 runs; every run is in results.jsonl, and the lines below count them all.*

| follows | after | seeds | d return | d max DD | d Calmar | seeds better |
|---|---|---|---|---|---|---|
| 50% | 0 min | 20 | -0.58 pts | -0.18 pts | -0.014 | 3 of 20 |
| 50% | 30 min | 20 | -0.57 pts | -0.19 pts | -0.013 | 3 of 20 |
| 50% | 90 min | 20 | -0.54 pts | -0.18 pts | -0.013 | 4 of 20 |
| 80% | 0 min | 20 | -0.96 pts | -1.02 pts | -0.019 | 0 of 20 |
| 80% | 30 min | 20 | -0.94 pts | -1.05 pts | -0.019 | 0 of 20 |
| 80% | 90 min | 20 | -0.90 pts | -1.03 pts | -0.018 | 0 of 20 |
| 100% | 0 min | 20 | -1.24 pts | -1.41 pts | -0.025 | 0 of 20 |
| 100% | 30 min | 20 | -1.21 pts | -1.45 pts | -0.024 | 0 of 20 |
| 100% | 90 min | 20 | -1.16 pts | -1.43 pts | -0.023 | 0 of 20 |

### accuracy

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| accuracy grid tiers mixture 0.1 seed 6 | 6.3% | 34.1% | 0.18 | -0.04 | +0.21 | -0.01 |
| accuracy grid tiers mixture 0.1 seed 5 | 6.2% | 28.6% | 0.21 | -0.01 | -0.03 | -0.00 |
| accuracy grid tiers mixture 0.1 seed 17 | 6.6% | 25.2% | 0.26 | +0.04 | +0.01 | +0.05 |
| accuracy grid tiers mixture 0.0 seed 5 | 6.2% | 30.8% | 0.20 | -0.02 | -0.03 | -0.01 |
| accuracy grid tiers mixture 0.1 seed 12 | 6.7% | 31.8% | 0.21 | -0.01 | +0.24 | +0.01 |
| accuracy grid tiers mixture 0.0 seed 19 | 6.5% | 32.6% | 0.20 | -0.02 | -0.04 | +0.00 |
| accuracy grid tiers mixture 0.0 seed 8 | 6.3% | 36.5% | 0.17 | -0.05 | +0.05 | -0.02 |
| accuracy grid tiers mixture 0.1 seed 16 | 6.4% | 29.2% | 0.22 | -0.00 | +0.11 | +0.01 |
| accuracy grid tiers mixture 0.1 seed 15 | 6.4% | 35.2% | 0.18 | -0.04 | +0.01 | -0.01 |
| accuracy grid tiers mixture 0.1 seed 18 | 6.4% | 36.0% | 0.18 | -0.04 | +0.15 | -0.01 |
| accuracy grid none | 8.5% | 38.4% | 0.22 | +0.00 | +0.00 | +0.00 |
| accuracy grid tiers mixture 0.1 seed 1 | 6.7% | 34.8% | 0.19 | -0.03 | -0.09 | +0.01 |
| accuracy grid tiers mixture 0.1 seed 8 | 6.3% | 35.7% | 0.18 | -0.04 | -0.01 | -0.02 |
| accuracy grid tiers mixture 0.0 seed 14 | 6.2% | 24.5% | 0.25 | +0.03 | +0.15 | +0.02 |
| accuracy grid tiers mixture 0.1 seed 9 | 6.8% | 21.8% | 0.31 | +0.09 | -0.02 | +0.11 |
| accuracy grid tiers mixture 0.1 seed 7 | 6.2% | 40.7% | 0.15 | -0.07 | +0.00 | -0.04 |
| accuracy grid tiers mixture 0.0 seed 0 | 5.9% | 34.5% | 0.17 | -0.05 | +0.01 | -0.04 |
| accuracy grid tiers mixture 0.0 seed 17 | 6.6% | 27.6% | 0.24 | +0.02 | -0.03 | +0.04 |
| accuracy grid tiers mixture 0.0 seed 1 | 6.7% | 36.0% | 0.19 | -0.04 | -0.08 | -0.00 |
| accuracy grid tiers mixture 0.0 seed 16 | 6.4% | 30.3% | 0.21 | -0.01 | +0.11 | +0.01 |
| accuracy grid tiers mixture 0.1 seed 11 | 6.5% | 37.0% | 0.18 | -0.05 | +0.03 | -0.01 |
| accuracy grid tiers mixture 0.0 seed 7 | 6.1% | 40.4% | 0.15 | -0.07 | -0.02 | -0.04 |
| accuracy grid tiers mixture 0.1 seed 0 | 6.3% | 34.8% | 0.18 | -0.04 | +0.09 | -0.02 |
| accuracy grid tiers mixture 0.0 seed 15 | 6.5% | 36.7% | 0.18 | -0.04 | +0.00 | -0.01 |
| accuracy grid tiers mixture 0.0 seed 13 | 6.3% | 40.3% | 0.16 | -0.06 | -0.02 | -0.03 |
| accuracy grid tiers mixture 0.0 seed 12 | 6.7% | 22.3% | 0.30 | +0.08 | +0.27 | +0.07 |
| accuracy grid tiers mixture 0.0 seed 6 | 6.4% | 35.1% | 0.18 | -0.04 | +0.17 | -0.01 |
| accuracy grid tiers mixture 0.1 seed 14 | 6.7% | 23.0% | 0.29 | +0.07 | +0.27 | +0.07 |
| accuracy grid tiers mixture 0.1 seed 13 | 6.4% | 38.2% | 0.17 | -0.05 | +0.04 | -0.03 |
| accuracy grid tiers mixture 0.0 seed 10 | 6.7% | 30.8% | 0.22 | -0.00 | -0.05 | +0.02 |
| accuracy grid tiers mixture 0.0 seed 11 | 6.5% | 39.7% | 0.16 | -0.06 | -0.04 | -0.02 |
| accuracy grid tiers mixture 0.1 seed 2 | 6.4% | 38.1% | 0.17 | -0.05 | +0.08 | -0.02 |
| accuracy grid tiers mixture 0.0 seed 18 | 6.4% | 35.1% | 0.18 | -0.04 | +0.09 | -0.01 |
| accuracy grid tiers mixture 0.0 seed 9 | 6.7% | 22.5% | 0.30 | +0.08 | -0.06 | +0.09 |
| accuracy grid tiers mixture 0.1 seed 4 | 6.7% | 31.7% | 0.21 | -0.01 | +0.05 | +0.02 |
| accuracy grid tiers mixture 0.0 seed 4 | 6.1% | 37.2% | 0.16 | -0.06 | -0.02 | -0.03 |
| accuracy grid tiers mixture 0.0 seed 3 | 6.6% | 43.7% | 0.15 | -0.07 | -0.03 | -0.02 |
| accuracy grid tiers mixture 0.1 seed 10 | 6.7% | 30.1% | 0.22 | +0.00 | -0.01 | +0.03 |
| accuracy grid tiers mixture 0.1 seed 3 | 6.5% | 44.0% | 0.15 | -0.07 | +0.07 | -0.03 |
| accuracy grid tiers mixture 0.0 seed 2 | 6.5% | 34.7% | 0.19 | -0.03 | +0.07 | -0.00 |
| accuracy grid tiers mixture 0.2 seed 10 | 6.6% | 26.2% | 0.25 | +0.03 | +0.02 | +0.04 |
| accuracy grid tiers mixture 0.1 seed 19 | 6.3% | 31.8% | 0.20 | -0.02 | +0.02 | -0.00 |
| accuracy grid tiers mixture 0.2 seed 6 | 6.5% | 33.3% | 0.19 | -0.03 | +0.14 | +0.00 |
| accuracy grid tiers mixture 0.2 seed 1 | 6.7% | 35.1% | 0.19 | -0.03 | +0.02 | +0.00 |
| accuracy grid tiers mixture 0.2 seed 3 | 6.6% | 43.5% | 0.15 | -0.07 | +0.06 | -0.02 |
| accuracy grid tiers mixture 0.2 seed 15 | 6.3% | 25.7% | 0.25 | +0.02 | +0.03 | +0.03 |
| accuracy grid tiers mixture 0.2 seed 13 | 6.4% | 34.2% | 0.19 | -0.03 | +0.03 | -0.01 |
| accuracy grid tiers mixture 0.2 seed 9 | 6.9% | 21.5% | 0.32 | +0.10 | +0.04 | +0.11 |
| accuracy grid tiers mixture 0.2 seed 7 | 6.1% | 35.0% | 0.17 | -0.05 | +0.08 | -0.03 |
| accuracy grid tiers mixture 0.2 seed 18 | 6.5% | 36.4% | 0.18 | -0.04 | +0.16 | -0.00 |
| accuracy grid tiers mixture 0.2 seed 16 | 6.5% | 26.1% | 0.25 | +0.03 | +0.11 | +0.04 |
| accuracy grid tiers mixture 0.3 seed 1 | 6.8% | 35.3% | 0.19 | -0.03 | +0.04 | +0.01 |
| accuracy grid tiers mixture 0.3 seed 2 | 6.8% | 30.9% | 0.22 | -0.00 | +0.07 | +0.04 |
| accuracy grid tiers mixture 0.2 seed 19 | 6.2% | 27.0% | 0.23 | +0.01 | +0.03 | +0.01 |
| accuracy grid tiers mixture 0.3 seed 5 | 6.3% | 30.3% | 0.21 | -0.01 | +0.01 | -0.00 |
| accuracy grid tiers mixture 0.3 seed 0 | 6.2% | 32.6% | 0.19 | -0.03 | +0.13 | -0.01 |
| accuracy grid tiers mixture 0.2 seed 11 | 6.5% | 33.3% | 0.20 | -0.03 | +0.07 | +0.01 |
| accuracy grid tiers mixture 0.3 seed 10 | 6.6% | 25.8% | 0.25 | +0.03 | +0.05 | +0.05 |
| accuracy grid tiers mixture 0.2 seed 0 | 6.2% | 34.5% | 0.18 | -0.04 | +0.13 | -0.02 |
| accuracy grid tiers mixture 0.2 seed 2 | 6.9% | 37.7% | 0.18 | -0.04 | +0.07 | +0.01 |

*The first 60 of 2041 runs; every run is in results.jsonl, and the lines below count them all.*

| lever | family | accuracy | median d Calmar | p10 | p90 |
|---|---|---|---|---|---|
| None | None | None | +0.000 | +0.000 | +0.000 |
| all | mixture | 0.0 | -0.042 | -0.067 | +0.070 |
| all | mixture | 0.1 | -0.037 | -0.059 | +0.057 |
| all | mixture | 0.2 | -0.018 | -0.051 | +0.050 |
| all | mixture | 0.3 | -0.013 | -0.040 | +0.058 |
| all | mixture | 0.5 | +0.022 | -0.010 | +0.104 |
| all | mixture | 0.7 | +0.073 | +0.028 | +0.182 |
| all | mixture | 0.9 | +0.127 | +0.062 | +0.164 |
| all | mixture | 1.0 | +0.139 | +0.139 | +0.139 |
| all | noisy | 0.0 | -0.063 | -0.083 | -0.010 |
| all | noisy | 0.1 | -0.046 | -0.073 | +0.019 |
| all | noisy | 0.2 | -0.033 | -0.066 | +0.044 |
| all | noisy | 0.3 | -0.012 | -0.047 | +0.123 |
| all | noisy | 0.5 | +0.035 | -0.006 | +0.235 |
| all | noisy | 0.7 | +0.107 | +0.011 | +0.295 |
| all | noisy | 0.9 | +0.141 | +0.103 | +0.214 |
| all | noisy | 1.0 | +0.139 | +0.139 | +0.139 |
| all | proxy+ | 0.0 | -0.047 | -0.047 | -0.047 |
| all | proxy+ | 0.1 | -0.048 | -0.048 | -0.048 |
| all | proxy+ | 0.2 | -0.041 | -0.041 | -0.041 |
| all | proxy+ | 0.3 | -0.013 | -0.013 | -0.013 |
| all | proxy+ | 0.5 | +0.028 | +0.028 | +0.028 |
| spacing | mixture | 0.0 | -0.026 | -0.030 | +0.002 |
| spacing | mixture | 0.1 | -0.027 | -0.030 | -0.020 |
| spacing | mixture | 0.2 | -0.026 | -0.030 | -0.020 |
| spacing | mixture | 0.3 | -0.027 | -0.029 | -0.022 |
| spacing | mixture | 0.5 | -0.027 | -0.030 | -0.022 |
| spacing | mixture | 0.7 | -0.028 | -0.030 | -0.024 |
| spacing | mixture | 0.9 | -0.028 | -0.028 | -0.026 |
| spacing | mixture | 1.0 | -0.028 | -0.028 | -0.028 |
| spacing | noisy | 0.0 | -0.025 | -0.029 | -0.006 |
| spacing | noisy | 0.1 | -0.026 | -0.029 | -0.007 |
| spacing | noisy | 0.2 | -0.025 | -0.029 | -0.007 |
| spacing | noisy | 0.3 | -0.024 | -0.029 | -0.007 |
| spacing | noisy | 0.5 | -0.024 | -0.028 | -0.021 |
| spacing | noisy | 0.7 | -0.025 | -0.028 | -0.020 |
| spacing | noisy | 0.9 | -0.026 | -0.029 | -0.023 |
| spacing | noisy | 1.0 | -0.028 | -0.028 | -0.028 |
| spacing | proxy+ | 0.0 | -0.026 | -0.026 | -0.026 |
| spacing | proxy+ | 0.1 | -0.026 | -0.026 | -0.026 |
| spacing | proxy+ | 0.2 | -0.026 | -0.026 | -0.026 |
| spacing | proxy+ | 0.3 | -0.025 | -0.025 | -0.025 |
| spacing | proxy+ | 0.5 | -0.025 | -0.025 | -0.025 |
| tiers | mixture | 0.0 | -0.036 | -0.064 | +0.076 |
| tiers | mixture | 0.1 | -0.032 | -0.053 | +0.071 |
| tiers | mixture | 0.2 | -0.011 | -0.043 | +0.064 |
| tiers | mixture | 0.3 | -0.006 | -0.034 | +0.069 |
| tiers | mixture | 0.5 | +0.033 | -0.002 | +0.113 |
| tiers | mixture | 0.7 | +0.088 | +0.041 | +0.197 |
| tiers | mixture | 0.9 | +0.142 | +0.075 | +0.183 |
| tiers | mixture | 1.0 | +0.156 | +0.156 | +0.156 |
| tiers | noisy | 0.0 | -0.056 | -0.079 | -0.023 |
| tiers | noisy | 0.1 | -0.038 | -0.070 | +0.013 |
| tiers | noisy | 0.2 | -0.023 | -0.059 | +0.050 |
| tiers | noisy | 0.3 | -0.001 | -0.039 | +0.111 |
| tiers | noisy | 0.5 | +0.045 | +0.004 | +0.245 |
| tiers | noisy | 0.7 | +0.122 | +0.024 | +0.307 |
| tiers | noisy | 0.9 | +0.160 | +0.118 | +0.236 |
| tiers | noisy | 1.0 | +0.156 | +0.156 | +0.156 |
| tiers | proxy+ | 0.0 | -0.040 | -0.040 | -0.040 |
| tiers | proxy+ | 0.1 | -0.042 | -0.042 | -0.042 |
| tiers | proxy+ | 0.2 | -0.035 | -0.035 | -0.035 |
| tiers | proxy+ | 0.3 | -0.007 | -0.007 | -0.007 |
| tiers | proxy+ | 0.5 | +0.037 | +0.037 | +0.037 |
| weekly | mixture | 0.0 | -0.016 | -0.016 | -0.015 |
| weekly | mixture | 0.1 | -0.016 | -0.016 | -0.015 |
| weekly | mixture | 0.2 | -0.016 | -0.016 | -0.015 |
| weekly | mixture | 0.3 | -0.016 | -0.016 | -0.015 |
| weekly | mixture | 0.5 | -0.016 | -0.016 | -0.015 |
| weekly | mixture | 0.7 | -0.015 | -0.016 | -0.015 |
| weekly | mixture | 0.9 | -0.015 | -0.015 | -0.015 |
| weekly | mixture | 1.0 | -0.015 | -0.015 | -0.015 |
| weekly | noisy | 0.0 | -0.016 | -0.016 | -0.015 |
| weekly | noisy | 0.1 | -0.016 | -0.016 | -0.015 |
| weekly | noisy | 0.2 | -0.016 | -0.016 | -0.015 |
| weekly | noisy | 0.3 | -0.016 | -0.016 | -0.015 |
| weekly | noisy | 0.5 | -0.016 | -0.016 | -0.015 |
| weekly | noisy | 0.7 | -0.016 | -0.016 | -0.015 |
| weekly | noisy | 0.9 | -0.015 | -0.016 | -0.015 |
| weekly | noisy | 1.0 | -0.015 | -0.015 | -0.015 |
| weekly | proxy+ | 0.0 | -0.015 | -0.015 | -0.015 |
| weekly | proxy+ | 0.1 | -0.015 | -0.015 | -0.015 |
| weekly | proxy+ | 0.2 | -0.015 | -0.015 | -0.015 |
| weekly | proxy+ | 0.3 | -0.015 | -0.015 | -0.015 |
| weekly | proxy+ | 0.5 | -0.015 | -0.015 | -0.015 |

all: rho* = 0.5, rho*90 = 0.7
spacing: rho* = None, rho*90 = None
tiers: rho* = 0.5, rho*90 = 0.5
weekly: rho* = None, rho*90 = None

| knob | rho 0.2 | rho 0.5 | rho 0.9 |
|---|---|---|---|
| none | -0.033 | +0.035 | +0.141 |
| persistence | -0.024 | +0.057 | +0.144 |
| shared | -0.039 | +0.024 | +0.127 |
| bias -0.5 | -0.029 | +0.001 | +0.088 |
| bias +0.5 | -0.050 | +0.034 | +0.134 |
| missing | -0.035 | +0.014 | +0.074 |
| catalyst_miss | -0.033 | +0.035 | +0.141 |

## ultimate

### tiers

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| tiers ultimate none | 27.5% | 16.5% | 1.67 | +0.00 | +0.00 | +0.00 |
| tiers ultimate pause random 13% | 26.8% | 15.2% | 1.77 | +0.10 | +0.15 | -0.23 |
| tiers ultimate x0.75 | 24.6% | 15.0% | 1.64 | -0.03 | -0.06 | -0.03 |
| tiers ultimate x0.5 | 21.1% | 14.4% | 1.47 | -0.20 | -0.40 | +0.01 |
| tiers ultimate x1.0 | 26.9% | 16.0% | 1.68 | +0.01 | +0.01 | -0.02 |
| tiers ultimate x0.25 | 15.7% | 16.3% | 0.96 | -0.71 | -1.36 | -0.06 |
| tiers ultimate ceiling50 | 22.5% | 17.1% | 1.32 | -0.35 | -1.00 | -0.02 |

### oracle

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| oracle ultimate none | 27.5% | 16.5% | 1.67 | +0.00 | +0.00 | +0.00 |
| oracle ultimate worst 20% pause | 24.8% | 16.8% | 1.48 | -0.19 | -0.33 | -0.25 |
| oracle ultimate worst 10% pause | 27.0% | 16.5% | 1.63 | -0.03 | -0.09 | -0.16 |
| oracle ultimate worst 5% x0.5 | 26.5% | 16.5% | 1.61 | -0.06 | -0.06 | -0.20 |
| oracle ultimate worst 5% pause | 27.4% | 16.5% | 1.66 | -0.00 | -0.00 | -0.01 |
| oracle ultimate worst 10% x0.5 | 25.6% | 16.5% | 1.55 | -0.11 | -0.14 | -0.23 |
| oracle ultimate worst 20% x0.5 | 24.0% | 16.6% | 1.45 | -0.21 | -0.30 | -0.12 |

### matrix

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| matrix ultimate none | 27.5% | 16.5% | 1.67 | +0.00 | +0.00 | +0.00 |
| matrix ultimate tier0 pause | 23.3% | 14.4% | 1.62 | -0.05 | -0.21 | +0.21 |
| matrix ultimate tier1 x0.75 | 26.7% | 16.3% | 1.63 | -0.03 | -0.07 | -0.03 |
| matrix ultimate tier1 x0.5 | 26.0% | 16.1% | 1.61 | -0.05 | -0.14 | -0.04 |
| matrix ultimate tier0 x0.5 | 25.3% | 15.1% | 1.67 | +0.00 | +0.08 | +0.02 |
| matrix ultimate tier0 x0.75 | 26.5% | 15.9% | 1.67 | -0.00 | +0.03 | +0.02 |
| matrix ultimate tier0 x0.25 | 23.6% | 13.6% | 1.73 | +0.07 | +0.18 | +0.03 |
| matrix ultimate tier1 x0.25 | 25.3% | 16.0% | 1.58 | -0.08 | -0.21 | -0.05 |
| matrix ultimate tier1 pause | 26.1% | 15.8% | 1.65 | -0.02 | -0.15 | -0.07 |
| matrix ultimate tier2 pause | 27.0% | 15.4% | 1.75 | +0.09 | +0.15 | -0.02 |
| matrix ultimate tier2 x0.75 | 26.8% | 15.9% | 1.68 | +0.02 | +0.04 | -0.04 |
| matrix ultimate tier3 x0.75 | 27.2% | 16.5% | 1.65 | -0.02 | -0.07 | +0.02 |
| matrix ultimate tier2 x0.5 | 26.5% | 15.8% | 1.68 | +0.01 | +0.04 | -0.06 |
| matrix ultimate tier2 x0.25 | 26.3% | 15.6% | 1.68 | +0.01 | +0.05 | -0.09 |
| matrix ultimate tier3 x0.5 | 27.1% | 16.5% | 1.64 | -0.03 | -0.11 | +0.03 |
| matrix ultimate tier3 x0.25 | 26.9% | 16.5% | 1.63 | -0.03 | -0.14 | +0.04 |
| matrix ultimate tier3 pause | 27.0% | 16.5% | 1.64 | -0.03 | -0.13 | +0.04 |

### proxy

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| proxy ultimate none | 27.5% | 16.5% | 1.67 | +0.00 | +0.00 | +0.00 |
| proxy ultimate continuous | 25.4% | 15.6% | 1.63 | -0.03 | -0.11 | -0.04 |
| proxy ultimate binary | 26.5% | 16.0% | 1.66 | -0.01 | -0.08 | +0.01 |
| proxy ultimate ceiling | 26.5% | 15.8% | 1.68 | +0.01 | -0.04 | -0.01 |
| proxy ultimate graded | 25.1% | 15.4% | 1.63 | -0.04 | -0.16 | -0.05 |

### spacing

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| spacing ultimate none | 27.5% | 16.5% | 1.67 | +0.00 | +0.00 | +0.00 |
| spacing ultimate B e1.0 max4.0 follow=False | 26.7% | 16.0% | 1.67 | +0.00 | -0.00 | -0.05 |
| spacing ultimate B e1.0 max2.0 follow=False | 26.7% | 16.0% | 1.67 | +0.00 | -0.00 | -0.05 |
| spacing ultimate B e0.5 max2.0 follow=False | 26.8% | 16.0% | 1.68 | +0.01 | +0.01 | -0.04 |
| spacing ultimate B e1.0 max4.0 follow=True | 26.5% | 16.0% | 1.66 | -0.01 | -0.09 | +0.01 |
| spacing ultimate B e0.5 max4.0 follow=False | 26.8% | 16.0% | 1.68 | +0.01 | +0.01 | -0.04 |
| spacing ultimate B e0.5 max2.0 follow=True | 26.8% | 16.0% | 1.68 | +0.01 | -0.01 | -0.02 |
| spacing ultimate B e1.0 max2.0 follow=True | 26.5% | 16.0% | 1.66 | -0.01 | -0.09 | +0.01 |
| spacing ultimate B e0.5 max4.0 follow=True | 26.8% | 16.0% | 1.68 | +0.01 | -0.01 | -0.02 |
| spacing ultimate B + tiers | 25.0% | 15.4% | 1.62 | -0.04 | -0.17 | -0.08 |

### weekly

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| weekly ultimate none | 27.5% | 16.5% | 1.67 | +0.00 | +0.00 | +0.00 |
| weekly ultimate G max slope 1.0 | 26.5% | 15.9% | 1.66 | -0.00 | -0.06 | -0.01 |
| weekly ultimate G next_month slope 0.5 | 26.8% | 16.0% | 1.67 | +0.01 | -0.01 | -0.02 |
| weekly ultimate G next_month slope 1.0 | 26.5% | 16.0% | 1.66 | -0.01 | -0.08 | -0.01 |
| weekly ultimate G next_month slope 0.25 | 26.9% | 16.0% | 1.68 | +0.02 | +0.02 | -0.02 |
| weekly ultimate G next_quarter slope 0.5 | 26.8% | 16.0% | 1.68 | +0.02 | +0.01 | -0.02 |
| weekly ultimate G next_quarter slope 0.25 | 26.9% | 16.0% | 1.68 | +0.02 | +0.01 | -0.02 |
| weekly ultimate G max slope 0.5 | 26.8% | 16.0% | 1.68 | +0.01 | +0.00 | -0.02 |
| weekly ultimate G max slope 0.25 | 26.9% | 16.0% | 1.68 | +0.02 | +0.02 | -0.02 |
| weekly ultimate G next_quarter slope 1.0 | 26.8% | 15.9% | 1.68 | +0.02 | +0.00 | -0.02 |
| weekly ultimate G every five sessions | 26.8% | 16.0% | 1.67 | +0.01 | -0.01 | -0.02 |
| weekly ultimate all levers | 25.0% | 15.4% | 1.62 | -0.05 | -0.17 | -0.08 |

### null

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| null ultimate none | 27.5% | 16.5% | 1.67 | +0.00 | +0.00 | +0.00 |
| null ultimate tiers shift 00 | 24.0% | 13.8% | 1.74 | +0.07 | +0.13 | -0.39 |
| null ultimate tiers shift 01 | 23.5% | 15.2% | 1.54 | -0.13 | -0.37 | -0.12 |
| null ultimate tiers shift 03 | 23.7% | 14.2% | 1.66 | -0.00 | +0.04 | -0.45 |
| null ultimate tiers shift 04 | 24.5% | 15.5% | 1.58 | -0.08 | -0.01 | -0.18 |
| null ultimate tiers shift 05 | 24.1% | 15.2% | 1.58 | -0.08 | -0.13 | -0.39 |
| null ultimate tiers shift 06 | 24.4% | 15.6% | 1.57 | -0.10 | -0.40 | +0.36 |
| null ultimate tiers shift 08 | 23.3% | 14.6% | 1.59 | -0.07 | -0.24 | -0.23 |
| null ultimate tiers shift 10 | 24.5% | 15.2% | 1.61 | -0.05 | -0.11 | -0.20 |
| null ultimate tiers shift 09 | 23.6% | 14.0% | 1.68 | +0.02 | -0.06 | -0.21 |
| null ultimate tiers shift 02 | 22.2% | 16.2% | 1.37 | -0.30 | -0.63 | +0.05 |
| null ultimate tiers shift 12 | 24.1% | 15.9% | 1.52 | -0.14 | -0.25 | +0.20 |
| null ultimate tiers shift 13 | 24.2% | 16.1% | 1.51 | -0.16 | -0.30 | +0.32 |
| null ultimate tiers shift 11 | 24.4% | 15.4% | 1.58 | -0.08 | -0.14 | -0.08 |
| null ultimate tiers shift 15 | 24.3% | 16.2% | 1.50 | -0.17 | -0.33 | -0.12 |
| null ultimate tiers shift 14 | 24.7% | 14.6% | 1.69 | +0.02 | -0.14 | +0.30 |
| null ultimate tiers shift 16 | 24.3% | 14.3% | 1.70 | +0.03 | +0.04 | -0.21 |
| null ultimate tiers real | 25.1% | 15.4% | 1.63 | -0.04 | -0.16 | -0.05 |
| null ultimate tiers shift 17 | 23.3% | 14.5% | 1.61 | -0.05 | -0.43 | +0.27 |
| null ultimate tiers shift 18 | 22.1% | 16.4% | 1.35 | -0.31 | -0.37 | -0.80 |
| null ultimate tiers shift 07 | 23.5% | 16.4% | 1.44 | -0.23 | -0.42 | -0.15 |
| null ultimate tiers shift 19 | 23.2% | 16.2% | 1.44 | -0.23 | -0.43 | -0.34 |
| null ultimate tiers shift 20 | 22.1% | 16.4% | 1.35 | -0.31 | -0.37 | -0.80 |
| null ultimate tiers shift 22 | 24.7% | 15.4% | 1.61 | -0.06 | -0.20 | -0.20 |
| null ultimate tiers shift 21 | 22.7% | 14.9% | 1.53 | -0.14 | -0.20 | -0.57 |
| null ultimate tiers shift 23 | 24.3% | 16.5% | 1.47 | -0.19 | -0.38 | +0.16 |
| null ultimate tiers shift 25 | 25.1% | 15.9% | 1.58 | -0.09 | -0.32 | +0.41 |
| null ultimate tiers shift 24 | 24.9% | 15.7% | 1.58 | -0.08 | -0.27 | +0.02 |
| null ultimate tiers shift 27 | 23.7% | 15.1% | 1.56 | -0.10 | -0.27 | +0.53 |
| null ultimate tiers shift 26 | 23.9% | 15.6% | 1.53 | -0.14 | -0.41 | -0.08 |
| null ultimate tiers shift 28 | 24.5% | 15.0% | 1.64 | -0.03 | -0.21 | +0.31 |
| null ultimate tiers shift 29 | 25.1% | 15.9% | 1.58 | -0.09 | -0.32 | +0.41 |
| null ultimate tiers shift 30 | 25.2% | 13.4% | 1.89 | +0.22 | +0.46 | +0.16 |
| null ultimate tiers shift 32 | 25.0% | 15.0% | 1.67 | +0.00 | +0.05 | +0.14 |
| null ultimate tiers shift 34 | 25.1% | 16.5% | 1.53 | -0.14 | -0.30 | +0.19 |
| null ultimate tiers shift 35 | 23.3% | 14.3% | 1.63 | -0.03 | +0.12 | -0.39 |
| null ultimate tiers shift 36 | 23.8% | 16.4% | 1.45 | -0.21 | -0.50 | +0.10 |
| null ultimate tiers shift 38 | 24.0% | 15.1% | 1.58 | -0.08 | -0.27 | -0.12 |
| null ultimate tiers shift 39 | 24.7% | 14.6% | 1.69 | +0.02 | -0.14 | +0.30 |
| null ultimate spacing shift 00 | 26.5% | 14.8% | 1.80 | +0.13 | +0.24 | -0.11 |
| null ultimate spacing real | 26.7% | 16.0% | 1.67 | +0.00 | -0.00 | -0.05 |
| null ultimate spacing shift 01 | 26.2% | 15.6% | 1.68 | +0.02 | -0.04 | -0.03 |
| null ultimate spacing shift 02 | 26.2% | 15.4% | 1.70 | +0.04 | +0.02 | -0.08 |
| null ultimate spacing shift 03 | 26.4% | 15.5% | 1.71 | +0.04 | +0.08 | -0.13 |
| null ultimate spacing shift 04 | 26.4% | 15.6% | 1.69 | +0.02 | +0.09 | -0.12 |
| null ultimate spacing shift 05 | 26.3% | 15.5% | 1.69 | +0.02 | +0.04 | -0.13 |
| null ultimate tiers shift 37 | 22.6% | 15.2% | 1.49 | -0.17 | -0.29 | -0.55 |
| null ultimate tiers shift 33 | 23.5% | 15.8% | 1.48 | -0.18 | -0.29 | -0.25 |
| null ultimate tiers shift 31 | 23.6% | 14.2% | 1.66 | -0.01 | -0.33 | +0.30 |
| null ultimate spacing shift 07 | 26.4% | 16.1% | 1.64 | -0.03 | -0.08 | -0.05 |
| null ultimate spacing shift 08 | 26.6% | 14.3% | 1.86 | +0.19 | +0.32 | -0.08 |
| null ultimate spacing shift 10 | 26.5% | 16.2% | 1.64 | -0.03 | -0.04 | -0.11 |
| null ultimate spacing shift 12 | 26.6% | 15.9% | 1.68 | +0.01 | +0.02 | +0.03 |
| null ultimate spacing shift 11 | 26.6% | 15.9% | 1.67 | +0.00 | -0.01 | -0.05 |
| null ultimate spacing shift 13 | 26.8% | 15.9% | 1.69 | +0.02 | +0.02 | +0.01 |
| null ultimate spacing shift 14 | 26.7% | 16.0% | 1.67 | +0.00 | -0.06 | +0.07 |
| null ultimate spacing shift 15 | 26.8% | 15.9% | 1.69 | +0.02 | +0.06 | -0.06 |
| null ultimate spacing shift 16 | 26.5% | 15.3% | 1.73 | +0.07 | +0.15 | -0.16 |
| null ultimate spacing shift 17 | 26.3% | 14.7% | 1.79 | +0.12 | +0.14 | -0.04 |
| null ultimate spacing shift 19 | 26.6% | 16.0% | 1.66 | -0.00 | +0.03 | -0.15 |

*The first 60 of 124 runs; every run is in results.jsonl, and the lines below count them all.*

tiers: the real schedule beats 29 of 40 shifted copies on Calmar.

spacing: the real schedule beats 17 of 40 shifted copies on Calmar.

weekly: the real schedule beats 13 of 40 shifted copies on Calmar.

### robust

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| robust ultimate none | 27.5% | 16.5% | 1.67 | +0.00 | +0.00 | +0.00 |
| robust ultimate without volatility | 24.7% | 14.8% | 1.67 | +0.00 | -0.09 | -0.03 |
| robust ultimate thresholds -0.05 | 24.4% | 15.0% | 1.63 | -0.04 | -0.16 | -0.04 |
| robust ultimate without regime | 24.8% | 15.3% | 1.62 | -0.04 | -0.15 | -0.14 |
| robust ultimate without tail | 25.7% | 15.7% | 1.64 | -0.02 | -0.09 | -0.04 |
| robust ultimate without gap | 25.0% | 15.1% | 1.66 | -0.01 | -0.10 | -0.01 |
| robust ultimate thresholds +0.05 | 25.7% | 15.6% | 1.64 | -0.02 | -0.10 | -0.03 |
| robust ultimate reversals not exempt | 24.2% | 15.2% | 1.59 | -0.08 | -0.25 | -0.15 |
| robust ultimate without catalyst | 24.7% | 15.1% | 1.64 | -0.03 | -0.13 | -0.01 |

### stress

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| stress ultimate grind none | 26.6% | 16.5% | 1.61 | -0.06 | -0.00 | -0.32 |
| stress ultimate fast none | 25.9% | 16.5% | 1.57 | -0.10 | -0.36 | +0.08 |
| stress ultimate deeper none | 26.5% | 16.7% | 1.59 | -0.07 | +0.00 | -0.65 |
| stress ultimate none | 27.5% | 16.5% | 1.67 | +0.00 | +0.00 | +0.00 |
| stress ultimate twice none | 24.4% | 16.5% | 1.48 | -0.19 | +0.00 | -0.47 |
| stress ultimate twice tiers | 21.8% | 15.4% | 1.42 | -0.25 | -0.16 | -0.59 |
| stress ultimate deeper tiers | 24.1% | 17.5% | 1.38 | -0.29 | -0.16 | -0.62 |
| stress ultimate grind tiers | 24.2% | 15.4% | 1.57 | -0.09 | -0.16 | -0.34 |
| stress ultimate fast tiers | 24.0% | 15.4% | 1.56 | -0.11 | -0.42 | +0.00 |

twice: the tiers move max DD by -1.1 points.

deeper: the tiers move max DD by +0.9 points.

grind: the tiers move max DD by -1.1 points.

fast: the tiers move max DD by -1.1 points.

### perturb

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| perturb ultimate none | 27.5% | 16.5% | 1.67 | +0.00 | +0.00 | +0.00 |
| perturb ultimate always3 | 5.2% | 25.4% | 0.20 | -1.46 | -2.63 | -0.96 |
| perturb ultimate inverted | 18.3% | 16.1% | 1.14 | -0.53 | -1.02 | +0.26 |
| perturb ultimate random 50% | 24.3% | 15.0% | 1.61 | -0.05 | -0.17 | +0.01 |
| perturb ultimate always0 | 26.9% | 16.0% | 1.68 | +0.01 | +0.01 | -0.02 |
| perturb ultimate random 10% | 25.0% | 15.1% | 1.65 | -0.01 | -0.12 | -0.05 |
| perturb ultimate random 25% | 24.7% | 14.9% | 1.66 | -0.00 | -0.08 | -0.09 |

### catalysts

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| catalysts ultimate none | 27.5% | 16.5% | 1.67 | +0.00 | +0.00 | +0.00 |
| catalysts ultimate blackout 30m | 26.9% | 15.9% | 1.69 | +0.03 | +0.03 | -0.02 |
| catalysts ultimate blackout 15m | 26.9% | 15.9% | 1.68 | +0.02 | +0.02 | -0.02 |
| catalysts ultimate blackout 10m | 26.9% | 16.0% | 1.68 | +0.02 | +0.01 | -0.02 |

### priority

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| priority ultimate none | 27.5% | 16.5% | 1.67 | +0.00 | +0.00 | +0.00 |
| priority ultimate supersedes neither | 25.2% | 15.6% | 1.61 | -0.05 | -0.21 | -0.01 |
| priority ultimate supersedes both | 25.1% | 15.4% | 1.63 | -0.04 | -0.16 | -0.05 |
| priority ultimate supersedes governor | 25.2% | 15.6% | 1.61 | -0.05 | -0.21 | -0.01 |

### advisory

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| advisory ultimate none | 27.5% | 16.5% | 1.67 | +0.00 | +0.00 | +0.00 |
| advisory ultimate follow 0.5 after 0m seed 0 | 27.3% | 16.5% | 1.65 | -0.01 | -0.05 | +0.02 |
| advisory ultimate follow 0.5 after 0m seed 1 | 27.2% | 16.5% | 1.65 | -0.02 | -0.09 | +0.03 |
| advisory ultimate follow 0.5 after 0m seed 2 | 27.3% | 16.5% | 1.66 | -0.01 | -0.03 | +0.00 |
| advisory ultimate follow 0.5 after 0m seed 3 | 27.0% | 16.5% | 1.63 | -0.03 | -0.12 | +0.02 |
| advisory ultimate follow 0.5 after 0m seed 4 | 27.2% | 16.5% | 1.65 | -0.02 | -0.08 | +0.03 |
| advisory ultimate follow 0.5 after 0m seed 6 | 27.1% | 16.5% | 1.64 | -0.02 | -0.09 | +0.03 |
| advisory ultimate follow 0.5 after 0m seed 5 | 27.2% | 16.5% | 1.65 | -0.02 | -0.08 | +0.02 |
| advisory ultimate follow 0.5 after 0m seed 7 | 27.5% | 16.5% | 1.67 | +0.00 | -0.02 | +0.03 |
| advisory ultimate follow 0.5 after 0m seed 9 | 27.1% | 16.5% | 1.64 | -0.02 | -0.09 | +0.03 |
| advisory ultimate follow 0.5 after 0m seed 8 | 27.2% | 16.5% | 1.65 | -0.02 | -0.09 | +0.04 |
| advisory ultimate follow 0.5 after 0m seed 10 | 27.2% | 16.5% | 1.65 | -0.01 | -0.07 | +0.04 |
| advisory ultimate follow 0.5 after 0m seed 12 | 27.5% | 16.5% | 1.67 | -0.00 | -0.02 | +0.02 |
| advisory ultimate follow 0.5 after 0m seed 11 | 27.4% | 16.5% | 1.66 | -0.00 | -0.03 | +0.03 |
| advisory ultimate follow 0.5 after 0m seed 14 | 27.5% | 16.5% | 1.67 | +0.00 | -0.02 | +0.03 |
| advisory ultimate follow 0.5 after 0m seed 15 | 27.1% | 16.5% | 1.64 | -0.02 | -0.09 | +0.02 |
| advisory ultimate follow 0.5 after 0m seed 16 | 26.9% | 16.5% | 1.63 | -0.03 | -0.13 | +0.04 |
| advisory ultimate follow 0.5 after 0m seed 13 | 27.1% | 16.5% | 1.64 | -0.03 | -0.09 | +0.01 |
| advisory ultimate follow 0.5 after 0m seed 17 | 27.0% | 16.5% | 1.64 | -0.03 | -0.11 | +0.03 |
| advisory ultimate follow 0.5 after 0m seed 19 | 27.1% | 16.5% | 1.64 | -0.02 | -0.09 | +0.02 |
| advisory ultimate follow 0.5 after 0m seed 18 | 27.4% | 16.5% | 1.66 | -0.01 | -0.03 | +0.02 |
| advisory ultimate follow 0.5 after 30m seed 0 | 27.3% | 16.5% | 1.65 | -0.01 | -0.05 | +0.02 |
| advisory ultimate follow 0.5 after 30m seed 5 | 27.2% | 16.5% | 1.65 | -0.02 | -0.07 | +0.02 |
| advisory ultimate follow 0.5 after 30m seed 2 | 27.3% | 16.5% | 1.66 | -0.01 | -0.03 | +0.00 |
| advisory ultimate follow 0.5 after 30m seed 3 | 27.0% | 16.5% | 1.63 | -0.03 | -0.12 | +0.02 |
| advisory ultimate follow 0.5 after 30m seed 1 | 27.2% | 16.5% | 1.65 | -0.02 | -0.08 | +0.03 |
| advisory ultimate follow 0.5 after 30m seed 4 | 27.2% | 16.5% | 1.65 | -0.02 | -0.08 | +0.03 |
| advisory ultimate follow 0.5 after 30m seed 7 | 27.5% | 16.5% | 1.67 | +0.00 | -0.02 | +0.03 |
| advisory ultimate follow 0.5 after 30m seed 8 | 27.2% | 16.5% | 1.65 | -0.02 | -0.09 | +0.04 |
| advisory ultimate follow 0.5 after 30m seed 6 | 27.1% | 16.5% | 1.64 | -0.02 | -0.09 | +0.02 |
| advisory ultimate follow 0.5 after 30m seed 9 | 27.1% | 16.5% | 1.64 | -0.02 | -0.09 | +0.03 |
| advisory ultimate follow 0.5 after 30m seed 11 | 27.4% | 16.5% | 1.66 | -0.00 | -0.03 | +0.03 |
| advisory ultimate follow 0.5 after 30m seed 12 | 27.5% | 16.5% | 1.67 | -0.00 | -0.02 | +0.02 |
| advisory ultimate follow 0.5 after 30m seed 13 | 27.1% | 16.5% | 1.64 | -0.02 | -0.09 | +0.01 |
| advisory ultimate follow 0.5 after 30m seed 10 | 27.2% | 16.5% | 1.65 | -0.01 | -0.07 | +0.04 |
| advisory ultimate follow 0.5 after 30m seed 14 | 27.5% | 16.5% | 1.67 | +0.00 | -0.02 | +0.03 |
| advisory ultimate follow 0.5 after 30m seed 15 | 27.1% | 16.5% | 1.64 | -0.02 | -0.09 | +0.02 |
| advisory ultimate follow 0.5 after 30m seed 16 | 27.0% | 16.5% | 1.63 | -0.03 | -0.12 | +0.03 |
| advisory ultimate follow 0.5 after 30m seed 18 | 27.4% | 16.5% | 1.66 | -0.01 | -0.03 | +0.02 |
| advisory ultimate follow 0.5 after 30m seed 17 | 27.0% | 16.5% | 1.64 | -0.03 | -0.10 | +0.03 |
| advisory ultimate follow 0.5 after 30m seed 19 | 27.1% | 16.5% | 1.65 | -0.02 | -0.08 | +0.02 |
| advisory ultimate follow 0.5 after 90m seed 1 | 27.2% | 16.5% | 1.65 | -0.02 | -0.08 | +0.03 |
| advisory ultimate follow 0.5 after 90m seed 2 | 27.3% | 16.5% | 1.66 | -0.01 | -0.04 | +0.00 |
| advisory ultimate follow 0.5 after 90m seed 4 | 27.2% | 16.5% | 1.65 | -0.02 | -0.08 | +0.03 |
| advisory ultimate follow 0.5 after 90m seed 3 | 26.9% | 16.5% | 1.63 | -0.03 | -0.12 | +0.03 |
| advisory ultimate follow 0.5 after 90m seed 0 | 27.2% | 16.5% | 1.65 | -0.02 | -0.07 | +0.02 |
| advisory ultimate follow 0.5 after 90m seed 5 | 27.2% | 16.5% | 1.65 | -0.02 | -0.07 | +0.02 |
| advisory ultimate follow 0.5 after 90m seed 6 | 27.1% | 16.5% | 1.64 | -0.02 | -0.09 | +0.02 |
| advisory ultimate follow 0.5 after 90m seed 7 | 27.5% | 16.5% | 1.67 | -0.00 | -0.02 | +0.03 |
| advisory ultimate follow 0.5 after 90m seed 9 | 27.1% | 16.5% | 1.64 | -0.02 | -0.10 | +0.03 |
| advisory ultimate follow 0.5 after 90m seed 10 | 27.2% | 16.5% | 1.65 | -0.02 | -0.08 | +0.04 |
| advisory ultimate follow 0.5 after 90m seed 11 | 27.4% | 16.5% | 1.66 | -0.00 | -0.03 | +0.03 |
| advisory ultimate follow 0.5 after 90m seed 8 | 27.2% | 16.5% | 1.65 | -0.02 | -0.08 | +0.04 |
| advisory ultimate follow 0.5 after 90m seed 13 | 27.1% | 16.5% | 1.64 | -0.02 | -0.09 | +0.01 |
| advisory ultimate follow 0.5 after 90m seed 12 | 27.5% | 16.5% | 1.66 | -0.00 | -0.02 | +0.02 |
| advisory ultimate follow 0.5 after 90m seed 14 | 27.5% | 16.5% | 1.66 | -0.00 | -0.03 | +0.03 |
| advisory ultimate follow 0.5 after 90m seed 16 | 27.0% | 16.5% | 1.63 | -0.03 | -0.12 | +0.03 |
| advisory ultimate follow 0.5 after 90m seed 15 | 27.1% | 16.5% | 1.64 | -0.03 | -0.10 | +0.02 |
| advisory ultimate follow 0.5 after 90m seed 17 | 27.0% | 16.5% | 1.64 | -0.03 | -0.10 | +0.03 |
| advisory ultimate follow 0.5 after 90m seed 18 | 27.3% | 16.5% | 1.66 | -0.01 | -0.04 | +0.02 |

*The first 60 of 181 runs; every run is in results.jsonl, and the lines below count them all.*

| follows | after | seeds | d return | d max DD | d Calmar | seeds better |
|---|---|---|---|---|---|---|
| 50% | 0 min | 20 | -0.27 pts | +0.00 pts | -0.016 | 2 of 20 |
| 50% | 30 min | 20 | -0.26 pts | +0.00 pts | -0.016 | 2 of 20 |
| 50% | 90 min | 20 | -0.28 pts | +0.00 pts | -0.017 | 0 of 20 |
| 80% | 0 min | 20 | -0.40 pts | +0.00 pts | -0.024 | 0 of 20 |
| 80% | 30 min | 20 | -0.39 pts | +0.00 pts | -0.024 | 0 of 20 |
| 80% | 90 min | 20 | -0.41 pts | +0.00 pts | -0.025 | 0 of 20 |
| 100% | 0 min | 20 | -0.51 pts | +0.00 pts | -0.031 | 0 of 20 |
| 100% | 30 min | 20 | -0.50 pts | +0.00 pts | -0.030 | 0 of 20 |
| 100% | 90 min | 20 | -0.51 pts | +0.00 pts | -0.031 | 0 of 20 |

### accuracy

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| accuracy ultimate none | 27.5% | 16.5% | 1.67 | +0.00 | +0.00 | +0.00 |
| accuracy ultimate tiers mixture 0.0 seed 0 | 25.0% | 14.5% | 1.73 | +0.07 | +0.13 | -0.07 |
| accuracy ultimate tiers mixture 0.0 seed 2 | 25.0% | 15.4% | 1.62 | -0.05 | -0.13 | -0.05 |
| accuracy ultimate tiers mixture 0.0 seed 4 | 24.9% | 15.7% | 1.59 | -0.08 | -0.15 | -0.02 |
| accuracy ultimate tiers mixture 0.0 seed 3 | 24.6% | 15.2% | 1.62 | -0.05 | -0.16 | +0.07 |
| accuracy ultimate tiers mixture 0.0 seed 7 | 24.0% | 15.4% | 1.55 | -0.11 | -0.17 | -0.21 |
| accuracy ultimate tiers mixture 0.0 seed 9 | 24.5% | 15.0% | 1.63 | -0.03 | -0.10 | +0.08 |
| accuracy ultimate tiers mixture 0.0 seed 16 | 25.0% | 14.0% | 1.78 | +0.12 | +0.18 | -0.02 |
| accuracy ultimate tiers mixture 0.0 seed 17 | 25.4% | 15.1% | 1.69 | +0.02 | -0.00 | +0.05 |
| accuracy ultimate tiers mixture 0.0 seed 8 | 24.3% | 14.1% | 1.72 | +0.06 | -0.00 | +0.02 |
| accuracy ultimate tiers mixture 0.0 seed 13 | 25.4% | 14.3% | 1.78 | +0.11 | +0.19 | +0.03 |
| accuracy ultimate tiers mixture 0.0 seed 5 | 25.1% | 15.6% | 1.61 | -0.05 | -0.13 | +0.03 |
| accuracy ultimate tiers mixture 0.0 seed 1 | 25.1% | 14.9% | 1.68 | +0.01 | -0.02 | +0.15 |
| accuracy ultimate tiers mixture 0.0 seed 19 | 25.4% | 14.8% | 1.71 | +0.05 | -0.01 | +0.30 |
| accuracy ultimate tiers mixture 0.0 seed 18 | 24.4% | 15.5% | 1.58 | -0.09 | -0.18 | -0.07 |
| accuracy ultimate tiers mixture 0.0 seed 10 | 25.0% | 15.6% | 1.60 | -0.06 | -0.08 | -0.04 |
| accuracy ultimate tiers mixture 0.0 seed 11 | 25.0% | 15.0% | 1.67 | +0.00 | -0.06 | +0.28 |
| accuracy ultimate tiers mixture 0.0 seed 12 | 25.0% | 14.9% | 1.67 | +0.00 | -0.01 | +0.06 |
| accuracy ultimate tiers mixture 0.1 seed 0 | 25.1% | 14.4% | 1.74 | +0.08 | +0.16 | -0.02 |
| accuracy ultimate tiers mixture 0.1 seed 1 | 25.0% | 14.8% | 1.69 | +0.02 | +0.03 | +0.14 |
| accuracy ultimate tiers mixture 0.1 seed 2 | 25.1% | 14.9% | 1.69 | +0.02 | -0.00 | +0.03 |
| accuracy ultimate tiers mixture 0.1 seed 3 | 24.6% | 15.2% | 1.62 | -0.05 | -0.12 | +0.06 |
| accuracy ultimate tiers mixture 0.1 seed 4 | 24.8% | 15.7% | 1.58 | -0.09 | -0.15 | -0.05 |
| accuracy ultimate tiers mixture 0.1 seed 5 | 25.0% | 15.6% | 1.60 | -0.06 | -0.13 | -0.05 |
| accuracy ultimate tiers mixture 0.0 seed 6 | 25.0% | 15.1% | 1.66 | -0.01 | +0.02 | -0.15 |
| accuracy ultimate tiers mixture 0.1 seed 9 | 24.6% | 14.7% | 1.67 | +0.00 | -0.04 | +0.13 |
| accuracy ultimate tiers mixture 0.1 seed 11 | 25.0% | 15.0% | 1.67 | +0.00 | -0.03 | +0.20 |
| accuracy ultimate tiers mixture 0.1 seed 10 | 24.9% | 15.6% | 1.60 | -0.06 | -0.06 | -0.14 |
| accuracy ultimate tiers mixture 0.1 seed 16 | 25.0% | 14.1% | 1.78 | +0.11 | +0.17 | +0.02 |
| accuracy ultimate tiers mixture 0.1 seed 15 | 25.2% | 14.7% | 1.71 | +0.05 | +0.04 | +0.02 |
| accuracy ultimate tiers mixture 0.1 seed 12 | 25.1% | 14.5% | 1.73 | +0.06 | +0.09 | +0.02 |
| accuracy ultimate tiers mixture 0.1 seed 18 | 24.7% | 15.4% | 1.61 | -0.06 | -0.15 | -0.02 |
| accuracy ultimate tiers mixture 0.1 seed 7 | 24.2% | 15.0% | 1.61 | -0.06 | -0.09 | -0.16 |
| accuracy ultimate tiers mixture 0.1 seed 14 | 24.3% | 14.7% | 1.65 | -0.02 | -0.05 | -0.07 |
| accuracy ultimate tiers mixture 0.0 seed 14 | 24.3% | 15.1% | 1.60 | -0.06 | -0.14 | -0.10 |
| accuracy ultimate tiers mixture 0.1 seed 19 | 25.4% | 14.4% | 1.76 | +0.09 | +0.10 | +0.25 |
| accuracy ultimate tiers mixture 0.1 seed 17 | 25.4% | 14.6% | 1.74 | +0.08 | +0.11 | -0.02 |
| accuracy ultimate tiers mixture 0.1 seed 8 | 24.3% | 14.2% | 1.71 | +0.04 | -0.01 | -0.03 |
| accuracy ultimate tiers mixture 0.2 seed 4 | 24.9% | 15.7% | 1.59 | -0.07 | -0.14 | -0.00 |
| accuracy ultimate tiers mixture 0.2 seed 2 | 25.2% | 14.9% | 1.70 | +0.03 | +0.02 | +0.10 |
| accuracy ultimate tiers mixture 0.2 seed 7 | 24.7% | 15.2% | 1.62 | -0.04 | -0.06 | -0.08 |
| accuracy ultimate tiers mixture 0.2 seed 0 | 25.1% | 14.4% | 1.74 | +0.08 | +0.15 | -0.05 |
| accuracy ultimate tiers mixture 0.2 seed 1 | 25.1% | 14.5% | 1.73 | +0.07 | +0.12 | +0.08 |
| accuracy ultimate tiers mixture 0.0 seed 15 | 24.8% | 15.3% | 1.61 | -0.05 | -0.15 | -0.02 |
| accuracy ultimate tiers mixture 0.1 seed 6 | 24.9% | 14.9% | 1.68 | +0.01 | +0.07 | -0.17 |
| accuracy ultimate tiers mixture 0.2 seed 9 | 24.9% | 14.7% | 1.69 | +0.03 | +0.03 | +0.07 |
| accuracy ultimate tiers mixture 0.2 seed 10 | 25.0% | 15.6% | 1.61 | -0.06 | -0.07 | -0.09 |
| accuracy ultimate tiers mixture 0.2 seed 5 | 25.2% | 15.5% | 1.62 | -0.04 | -0.10 | +0.08 |
| accuracy ultimate tiers mixture 0.1 seed 13 | 25.5% | 13.9% | 1.84 | +0.17 | +0.30 | +0.07 |
| accuracy ultimate tiers mixture 0.2 seed 15 | 25.1% | 15.0% | 1.68 | +0.01 | -0.01 | +0.04 |
| accuracy ultimate tiers mixture 0.2 seed 3 | 24.7% | 15.1% | 1.64 | -0.03 | -0.04 | -0.04 |
| accuracy ultimate tiers mixture 0.2 seed 18 | 24.8% | 15.4% | 1.61 | -0.05 | -0.12 | -0.02 |
| accuracy ultimate tiers mixture 0.2 seed 17 | 25.5% | 14.6% | 1.75 | +0.08 | +0.11 | +0.02 |
| accuracy ultimate tiers mixture 0.2 seed 8 | 24.7% | 14.0% | 1.76 | +0.10 | +0.12 | +0.02 |
| accuracy ultimate tiers mixture 0.2 seed 11 | 25.3% | 15.0% | 1.69 | +0.02 | +0.01 | +0.20 |
| accuracy ultimate tiers mixture 0.2 seed 19 | 25.4% | 14.4% | 1.77 | +0.10 | +0.14 | +0.18 |
| accuracy ultimate tiers mixture 0.3 seed 2 | 25.4% | 14.8% | 1.72 | +0.05 | +0.08 | +0.13 |
| accuracy ultimate tiers mixture 0.2 seed 14 | 24.1% | 14.7% | 1.64 | -0.03 | -0.05 | -0.15 |
| accuracy ultimate tiers mixture 0.2 seed 16 | 25.1% | 14.1% | 1.78 | +0.11 | +0.16 | +0.05 |
| accuracy ultimate tiers mixture 0.2 seed 13 | 25.4% | 13.8% | 1.85 | +0.18 | +0.35 | -0.02 |

*The first 60 of 2041 runs; every run is in results.jsonl, and the lines below count them all.*

| lever | family | accuracy | median d Calmar | p10 | p90 |
|---|---|---|---|---|---|
| None | None | None | +0.000 | +0.000 | +0.000 |
| all | mixture | 0.0 | -0.013 | -0.068 | +0.122 |
| all | mixture | 0.1 | +0.031 | -0.057 | +0.144 |
| all | mixture | 0.2 | +0.030 | -0.043 | +0.145 |
| all | mixture | 0.3 | +0.056 | -0.043 | +0.204 |
| all | mixture | 0.5 | +0.110 | +0.029 | +0.150 |
| all | mixture | 0.7 | +0.142 | +0.095 | +0.206 |
| all | mixture | 0.9 | +0.177 | +0.129 | +0.222 |
| all | mixture | 1.0 | +0.129 | +0.129 | +0.129 |
| all | noisy | 0.0 | -0.003 | -0.032 | +0.071 |
| all | noisy | 0.1 | +0.037 | -0.008 | +0.093 |
| all | noisy | 0.2 | +0.055 | +0.015 | +0.166 |
| all | noisy | 0.3 | +0.095 | +0.058 | +0.182 |
| all | noisy | 0.5 | +0.108 | +0.080 | +0.206 |
| all | noisy | 0.7 | +0.142 | +0.096 | +0.229 |
| all | noisy | 0.9 | +0.152 | +0.112 | +0.212 |
| all | noisy | 1.0 | +0.129 | +0.129 | +0.129 |
| all | proxy+ | 0.0 | -0.045 | -0.045 | -0.045 |
| all | proxy+ | 0.1 | -0.027 | -0.027 | -0.027 |
| all | proxy+ | 0.2 | -0.001 | -0.001 | -0.001 |
| all | proxy+ | 0.3 | +0.024 | +0.024 | +0.024 |
| all | proxy+ | 0.5 | +0.053 | +0.053 | +0.053 |
| spacing | mixture | 0.0 | +0.007 | -0.010 | +0.029 |
| spacing | mixture | 0.1 | +0.006 | -0.008 | +0.024 |
| spacing | mixture | 0.2 | +0.003 | -0.006 | +0.033 |
| spacing | mixture | 0.3 | +0.006 | -0.005 | +0.027 |
| spacing | mixture | 0.5 | +0.005 | -0.003 | +0.025 |
| spacing | mixture | 0.7 | +0.004 | -0.009 | +0.023 |
| spacing | mixture | 0.9 | +0.000 | -0.003 | +0.008 |
| spacing | mixture | 1.0 | +0.000 | +0.000 | +0.000 |
| spacing | noisy | 0.0 | +0.004 | -0.005 | +0.028 |
| spacing | noisy | 0.1 | +0.007 | -0.007 | +0.023 |
| spacing | noisy | 0.2 | +0.005 | -0.008 | +0.034 |
| spacing | noisy | 0.3 | +0.010 | -0.005 | +0.034 |
| spacing | noisy | 0.5 | +0.004 | -0.006 | +0.020 |
| spacing | noisy | 0.7 | +0.004 | -0.008 | +0.021 |
| spacing | noisy | 0.9 | +0.001 | -0.007 | +0.013 |
| spacing | noisy | 1.0 | +0.000 | +0.000 | +0.000 |
| spacing | proxy+ | 0.0 | +0.005 | +0.005 | +0.005 |
| spacing | proxy+ | 0.1 | +0.008 | +0.008 | +0.008 |
| spacing | proxy+ | 0.2 | +0.006 | +0.006 | +0.006 |
| spacing | proxy+ | 0.3 | +0.005 | +0.005 | +0.005 |
| spacing | proxy+ | 0.5 | +0.003 | +0.003 | +0.003 |
| tiers | mixture | 0.0 | -0.020 | -0.076 | +0.112 |
| tiers | mixture | 0.1 | +0.016 | -0.063 | +0.112 |
| tiers | mixture | 0.2 | +0.023 | -0.052 | +0.110 |
| tiers | mixture | 0.3 | +0.060 | -0.055 | +0.120 |
| tiers | mixture | 0.5 | +0.108 | +0.040 | +0.160 |
| tiers | mixture | 0.7 | +0.145 | +0.096 | +0.191 |
| tiers | mixture | 0.9 | +0.189 | +0.130 | +0.242 |
| tiers | mixture | 1.0 | +0.145 | +0.145 | +0.145 |
| tiers | noisy | 0.0 | -0.003 | -0.050 | +0.071 |
| tiers | noisy | 0.1 | +0.026 | -0.015 | +0.089 |
| tiers | noisy | 0.2 | +0.048 | +0.010 | +0.159 |
| tiers | noisy | 0.3 | +0.069 | +0.028 | +0.150 |
| tiers | noisy | 0.5 | +0.106 | +0.070 | +0.206 |
| tiers | noisy | 0.7 | +0.142 | +0.097 | +0.223 |
| tiers | noisy | 0.9 | +0.163 | +0.107 | +0.222 |
| tiers | noisy | 1.0 | +0.145 | +0.145 | +0.145 |
| tiers | proxy+ | 0.0 | -0.038 | -0.038 | -0.038 |
| tiers | proxy+ | 0.1 | -0.018 | -0.018 | -0.018 |
| tiers | proxy+ | 0.2 | +0.005 | +0.005 | +0.005 |
| tiers | proxy+ | 0.3 | +0.034 | +0.034 | +0.034 |
| tiers | proxy+ | 0.5 | +0.065 | +0.065 | +0.065 |
| weekly | mixture | 0.0 | +0.051 | +0.022 | +0.088 |
| weekly | mixture | 0.1 | +0.043 | +0.028 | +0.098 |
| weekly | mixture | 0.2 | +0.045 | +0.032 | +0.099 |
| weekly | mixture | 0.3 | +0.042 | +0.032 | +0.088 |
| weekly | mixture | 0.5 | +0.038 | +0.033 | +0.066 |
| weekly | mixture | 0.7 | +0.039 | +0.037 | +0.044 |
| weekly | mixture | 0.9 | +0.040 | +0.039 | +0.042 |
| weekly | mixture | 1.0 | +0.042 | +0.042 | +0.042 |
| weekly | noisy | 0.0 | +0.043 | +0.027 | +0.089 |
| weekly | noisy | 0.1 | +0.045 | +0.031 | +0.091 |
| weekly | noisy | 0.2 | +0.045 | +0.033 | +0.091 |
| weekly | noisy | 0.3 | +0.045 | +0.036 | +0.094 |
| weekly | noisy | 0.5 | +0.047 | +0.039 | +0.074 |
| weekly | noisy | 0.7 | +0.045 | +0.040 | +0.054 |
| weekly | noisy | 0.9 | +0.042 | +0.039 | +0.052 |
| weekly | noisy | 1.0 | +0.042 | +0.042 | +0.042 |
| weekly | proxy+ | 0.0 | +0.009 | +0.009 | +0.009 |
| weekly | proxy+ | 0.1 | +0.011 | +0.011 | +0.011 |
| weekly | proxy+ | 0.2 | +0.013 | +0.013 | +0.013 |
| weekly | proxy+ | 0.3 | +0.015 | +0.015 | +0.015 |
| weekly | proxy+ | 0.5 | +0.026 | +0.026 | +0.026 |

all: rho* = 0.1, rho*90 = 0.2
spacing: rho* = 0.0, rho*90 = 1.0
tiers: rho* = 0.1, rho*90 = 0.2
weekly: rho* = 0.0, rho*90 = 0.0

| knob | rho 0.2 | rho 0.5 | rho 0.9 |
|---|---|---|---|
| none | +0.055 | +0.108 | +0.152 |
| persistence | +0.022 | +0.100 | +0.151 |
| shared | +0.039 | +0.093 | +0.155 |
| bias -0.5 | +0.058 | +0.079 | +0.094 |
| bias +0.5 | +0.020 | +0.144 | +0.189 |
| missing | +0.058 | +0.108 | +0.140 |
| catalyst_miss | +0.055 | +0.108 | +0.152 |

## daily

### tiers

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| tiers daily none | 48.5% | 29.9% | 1.62 | +0.00 | +0.00 | +0.00 |
| tiers daily pause random 13% | 46.8% | 29.7% | 1.58 | -0.04 | -0.10 | -0.14 |
| tiers daily x0.75 | 48.0% | 28.5% | 1.69 | +0.07 | +0.35 | +0.14 |
| tiers daily x0.5 | 46.7% | 24.1% | 1.93 | +0.31 | +0.53 | +0.27 |
| tiers daily x1.0 | 48.7% | 29.6% | 1.64 | +0.02 | +0.20 | +0.04 |
| tiers daily x0.25 | 40.5% | 18.5% | 2.18 | +0.56 | -0.06 | +0.30 |
| tiers daily ceiling50 | 22.9% | 24.4% | 0.94 | -0.68 | -1.17 | -0.60 |

### oracle

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| oracle daily none | 48.5% | 29.9% | 1.62 | +0.00 | +0.00 | +0.00 |
| oracle daily worst 10% pause | 48.4% | 30.8% | 1.57 | -0.05 | -0.06 | +0.14 |
| oracle daily worst 20% pause | 48.6% | 30.0% | 1.62 | -0.00 | +0.13 | +0.04 |
| oracle daily worst 5% x0.5 | 48.8% | 30.2% | 1.62 | -0.01 | +0.01 | +0.10 |
| oracle daily worst 20% x0.5 | 48.3% | 30.1% | 1.60 | -0.02 | -0.02 | +0.09 |
| oracle daily worst 5% pause | 48.9% | 30.9% | 1.58 | -0.04 | +0.03 | +0.13 |
| oracle daily worst 10% x0.5 | 48.7% | 30.1% | 1.62 | -0.01 | -0.02 | +0.14 |

### matrix

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| matrix daily none | 48.5% | 29.9% | 1.62 | +0.00 | +0.00 | +0.00 |
| matrix daily tier0 x0.75 | 48.2% | 28.9% | 1.67 | +0.05 | +0.08 | +0.17 |
| matrix daily tier0 pause | 42.0% | 21.8% | 1.93 | +0.31 | -0.03 | -0.09 |
| matrix daily tier1 x0.75 | 48.1% | 30.0% | 1.61 | -0.01 | +0.12 | -0.04 |
| matrix daily tier1 pause | 45.1% | 25.4% | 1.78 | +0.15 | +0.01 | -0.19 |
| matrix daily tier1 x0.5 | 48.2% | 27.9% | 1.73 | +0.11 | +0.16 | -0.03 |
| matrix daily tier2 pause | 49.3% | 29.2% | 1.69 | +0.07 | +0.52 | +0.13 |
| matrix daily tier2 x0.25 | 48.8% | 29.4% | 1.66 | +0.04 | +0.37 | +0.07 |
| matrix daily tier2 x0.5 | 48.7% | 29.6% | 1.65 | +0.03 | +0.27 | +0.05 |
| matrix daily tier0 x0.5 | 47.4% | 27.6% | 1.72 | +0.10 | +0.05 | +0.17 |
| matrix daily tier1 x0.25 | 47.5% | 25.9% | 1.83 | +0.21 | +0.16 | -0.07 |
| matrix daily tier0 x0.25 | 45.5% | 24.8% | 1.84 | +0.22 | +0.02 | +0.07 |
| matrix daily tier2 x0.75 | 48.8% | 29.6% | 1.65 | +0.03 | +0.22 | +0.04 |
| matrix daily tier3 x0.75 | 48.5% | 29.9% | 1.62 | +0.00 | -0.01 | +0.10 |
| matrix daily tier3 x0.5 | 48.6% | 29.9% | 1.63 | +0.01 | -0.03 | +0.16 |
| matrix daily tier3 x0.25 | 48.6% | 29.8% | 1.63 | +0.01 | -0.05 | +0.18 |
| matrix daily tier3 pause | 48.5% | 29.9% | 1.62 | +0.00 | -0.09 | +0.19 |

### proxy

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| proxy daily none | 48.5% | 29.9% | 1.62 | +0.00 | +0.00 | +0.00 |
| proxy daily binary | 48.3% | 29.8% | 1.62 | +0.00 | +0.01 | +0.17 |
| proxy daily continuous | 48.0% | 29.6% | 1.62 | -0.00 | +0.18 | +0.14 |
| proxy daily ceiling | 44.6% | 30.2% | 1.48 | -0.15 | -0.48 | -0.02 |
| proxy daily graded | 47.1% | 30.1% | 1.56 | -0.06 | +0.04 | +0.14 |

### spacing

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| spacing daily none | 48.5% | 29.9% | 1.62 | +0.00 | +0.00 | +0.00 |
| spacing daily B e0.5 max2.0 follow=True | 48.0% | 29.9% | 1.61 | -0.01 | -0.09 | +0.05 |
| spacing daily B e0.5 max2.0 follow=False | 49.3% | 29.5% | 1.67 | +0.05 | +0.26 | +0.16 |
| spacing daily B e0.5 max4.0 follow=False | 49.3% | 29.5% | 1.67 | +0.05 | +0.26 | +0.16 |
| spacing daily B e0.5 max4.0 follow=True | 48.0% | 29.9% | 1.61 | -0.01 | -0.09 | +0.05 |
| spacing daily B e1.0 max2.0 follow=False | 49.2% | 29.3% | 1.68 | +0.06 | +0.30 | +0.22 |
| spacing daily B e1.0 max4.0 follow=False | 49.2% | 29.3% | 1.68 | +0.06 | +0.30 | +0.22 |
| spacing daily B e1.0 max2.0 follow=True | 47.5% | 30.2% | 1.57 | -0.05 | -0.21 | +0.08 |
| spacing daily B e1.0 max4.0 follow=True | 47.5% | 30.2% | 1.57 | -0.05 | -0.21 | +0.08 |
| spacing daily B + tiers | 47.7% | 28.5% | 1.67 | +0.05 | +0.10 | +0.31 |

### weekly

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| weekly daily none | 48.5% | 29.9% | 1.62 | +0.00 | +0.00 | +0.00 |
| weekly daily G next_month slope 0.25 | 47.5% | 29.4% | 1.62 | -0.00 | +0.15 | +0.01 |
| weekly daily G next_quarter slope 0.25 | 47.8% | 28.9% | 1.65 | +0.03 | +0.25 | +0.00 |
| weekly daily G next_quarter slope 0.5 | 46.9% | 28.7% | 1.63 | +0.01 | +0.37 | -0.03 |
| weekly daily G max slope 0.25 | 47.4% | 29.2% | 1.62 | +0.00 | +0.19 | -0.00 |
| weekly daily G next_month slope 0.5 | 46.3% | 29.7% | 1.56 | -0.06 | +0.14 | -0.04 |
| weekly daily G next_month slope 1.0 | 42.4% | 30.4% | 1.39 | -0.23 | -0.12 | -0.17 |
| weekly daily all levers | 45.3% | 29.3% | 1.55 | -0.08 | +0.12 | +0.24 |
| weekly daily G max slope 1.0 | 41.8% | 29.6% | 1.41 | -0.21 | +0.03 | -0.20 |
| weekly daily G max slope 0.5 | 46.0% | 29.4% | 1.56 | -0.06 | +0.21 | -0.08 |
| weekly daily G next_quarter slope 1.0 | 44.6% | 28.6% | 1.56 | -0.06 | +0.43 | -0.12 |
| weekly daily G every five sessions | 46.3% | 29.9% | 1.55 | -0.07 | +0.17 | -0.03 |

### null

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| null daily none | 48.5% | 29.9% | 1.62 | +0.00 | +0.00 | +0.00 |
| null daily tiers shift 00 | 42.7% | 25.3% | 1.69 | +0.07 | +0.74 | -0.37 |
| null daily tiers shift 03 | 42.7% | 27.0% | 1.58 | -0.04 | +0.76 | -0.37 |
| null daily tiers shift 02 | 39.4% | 29.9% | 1.32 | -0.30 | -1.05 | -0.01 |
| null daily tiers shift 01 | 40.6% | 31.4% | 1.29 | -0.33 | -0.83 | -0.21 |
| null daily tiers real | 47.1% | 30.1% | 1.56 | -0.06 | +0.04 | +0.14 |
| null daily tiers shift 04 | 44.2% | 29.8% | 1.48 | -0.14 | +0.27 | -0.16 |
| null daily tiers shift 06 | 44.5% | 30.2% | 1.47 | -0.15 | -0.29 | +0.05 |
| null daily tiers shift 05 | 41.8% | 29.7% | 1.41 | -0.21 | +0.19 | -0.34 |
| null daily tiers shift 07 | 43.5% | 23.4% | 1.86 | +0.24 | -0.35 | +0.03 |
| null daily tiers shift 08 | 44.7% | 30.0% | 1.49 | -0.13 | +0.08 | +0.04 |
| null daily tiers shift 09 | 44.9% | 29.4% | 1.53 | -0.09 | +0.33 | +0.01 |
| null daily tiers shift 12 | 43.7% | 27.9% | 1.56 | -0.06 | +0.32 | -0.27 |
| null daily tiers shift 11 | 41.6% | 30.1% | 1.38 | -0.24 | +0.08 | -0.46 |
| null daily tiers shift 10 | 44.9% | 26.3% | 1.70 | +0.08 | -0.39 | -0.12 |
| null daily tiers shift 13 | 46.9% | 19.7% | 2.38 | +0.76 | +0.02 | +1.22 |
| null daily tiers shift 14 | 44.6% | 24.2% | 1.84 | +0.22 | -0.48 | +0.53 |
| null daily tiers shift 17 | 40.6% | 31.8% | 1.28 | -0.34 | -0.02 | -0.19 |
| null daily tiers shift 16 | 44.5% | 24.5% | 1.82 | +0.20 | +0.21 | -0.19 |
| null daily tiers shift 18 | 35.7% | 30.3% | 1.18 | -0.44 | +0.31 | -0.68 |
| null daily tiers shift 19 | 40.1% | 25.4% | 1.58 | -0.04 | +0.17 | -0.21 |
| null daily tiers shift 15 | 42.2% | 24.4% | 1.73 | +0.11 | -0.18 | -0.08 |
| null daily tiers shift 20 | 35.7% | 30.3% | 1.18 | -0.44 | +0.31 | -0.68 |
| null daily tiers shift 21 | 38.4% | 28.7% | 1.34 | -0.28 | +0.36 | -0.66 |
| null daily tiers shift 22 | 44.9% | 30.0% | 1.50 | -0.13 | +0.51 | +0.13 |
| null daily tiers shift 24 | 44.1% | 29.5% | 1.50 | -0.12 | +0.27 | -0.18 |
| null daily tiers shift 26 | 44.0% | 28.9% | 1.52 | -0.10 | +0.29 | +0.01 |
| null daily tiers shift 27 | 47.1% | 25.0% | 1.88 | +0.26 | +0.21 | -0.00 |
| null daily tiers shift 31 | 39.3% | 33.7% | 1.16 | -0.46 | -0.47 | -0.18 |
| null daily tiers shift 23 | 42.3% | 28.0% | 1.51 | -0.11 | -0.33 | -0.13 |
| null daily tiers shift 32 | 43.4% | 26.9% | 1.62 | -0.01 | -0.25 | +0.19 |
| null daily tiers shift 25 | 44.0% | 23.7% | 1.86 | +0.24 | -0.80 | +0.54 |
| null daily tiers shift 28 | 44.0% | 22.1% | 1.99 | +0.37 | -0.45 | +0.72 |
| null daily tiers shift 30 | 46.5% | 19.9% | 2.34 | +0.72 | +0.26 | +0.09 |
| null daily tiers shift 33 | 43.0% | 26.7% | 1.61 | -0.01 | -0.10 | -0.05 |
| null daily tiers shift 34 | 47.5% | 22.3% | 2.13 | +0.51 | +0.05 | +1.29 |
| null daily tiers shift 35 | 44.1% | 19.9% | 2.21 | +0.59 | +0.10 | -0.17 |
| null daily tiers shift 29 | 44.0% | 23.7% | 1.86 | +0.24 | -0.80 | +0.54 |
| null daily tiers shift 38 | 44.9% | 32.0% | 1.40 | -0.22 | -0.37 | +0.25 |
| null daily tiers shift 36 | 41.7% | 29.0% | 1.44 | -0.18 | -0.97 | -0.09 |
| null daily tiers shift 39 | 44.6% | 24.2% | 1.84 | +0.22 | -0.48 | +0.53 |
| null daily spacing real | 49.2% | 29.3% | 1.68 | +0.06 | +0.30 | +0.22 |
| null daily spacing shift 00 | 46.6% | 27.5% | 1.70 | +0.08 | +0.11 | -0.14 |
| null daily tiers shift 37 | 37.4% | 28.5% | 1.31 | -0.31 | +0.27 | -0.68 |
| null daily spacing shift 01 | 47.0% | 30.1% | 1.56 | -0.06 | -0.15 | +0.04 |
| null daily spacing shift 02 | 48.6% | 29.2% | 1.66 | +0.04 | -0.09 | +0.27 |
| null daily spacing shift 03 | 47.2% | 29.8% | 1.58 | -0.04 | +0.37 | -0.16 |
| null daily spacing shift 04 | 45.2% | 29.5% | 1.53 | -0.09 | +0.20 | -0.16 |
| null daily spacing shift 05 | 45.8% | 29.6% | 1.55 | -0.07 | +0.51 | -0.26 |
| null daily spacing shift 06 | 47.8% | 30.1% | 1.59 | -0.03 | +0.11 | +0.07 |
| null daily spacing shift 07 | 47.1% | 26.2% | 1.80 | +0.18 | +0.08 | -0.06 |
| null daily spacing shift 08 | 48.3% | 29.0% | 1.66 | +0.04 | +0.06 | +0.21 |
| null daily spacing shift 09 | 46.8% | 29.6% | 1.58 | -0.04 | +0.45 | -0.14 |
| null daily spacing shift 10 | 47.3% | 28.9% | 1.64 | +0.02 | +0.26 | -0.10 |
| null daily spacing shift 11 | 45.5% | 29.7% | 1.53 | -0.09 | +0.31 | -0.30 |
| null daily spacing shift 13 | 48.8% | 23.8% | 2.05 | +0.43 | -0.08 | +0.87 |
| null daily spacing shift 12 | 46.2% | 28.8% | 1.61 | -0.02 | +0.22 | -0.08 |
| null daily spacing shift 16 | 46.6% | 26.6% | 1.76 | +0.13 | +0.26 | -0.22 |
| null daily spacing shift 15 | 45.9% | 27.5% | 1.67 | +0.04 | +0.04 | +0.06 |
| null daily spacing shift 17 | 48.6% | 29.6% | 1.64 | +0.02 | +0.58 | +0.03 |

*The first 60 of 124 runs; every run is in results.jsonl, and the lines below count them all.*

tiers: the real schedule beats 21 of 40 shifted copies on Calmar.

spacing: the real schedule beats 30 of 40 shifted copies on Calmar.

weekly: the real schedule beats 7 of 40 shifted copies on Calmar.

### robust

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| robust daily none | 48.5% | 29.9% | 1.62 | +0.00 | +0.00 | +0.00 |
| robust daily without volatility | 46.3% | 29.7% | 1.56 | -0.06 | +0.00 | +0.11 |
| robust daily without regime | 47.4% | 29.2% | 1.62 | -0.00 | +0.17 | +0.13 |
| robust daily thresholds -0.05 | 46.9% | 29.8% | 1.57 | -0.05 | +0.03 | +0.14 |
| robust daily without gap | 47.4% | 29.7% | 1.60 | -0.02 | -0.00 | +0.18 |
| robust daily thresholds +0.05 | 47.6% | 29.9% | 1.59 | -0.03 | +0.11 | +0.13 |
| robust daily without catalyst | 47.0% | 29.8% | 1.57 | -0.05 | -0.05 | +0.16 |
| robust daily reversals not exempt | 45.7% | 30.7% | 1.49 | -0.13 | -0.23 | +0.13 |
| robust daily without tail | 47.4% | 30.0% | 1.58 | -0.04 | +0.08 | +0.12 |

### stress

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| stress daily none | 48.5% | 29.9% | 1.62 | +0.00 | +0.00 | +0.00 |
| stress daily grind none | 46.4% | 24.3% | 1.91 | +0.29 | -0.01 | -0.25 |
| stress daily deeper none | 44.9% | 33.8% | 1.33 | -0.29 | -0.01 | -0.39 |
| stress daily twice none | 42.5% | 31.5% | 1.35 | -0.27 | +0.00 | -0.22 |
| stress daily deeper tiers | 44.4% | 32.6% | 1.36 | -0.26 | +0.03 | -0.19 |
| stress daily grind tiers | 45.5% | 20.6% | 2.21 | +0.59 | +0.04 | -0.04 |
| stress daily fast none | 39.8% | 33.7% | 1.18 | -0.44 | -1.15 | -0.35 |
| stress daily fast tiers | 39.4% | 34.0% | 1.16 | -0.46 | -1.09 | +0.03 |
| stress daily twice tiers | 39.7% | 31.1% | 1.28 | -0.34 | +0.04 | -0.48 |

deeper: the tiers move max DD by -1.2 points.

grind: the tiers move max DD by -3.7 points.

fast: the tiers move max DD by +0.3 points.

twice: the tiers move max DD by -0.4 points.

### perturb

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| perturb daily none | 48.5% | 29.9% | 1.62 | +0.00 | +0.00 | +0.00 |
| perturb daily always3 | 7.1% | 31.0% | 0.23 | -1.39 | -3.27 | -1.05 |
| perturb daily random 50% | 46.8% | 28.9% | 1.62 | -0.01 | -0.15 | +0.15 |
| perturb daily inverted | 35.3% | 16.4% | 2.15 | +0.53 | +0.55 | -0.30 |
| perturb daily always0 | 48.7% | 29.6% | 1.64 | +0.02 | +0.20 | +0.04 |
| perturb daily random 25% | 46.6% | 29.3% | 1.59 | -0.04 | -0.03 | +0.12 |
| perturb daily random 10% | 47.7% | 30.0% | 1.59 | -0.03 | +0.12 | +0.15 |

### catalysts

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| catalysts daily none | 48.5% | 29.9% | 1.62 | +0.00 | +0.00 | +0.00 |
| catalysts daily blackout 30m | 48.5% | 29.7% | 1.64 | +0.01 | +0.16 | +0.02 |
| catalysts daily blackout 15m | 48.6% | 29.7% | 1.64 | +0.02 | +0.18 | +0.03 |
| catalysts daily blackout 10m | 48.6% | 29.6% | 1.64 | +0.02 | +0.18 | +0.03 |

### priority

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| priority daily none | 48.5% | 29.9% | 1.62 | +0.00 | +0.00 | +0.00 |
| priority daily supersedes governor | 47.2% | 30.2% | 1.56 | -0.06 | -0.01 | +0.14 |
| priority daily supersedes both | 47.1% | 30.1% | 1.56 | -0.06 | +0.04 | +0.14 |
| priority daily supersedes neither | 47.2% | 30.2% | 1.56 | -0.06 | -0.01 | +0.14 |

### advisory

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| advisory daily none | 48.5% | 29.9% | 1.62 | +0.00 | +0.00 | +0.00 |
| advisory daily follow 0.5 after 0m seed 1 | 48.4% | 29.9% | 1.62 | -0.00 | -0.07 | +0.09 |
| advisory daily follow 0.5 after 0m seed 0 | 48.2% | 29.9% | 1.61 | -0.01 | -0.09 | +0.01 |
| advisory daily follow 0.5 after 0m seed 3 | 49.0% | 29.9% | 1.64 | +0.02 | +0.01 | +0.21 |
| advisory daily follow 0.5 after 0m seed 2 | 48.7% | 29.9% | 1.63 | +0.01 | +0.02 | +0.18 |
| advisory daily follow 0.5 after 0m seed 4 | 48.6% | 29.9% | 1.63 | +0.00 | -0.06 | +0.09 |
| advisory daily follow 0.5 after 0m seed 5 | 48.5% | 29.8% | 1.63 | +0.01 | +0.04 | +0.01 |
| advisory daily follow 0.5 after 0m seed 6 | 48.7% | 29.9% | 1.63 | +0.01 | +0.01 | +0.19 |
| advisory daily follow 0.5 after 0m seed 9 | 48.8% | 29.9% | 1.63 | +0.01 | -0.05 | +0.13 |
| advisory daily follow 0.5 after 0m seed 10 | 48.3% | 29.9% | 1.62 | -0.00 | -0.07 | +0.01 |
| advisory daily follow 0.5 after 0m seed 7 | 48.9% | 29.8% | 1.64 | +0.02 | +0.02 | +0.19 |
| advisory daily follow 0.5 after 0m seed 8 | 48.6% | 29.9% | 1.63 | +0.01 | -0.04 | +0.09 |
| advisory daily follow 0.5 after 0m seed 12 | 48.4% | 29.9% | 1.62 | -0.00 | +0.01 | +0.01 |
| advisory daily follow 0.5 after 0m seed 14 | 48.6% | 29.9% | 1.63 | +0.00 | +0.01 | +0.17 |
| advisory daily follow 0.5 after 0m seed 11 | 48.5% | 29.9% | 1.62 | -0.00 | -0.07 | +0.13 |
| advisory daily follow 0.5 after 0m seed 13 | 48.9% | 29.8% | 1.64 | +0.02 | +0.03 | +0.17 |
| advisory daily follow 0.5 after 0m seed 15 | 48.7% | 29.9% | 1.63 | +0.01 | -0.05 | +0.19 |
| advisory daily follow 0.5 after 0m seed 16 | 48.8% | 29.8% | 1.64 | +0.01 | +0.02 | +0.15 |
| advisory daily follow 0.5 after 0m seed 17 | 48.4% | 29.9% | 1.62 | -0.00 | -0.00 | +0.03 |
| advisory daily follow 0.5 after 0m seed 18 | 47.9% | 29.9% | 1.60 | -0.02 | -0.08 | -0.04 |
| advisory daily follow 0.5 after 0m seed 19 | 48.7% | 29.8% | 1.63 | +0.01 | +0.02 | +0.09 |
| advisory daily follow 0.5 after 30m seed 0 | 48.2% | 29.9% | 1.61 | -0.01 | -0.09 | +0.01 |
| advisory daily follow 0.5 after 30m seed 1 | 48.4% | 29.9% | 1.62 | +0.00 | -0.07 | +0.09 |
| advisory daily follow 0.5 after 30m seed 4 | 48.6% | 29.8% | 1.63 | +0.01 | -0.06 | +0.09 |
| advisory daily follow 0.5 after 30m seed 2 | 48.7% | 29.9% | 1.63 | +0.01 | +0.02 | +0.18 |
| advisory daily follow 0.5 after 30m seed 3 | 49.0% | 29.8% | 1.64 | +0.02 | +0.02 | +0.21 |
| advisory daily follow 0.5 after 30m seed 6 | 48.7% | 29.9% | 1.63 | +0.01 | +0.01 | +0.19 |
| advisory daily follow 0.5 after 30m seed 8 | 48.5% | 29.8% | 1.63 | +0.01 | -0.05 | +0.08 |
| advisory daily follow 0.5 after 30m seed 5 | 48.4% | 29.8% | 1.63 | +0.00 | +0.03 | +0.00 |
| advisory daily follow 0.5 after 30m seed 7 | 48.8% | 29.8% | 1.64 | +0.02 | +0.01 | +0.19 |
| advisory daily follow 0.5 after 30m seed 9 | 48.8% | 29.8% | 1.63 | +0.01 | -0.06 | +0.12 |
| advisory daily follow 0.5 after 30m seed 11 | 48.5% | 29.9% | 1.62 | -0.00 | -0.07 | +0.13 |
| advisory daily follow 0.5 after 30m seed 12 | 48.4% | 29.9% | 1.62 | -0.00 | +0.01 | +0.00 |
| advisory daily follow 0.5 after 30m seed 10 | 48.3% | 29.9% | 1.62 | -0.00 | -0.06 | +0.01 |
| advisory daily follow 0.5 after 30m seed 14 | 48.5% | 29.9% | 1.62 | +0.00 | +0.01 | +0.16 |
| advisory daily follow 0.5 after 30m seed 13 | 48.8% | 29.8% | 1.64 | +0.02 | +0.02 | +0.16 |
| advisory daily follow 0.5 after 30m seed 15 | 48.6% | 29.8% | 1.63 | +0.01 | -0.06 | +0.19 |
| advisory daily follow 0.5 after 30m seed 16 | 48.8% | 29.8% | 1.64 | +0.02 | +0.02 | +0.15 |
| advisory daily follow 0.5 after 30m seed 17 | 48.3% | 29.9% | 1.62 | -0.00 | -0.01 | +0.03 |
| advisory daily follow 0.5 after 30m seed 18 | 48.0% | 29.9% | 1.60 | -0.02 | -0.07 | -0.03 |
| advisory daily follow 0.5 after 30m seed 19 | 48.7% | 29.8% | 1.64 | +0.01 | +0.02 | +0.09 |
| advisory daily follow 0.5 after 90m seed 0 | 48.3% | 29.9% | 1.61 | -0.01 | -0.08 | +0.01 |
| advisory daily follow 0.5 after 90m seed 2 | 48.6% | 29.9% | 1.63 | +0.01 | +0.02 | +0.18 |
| advisory daily follow 0.5 after 90m seed 1 | 48.5% | 29.9% | 1.62 | +0.00 | -0.06 | +0.09 |
| advisory daily follow 0.5 after 90m seed 4 | 48.6% | 29.8% | 1.63 | +0.01 | -0.05 | +0.09 |
| advisory daily follow 0.5 after 90m seed 3 | 49.0% | 29.8% | 1.65 | +0.02 | +0.03 | +0.21 |
| advisory daily follow 0.5 after 90m seed 5 | 48.4% | 29.8% | 1.63 | +0.00 | +0.03 | +0.00 |
| advisory daily follow 0.5 after 90m seed 8 | 48.5% | 29.8% | 1.63 | +0.01 | -0.06 | +0.08 |
| advisory daily follow 0.5 after 90m seed 7 | 48.8% | 29.8% | 1.64 | +0.02 | +0.01 | +0.19 |
| advisory daily follow 0.5 after 90m seed 11 | 48.5% | 29.9% | 1.62 | -0.00 | -0.07 | +0.12 |
| advisory daily follow 0.5 after 90m seed 6 | 48.7% | 29.9% | 1.63 | +0.01 | +0.01 | +0.18 |
| advisory daily follow 0.5 after 90m seed 9 | 48.8% | 29.8% | 1.63 | +0.01 | -0.06 | +0.12 |
| advisory daily follow 0.5 after 90m seed 10 | 48.4% | 29.8% | 1.62 | +0.00 | -0.05 | +0.01 |
| advisory daily follow 0.5 after 90m seed 12 | 48.4% | 29.9% | 1.62 | -0.00 | +0.01 | +0.00 |
| advisory daily follow 0.5 after 90m seed 13 | 48.8% | 29.8% | 1.64 | +0.02 | +0.02 | +0.16 |
| advisory daily follow 0.5 after 90m seed 14 | 48.5% | 29.9% | 1.62 | +0.00 | +0.01 | +0.16 |
| advisory daily follow 0.5 after 90m seed 16 | 48.8% | 29.8% | 1.64 | +0.02 | +0.02 | +0.15 |
| advisory daily follow 0.5 after 90m seed 15 | 48.6% | 29.8% | 1.63 | +0.01 | -0.06 | +0.19 |
| advisory daily follow 0.5 after 90m seed 19 | 48.7% | 29.8% | 1.64 | +0.01 | +0.02 | +0.09 |
| advisory daily follow 0.8 after 0m seed 2 | 48.5% | 29.9% | 1.62 | -0.00 | -0.09 | +0.19 |

*The first 60 of 181 runs; every run is in results.jsonl, and the lines below count them all.*

| follows | after | seeds | d return | d max DD | d Calmar | seeds better |
|---|---|---|---|---|---|---|
| 50% | 0 min | 20 | +0.11 pts | -0.02 pts | +0.005 | 13 of 20 |
| 50% | 30 min | 20 | +0.09 pts | -0.04 pts | +0.005 | 14 of 20 |
| 50% | 90 min | 20 | +0.10 pts | -0.04 pts | +0.006 | 15 of 20 |
| 80% | 0 min | 20 | +0.19 pts | -0.00 pts | +0.007 | 17 of 20 |
| 80% | 30 min | 20 | +0.19 pts | -0.03 pts | +0.008 | 19 of 20 |
| 80% | 90 min | 20 | +0.23 pts | -0.04 pts | +0.010 | 19 of 20 |
| 100% | 0 min | 20 | +0.08 pts | +0.03 pts | +0.001 | 20 of 20 |
| 100% | 30 min | 20 | +0.11 pts | -0.01 pts | +0.004 | 20 of 20 |
| 100% | 90 min | 20 | +0.17 pts | -0.03 pts | +0.007 | 20 of 20 |

### accuracy

| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |
|---|---|---|---|---|---|---|
| accuracy daily none | 48.5% | 29.9% | 1.62 | +0.00 | +0.00 | +0.00 |
| accuracy daily tiers mixture 0.0 seed 1 | 48.1% | 26.1% | 1.84 | +0.22 | +0.28 | +0.08 |
| accuracy daily tiers mixture 0.0 seed 0 | 47.1% | 26.2% | 1.80 | +0.18 | +0.10 | +0.33 |
| accuracy daily tiers mixture 0.0 seed 8 | 47.0% | 27.8% | 1.69 | +0.07 | +0.39 | +0.11 |
| accuracy daily tiers mixture 0.0 seed 2 | 48.9% | 26.4% | 1.85 | +0.23 | +0.60 | +0.14 |
| accuracy daily tiers mixture 0.0 seed 4 | 47.1% | 29.0% | 1.63 | +0.00 | +0.38 | +0.15 |
| accuracy daily tiers mixture 0.0 seed 10 | 47.1% | 28.4% | 1.66 | +0.04 | -0.06 | +0.11 |
| accuracy daily tiers mixture 0.0 seed 3 | 47.8% | 26.8% | 1.78 | +0.16 | +0.23 | +0.32 |
| accuracy daily tiers mixture 0.0 seed 5 | 49.4% | 21.5% | 2.30 | +0.68 | +0.80 | +0.58 |
| accuracy daily tiers mixture 0.0 seed 6 | 47.9% | 27.6% | 1.73 | +0.11 | +0.70 | +0.06 |
| accuracy daily tiers mixture 0.0 seed 12 | 49.5% | 21.7% | 2.28 | +0.66 | +0.52 | +0.60 |
| accuracy daily tiers mixture 0.0 seed 11 | 47.4% | 27.5% | 1.73 | +0.10 | +0.11 | +0.13 |
| accuracy daily tiers mixture 0.0 seed 15 | 47.5% | 28.1% | 1.69 | +0.07 | +0.14 | +0.28 |
| accuracy daily tiers mixture 0.0 seed 7 | 46.7% | 27.8% | 1.68 | +0.06 | +0.14 | +0.13 |
| accuracy daily tiers mixture 0.0 seed 14 | 47.4% | 27.4% | 1.73 | +0.11 | +0.44 | +0.25 |
| accuracy daily tiers mixture 0.0 seed 13 | 47.3% | 28.8% | 1.64 | +0.02 | +0.19 | +0.05 |
| accuracy daily tiers mixture 0.0 seed 9 | 48.0% | 27.8% | 1.73 | +0.11 | +0.48 | +0.12 |
| accuracy daily tiers mixture 0.0 seed 17 | 47.6% | 27.7% | 1.72 | +0.10 | +0.07 | +0.18 |
| accuracy daily tiers mixture 0.0 seed 18 | 47.8% | 29.0% | 1.65 | +0.03 | +0.58 | +0.06 |
| accuracy daily tiers mixture 0.1 seed 2 | 49.0% | 26.2% | 1.87 | +0.25 | +0.63 | +0.14 |
| accuracy daily tiers mixture 0.1 seed 0 | 48.1% | 26.2% | 1.84 | +0.22 | +0.19 | +0.40 |
| accuracy daily tiers mixture 0.1 seed 4 | 47.9% | 28.5% | 1.68 | +0.06 | +0.60 | +0.17 |
| accuracy daily tiers mixture 0.0 seed 16 | 46.7% | 28.9% | 1.62 | -0.00 | -0.00 | +0.36 |
| accuracy daily tiers mixture 0.1 seed 5 | 49.5% | 21.1% | 2.34 | +0.72 | +0.76 | +0.60 |
| accuracy daily tiers mixture 0.0 seed 19 | 47.7% | 28.3% | 1.69 | +0.06 | +0.12 | +0.21 |
| accuracy daily tiers mixture 0.1 seed 6 | 48.2% | 28.0% | 1.72 | +0.10 | +0.57 | +0.11 |
| accuracy daily tiers mixture 0.1 seed 1 | 48.7% | 25.9% | 1.88 | +0.26 | +0.33 | +0.14 |
| accuracy daily tiers mixture 0.1 seed 3 | 47.4% | 26.9% | 1.76 | +0.14 | +0.17 | +0.26 |
| accuracy daily tiers mixture 0.1 seed 7 | 47.4% | 27.4% | 1.73 | +0.11 | +0.24 | +0.17 |
| accuracy daily tiers mixture 0.1 seed 12 | 48.8% | 22.0% | 2.22 | +0.60 | +0.22 | +0.74 |
| accuracy daily tiers mixture 0.1 seed 15 | 48.0% | 27.2% | 1.76 | +0.14 | +0.21 | +0.31 |
| accuracy daily tiers mixture 0.1 seed 19 | 47.8% | 28.0% | 1.71 | +0.09 | +0.07 | +0.33 |
| accuracy daily tiers mixture 0.1 seed 10 | 48.1% | 28.0% | 1.72 | +0.10 | +0.06 | +0.15 |
| accuracy daily tiers mixture 0.1 seed 18 | 48.5% | 28.3% | 1.71 | +0.09 | +0.82 | +0.12 |
| accuracy daily tiers mixture 0.1 seed 17 | 47.9% | 27.3% | 1.75 | +0.13 | +0.02 | +0.29 |
| accuracy daily tiers mixture 0.1 seed 8 | 47.1% | 27.7% | 1.70 | +0.08 | +0.44 | +0.09 |
| accuracy daily tiers mixture 0.2 seed 3 | 47.4% | 26.2% | 1.81 | +0.19 | +0.11 | +0.31 |
| accuracy daily tiers mixture 0.2 seed 2 | 48.8% | 29.0% | 1.69 | +0.06 | +0.54 | +0.17 |
| accuracy daily tiers mixture 0.1 seed 9 | 48.6% | 27.4% | 1.78 | +0.16 | +0.51 | +0.15 |
| accuracy daily tiers mixture 0.2 seed 0 | 48.6% | 25.9% | 1.88 | +0.25 | +0.36 | +0.46 |
| accuracy daily tiers mixture 0.1 seed 11 | 48.1% | 26.1% | 1.84 | +0.22 | +0.21 | +0.16 |
| accuracy daily tiers mixture 0.1 seed 13 | 47.5% | 29.0% | 1.64 | +0.02 | +0.12 | +0.11 |
| accuracy daily tiers mixture 0.2 seed 7 | 48.5% | 23.8% | 2.04 | +0.41 | +0.25 | +0.56 |
| accuracy daily tiers mixture 0.2 seed 1 | 49.0% | 25.2% | 1.94 | +0.32 | +0.31 | +0.29 |
| accuracy daily tiers mixture 0.1 seed 16 | 47.3% | 28.1% | 1.68 | +0.06 | +0.06 | +0.40 |
| accuracy daily tiers mixture 0.2 seed 8 | 47.8% | 25.1% | 1.90 | +0.28 | +0.46 | +0.17 |
| accuracy daily tiers mixture 0.2 seed 9 | 48.7% | 27.1% | 1.79 | +0.17 | +0.65 | +0.19 |
| accuracy daily tiers mixture 0.2 seed 6 | 48.4% | 28.0% | 1.73 | +0.11 | +0.55 | +0.18 |
| accuracy daily tiers mixture 0.2 seed 5 | 50.5% | 19.6% | 2.58 | +0.96 | +0.97 | +0.71 |
| accuracy daily tiers mixture 0.2 seed 4 | 48.6% | 27.8% | 1.75 | +0.13 | +0.72 | +0.30 |
| accuracy daily tiers mixture 0.2 seed 15 | 49.4% | 23.7% | 2.08 | +0.46 | +0.33 | +0.87 |
| accuracy daily tiers mixture 0.2 seed 17 | 48.1% | 27.2% | 1.77 | +0.15 | +0.06 | +0.30 |
| accuracy daily tiers mixture 0.2 seed 11 | 48.5% | 26.0% | 1.86 | +0.24 | +0.22 | +0.18 |
| accuracy daily tiers mixture 0.2 seed 13 | 48.6% | 28.8% | 1.69 | +0.07 | +0.73 | +0.14 |
| accuracy daily tiers mixture 0.2 seed 16 | 48.1% | 27.7% | 1.73 | +0.11 | +0.10 | +0.48 |
| accuracy daily tiers mixture 0.3 seed 0 | 48.6% | 25.5% | 1.90 | +0.28 | +0.31 | +0.47 |
| accuracy daily tiers mixture 0.2 seed 10 | 48.3% | 27.9% | 1.73 | +0.11 | +0.08 | +0.16 |
| accuracy daily tiers mixture 0.3 seed 2 | 49.1% | 28.5% | 1.72 | +0.10 | +0.53 | +0.22 |
| accuracy daily tiers mixture 0.2 seed 12 | 49.6% | 21.2% | 2.34 | +0.72 | +0.43 | +0.89 |
| accuracy daily tiers mixture 0.2 seed 18 | 48.9% | 28.0% | 1.74 | +0.12 | +0.89 | +0.13 |

*The first 60 of 2041 runs; every run is in results.jsonl, and the lines below count them all.*

| lever | family | accuracy | median d Calmar | p10 | p90 |
|---|---|---|---|---|---|
| None | None | None | +0.000 | +0.000 | +0.000 |
| all | mixture | 0.0 | +0.109 | +0.022 | +0.631 |
| all | mixture | 0.1 | +0.193 | +0.063 | +0.629 |
| all | mixture | 0.2 | +0.266 | +0.136 | +0.752 |
| all | mixture | 0.3 | +0.374 | +0.216 | +0.818 |
| all | mixture | 0.5 | +0.591 | +0.339 | +1.140 |
| all | mixture | 0.7 | +0.904 | +0.681 | +1.275 |
| all | mixture | 0.9 | +1.108 | +0.943 | +1.340 |
| all | mixture | 1.0 | +1.171 | +1.171 | +1.171 |
| all | noisy | 0.0 | +0.178 | +0.017 | +0.379 |
| all | noisy | 0.1 | +0.270 | +0.033 | +0.517 |
| all | noisy | 0.2 | +0.346 | +0.231 | +0.697 |
| all | noisy | 0.3 | +0.482 | +0.262 | +0.899 |
| all | noisy | 0.5 | +0.632 | +0.393 | +0.971 |
| all | noisy | 0.7 | +0.796 | +0.540 | +1.072 |
| all | noisy | 0.9 | +1.007 | +0.721 | +1.087 |
| all | noisy | 1.0 | +1.171 | +1.171 | +1.171 |
| all | proxy+ | 0.0 | -0.075 | -0.075 | -0.075 |
| all | proxy+ | 0.1 | -0.039 | -0.039 | -0.039 |
| all | proxy+ | 0.2 | +0.014 | +0.014 | +0.014 |
| all | proxy+ | 0.3 | +0.108 | +0.108 | +0.108 |
| all | proxy+ | 0.5 | +0.346 | +0.346 | +0.346 |
| spacing | mixture | 0.0 | +0.057 | +0.026 | +0.141 |
| spacing | mixture | 0.1 | +0.058 | +0.023 | +0.130 |
| spacing | mixture | 0.2 | +0.072 | +0.019 | +0.137 |
| spacing | mixture | 0.3 | +0.072 | +0.021 | +0.128 |
| spacing | mixture | 0.5 | +0.089 | +0.040 | +0.178 |
| spacing | mixture | 0.7 | +0.109 | +0.059 | +0.166 |
| spacing | mixture | 0.9 | +0.129 | +0.115 | +0.167 |
| spacing | mixture | 1.0 | +0.136 | +0.136 | +0.136 |
| spacing | noisy | 0.0 | +0.080 | +0.026 | +0.187 |
| spacing | noisy | 0.1 | +0.082 | +0.032 | +0.193 |
| spacing | noisy | 0.2 | +0.087 | +0.031 | +0.183 |
| spacing | noisy | 0.3 | +0.084 | +0.033 | +0.170 |
| spacing | noisy | 0.5 | +0.086 | +0.026 | +0.191 |
| spacing | noisy | 0.7 | +0.071 | +0.035 | +0.175 |
| spacing | noisy | 0.9 | +0.107 | +0.049 | +0.197 |
| spacing | noisy | 1.0 | +0.136 | +0.136 | +0.136 |
| spacing | proxy+ | 0.0 | +0.057 | +0.057 | +0.057 |
| spacing | proxy+ | 0.1 | +0.064 | +0.064 | +0.064 |
| spacing | proxy+ | 0.2 | +0.066 | +0.066 | +0.066 |
| spacing | proxy+ | 0.3 | +0.071 | +0.071 | +0.071 |
| spacing | proxy+ | 0.5 | +0.090 | +0.090 | +0.090 |
| tiers | mixture | 0.0 | +0.102 | +0.020 | +0.660 |
| tiers | mixture | 0.1 | +0.137 | +0.062 | +0.599 |
| tiers | mixture | 0.2 | +0.183 | +0.098 | +0.720 |
| tiers | mixture | 0.3 | +0.290 | +0.128 | +0.807 |
| tiers | mixture | 0.5 | +0.497 | +0.209 | +0.979 |
| tiers | mixture | 0.7 | +0.687 | +0.464 | +0.965 |
| tiers | mixture | 0.9 | +0.815 | +0.725 | +1.018 |
| tiers | mixture | 1.0 | +0.858 | +0.858 | +0.858 |
| tiers | noisy | 0.0 | +0.119 | +0.004 | +0.375 |
| tiers | noisy | 0.1 | +0.221 | -0.007 | +0.366 |
| tiers | noisy | 0.2 | +0.226 | +0.036 | +0.483 |
| tiers | noisy | 0.3 | +0.343 | +0.101 | +0.695 |
| tiers | noisy | 0.5 | +0.459 | +0.246 | +0.870 |
| tiers | noisy | 0.7 | +0.575 | +0.283 | +0.795 |
| tiers | noisy | 0.9 | +0.706 | +0.554 | +0.968 |
| tiers | noisy | 1.0 | +0.858 | +0.858 | +0.858 |
| tiers | proxy+ | 0.0 | -0.057 | -0.057 | -0.057 |
| tiers | proxy+ | 0.1 | -0.055 | -0.055 | -0.055 |
| tiers | proxy+ | 0.2 | -0.015 | -0.015 | -0.015 |
| tiers | proxy+ | 0.3 | +0.062 | +0.062 | +0.062 |
| tiers | proxy+ | 0.5 | +0.316 | +0.316 | +0.316 |
| weekly | mixture | 0.0 | -0.001 | -0.034 | +0.109 |
| weekly | mixture | 0.1 | +0.024 | -0.032 | +0.120 |
| weekly | mixture | 0.2 | +0.036 | -0.028 | +0.184 |
| weekly | mixture | 0.3 | +0.072 | -0.010 | +0.248 |
| weekly | mixture | 0.5 | +0.186 | +0.095 | +0.300 |
| weekly | mixture | 0.7 | +0.284 | +0.135 | +0.321 |
| weekly | mixture | 0.9 | +0.313 | +0.288 | +0.347 |
| weekly | mixture | 1.0 | +0.333 | +0.333 | +0.333 |
| weekly | noisy | 0.0 | +0.000 | -0.062 | +0.046 |
| weekly | noisy | 0.1 | +0.024 | -0.031 | +0.097 |
| weekly | noisy | 0.2 | +0.041 | -0.007 | +0.154 |
| weekly | noisy | 0.3 | +0.063 | +0.023 | +0.195 |
| weekly | noisy | 0.5 | +0.122 | +0.073 | +0.252 |
| weekly | noisy | 0.7 | +0.173 | +0.148 | +0.322 |
| weekly | noisy | 0.9 | +0.275 | +0.218 | +0.356 |
| weekly | noisy | 1.0 | +0.333 | +0.333 | +0.333 |
| weekly | proxy+ | 0.0 | -0.064 | -0.064 | -0.064 |
| weekly | proxy+ | 0.1 | -0.025 | -0.025 | -0.025 |
| weekly | proxy+ | 0.2 | +0.022 | +0.022 | +0.022 |
| weekly | proxy+ | 0.3 | +0.071 | +0.071 | +0.071 |
| weekly | proxy+ | 0.5 | +0.169 | +0.169 | +0.169 |

all: rho* = 0.0, rho*90 = 0.0
spacing: rho* = 0.0, rho*90 = 0.0
tiers: rho* = 0.0, rho*90 = 0.0
weekly: rho* = 0.0, rho*90 = 0.3

| knob | rho 0.2 | rho 0.5 | rho 0.9 |
|---|---|---|---|
| none | +0.346 | +0.632 | +1.007 |
| persistence | +0.317 | +0.655 | +1.033 |
| shared | +0.255 | +0.533 | +0.960 |
| bias -0.5 | +0.134 | +0.272 | +0.449 |
| bias +0.5 | +0.463 | +0.980 | +1.577 |
| missing | +0.353 | +0.493 | +0.871 |
| catalyst_miss | +0.346 | +0.632 | +1.007 |

