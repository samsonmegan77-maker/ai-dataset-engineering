# ADR 017: Deterministic sampling and splitting

Sampling uses a local seeded PRNG. Splitting uses a seeded shuffle and fixed partition proportions without mutating global random state.
