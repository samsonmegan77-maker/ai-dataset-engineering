# ADR 009: Declarative transformations

Transformations run in fixed order: filter, normalize, map, select. Configuration is recorded so deterministic runs can be reproduced.
