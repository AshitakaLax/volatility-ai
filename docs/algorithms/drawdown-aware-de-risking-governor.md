# Drawdown-Aware De-Risking Governor

**Ledger ID RK23** · rank 23 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Risk management |
| Potential effectiveness rank | 23 (1 = strongest) |
| AI implementability rank | 138 (1 = easiest) |
| Retail advantage rank | 126 (1 = strongest) |
| Fit with this project | 🔬 built and measured (V11 throttle); the halt/liquidate tiers are research code |
| Implemented in volatility-ai | **Yes.** `dd_throttle_*` on the champion shrinks new lots as portfolio drawdown deepens (V11); a tiered ladder with a halt tier, hysteresis and a liquidation request is research code (`position_sizing.DrawdownLadder`); CPPI and the Grossman-Zhou multiplier are research code (`leads.cppi_path`, `leads.grossman_zhou_multiplier`). |
| Related ledger entries | V11, R5/S3 (catalog), RK22 |

## In one paragraph

Cut risk as the book's drawdown from its peak deepens, by steps or
continuously, and restore it by pre-set rules. The theory is Grossman
and Zhou's: to never lose more than a fixed fraction of the peak, hold
risky assets in proportion to the cushion above the drawdown floor. This
project has measured the simple version on TQQQ and found that it
changes size, not shape: return and drawdown fall together.

## The rule

```
dd_t = 1 - equity_t / max(equity_0..t)
continuous (V11):   new-lot size x f(dd_t), f falling from 1 at dd_start to a floor at dd_full
ladder (DrawdownLadder): tiers e.g. dd > 10%: 0.5x; dd > 20%: halt new lots; dd > 30%: request liquidation
Grossman-Zhou:      risky exposure = m x (W_t - alpha x peak_t)        # cushion above the floor alpha x peak
```

## Evidence

* **Grossman & Zhou (1993), *Mathematical Finance* 3(3), 241–276:** the
  optimal policy under a drawdown constraint (never below a fixed
  fraction of the running peak) holds risky assets proportional to the
  surplus over that floor; it resembles CPPI with a floor that ratchets
  with the peak. (Abstract.)
* **In this repository:** V11 on TQQQ cost 10.6 points of CAGR for 12.3
  points of drawdown, and 17.5 / 11.5 on SOXL: "shrinking lots as
  drawdown deepens scales return and drawdown together"
  (ultimate-algorithm.md, L4).

## Against, and failure modes

* Locks in losses and re-enters late (the CSV's caveat): drawdown is the
  *result* of a decline, so it acts after the damage.
* Klass & Nowicki (2005): the Grossman-Zhou strategy loses its long-run
  growth optimality in discrete time; with transaction costs it is hard
  to run near the floor. (Abstracts.)
* Path dependence: the same rule has very different outcomes in a V and
  in an L.

## Fit with volatility-ai

Fits and is built; the size-only throttle is measured and unimpressive.
The parts not yet measured are the ones that change *shape*: halting
new lots at a deep drawdown, and the liquidation tier, which is a
regime exit under the loss policy.

## How to test it here

Wire `DrawdownLadder`'s halt tier into the grid (no liquidation) and
compare with V11 on TQQQ: a halt removes the deep-drawdown lots that
need the largest recovery, which a proportional throttle only shrinks.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Grossman, S. J., Zhou, Z. (1993). "Optimal Investment Strategies for
  Controlling Drawdowns." *Mathematical Finance* 3(3), 241–276.
  <https://ideas.repec.org/a/bla/mathfi/v3y1993i3p241-276.html>. Abstract.
* Klass, M. J., Nowicki, K. (2005). "The Grossman and Zhou Investment
  Strategy Is Not Always Optimal." *Statistics & Probability Letters*
  74(3), 245–252. Abstract.
* This repository: ledger V11; `research/strategies/position_sizing.py`;
  `research/catalog/leads.py`; `docs/research/ultimate-algorithm.md` (L4).
