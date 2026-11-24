---
slug: matrix-rank
kind: topic
title: Matrix rank
summary: The rank of a matrix is the number of linearly independent rows (equivalently columns), and it decides how many solutions a linear system has.
syllabus:
  - da:linear-algebra/rank
  - da:linear-algebra/nullity
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

The rank of an $m \times n$ matrix $A$ is the number of pivots left after row reduction. It equals the dimension of the row space and of the column space. The nullity is $n - \operatorname{rank}(A)$.

## Intuition

Each independent row adds one real constraint. A row that is a combination of the others adds nothing, so rank counts only the constraints that matter.

## Definitions and theorems

- $\operatorname{rank}(A)$ = dimension of the column space = dimension of the row space.
- Rank-nullity theorem: $\operatorname{rank}(A) + \operatorname{nullity}(A) = n$, where $n$ is the number of columns.
- $\operatorname{rank}(A) \le \min(m, n)$; equality means full rank.
- A square matrix is invertible exactly when its rank equals its size.

## Formulas

$$\operatorname{rank}(A) + \dim \ker(A) = n$$

$$\operatorname{rank}(AB) \le \min(\operatorname{rank}(A), \operatorname{rank}(B))$$

## Worked examples

For $A = \begin{pmatrix} 1 & 2 \\ 2 & 4 \end{pmatrix}$ the second row is twice the first, so one pivot remains: rank 1 and nullity 1.

## Shortcuts

- Count non-zero rows after reducing to row echelon form.
- A square matrix with determinant $0$ has rank less than its size.

## Traps

- Rank counts independent rows, not non-zero rows of the original matrix.
- Rank is unchanged by row operations but the pivot positions are not unique to the matrix itself.

## Revision sheet

- rank = number of pivots in echelon form
- rank = dim(row space) = dim(column space)
- rank + nullity = number of columns
- rank <= min(rows, columns)
- invertible square matrix <=> full rank <=> det != 0

## Connections

Rank is the test used in [system-of-linear-equations](system-of-linear-equations.md) to decide consistency, and row reduction to find it is [gaussian-elimination](gaussian-elimination.md).

## Sources

See the `sources` field of [gaussian-elimination](gaussian-elimination.md) for the study page used for this group of topics.
