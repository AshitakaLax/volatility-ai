"""Machine-learning feature, label and dataset construction.

See ml_plan.md for the design. The short version: a model here does not
decide direction. It scores how reachable a lot's profit target is, and
the existing SizingStrategy interface consumes that score -- so nothing
in this package can create a code path that sells a lot at a loss.
"""
