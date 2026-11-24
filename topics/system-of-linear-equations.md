---
slug: system-of-linear-equations
kind: topic
title: System of linear equations
summary: A system $Ax = b$ has no solution, exactly one, or infinitely many, and rank tells which.
syllabus:
  - da:linear-algebra/systems-of-linear-equations-and-solutions
prerequisites:
  - matrix-rank
status: learning
confidence: 1
tags:
  - linear-algebra
show_on:
  - portfolio
created: 2026-11-24
updated: 2026-11-24
---

## Summary

A linear system $Ax = b$ with $n$ unknowns is solved by comparing $\operatorname{rank}(A)$ with the rank of the augmented matrix $[A \mid b]$.

## Intuition

Each equation is a flat slice (a line, a plane). The solution set is where all slices meet: empty, a single point, or a whole line or plane of points.

## Definitions and theorems

- Consistent: at least one solution exists.
- Rouché-Capelli: the system is consistent exactly when $\operatorname{rank}(A) = \operatorname{rank}([A \mid b])$.
- If consistent and the rank equals $n$, the solution is unique; if the rank is less than $n$, there are infinitely many.
- Homogeneous system $Ax = 0$ always has the zero solution.

## Formulas

Number of free variables $= n - \operatorname{rank}(A)$ when the system is consistent.

## Worked examples

$x + y = 2$ and $2x + 2y = 5$: $\operatorname{rank}(A) = 1$ but $\operatorname{rank}([A \mid b]) = 2$, so there is no solution.

## Shortcuts

Compare the two ranks first; do not solve a system you can already prove inconsistent.

## Traps

- Equal ranks with $\operatorname{rank} < n$ means infinitely many solutions, not none.
- A homogeneous system is never inconsistent.

## Revision sheet

- rank(A) < rank([A|b]) -> no solution
- rank(A) = rank([A|b]) = n -> unique solution
- rank(A) = rank([A|b]) < n -> infinitely many
- free variables = n - rank(A)
- Ax = 0 always has x = 0

## Connections

Rank comes from [matrix-rank](matrix-rank.md); the standard solving method is [gaussian-elimination](gaussian-elimination.md).

## Sources

See the `sources` field of [gaussian-elimination](gaussian-elimination.md).
