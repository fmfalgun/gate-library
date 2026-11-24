---
slug: gaussian-elimination
kind: topic
title: Gaussian elimination
summary: Reduce the augmented matrix to row echelon form with row operations, then back-substitute to solve the system.
syllabus:
  - da:linear-algebra/gaussian-elimination
  - cs:engineering-mathematics/linear-algebra-system-of-linear-equations
prerequisites:
  - matrix-rank
  - system-of-linear-equations
sources:
  - label: GeeksforGeeks - Linear Algebra (LMNs), Gaussian elimination
    url: https://www.geeksforgeeks.org/data-science/lmns-linear-algebra/#gaussian-elimination
status: learning
confidence: 2
tags:
  - linear-algebra
show_on:
  - portfolio
created: 2026-11-24
updated: 2026-11-24
---

## Summary

Gaussian elimination solves $Ax = b$ by applying row operations to the augmented matrix $[A \mid b]$ until it is in row echelon form (zeros below every pivot), then solving from the last row upward. The pivots also give the rank.

## Intuition

Eliminate one unknown at a time. Use the first equation to remove $x_1$ from every equation below it, the second to remove $x_2$ from those below it, and so on. What remains is a staircase that can be solved from the bottom.

## Definitions and theorems

- Elementary row operations: swap two rows; multiply a row by a non-zero constant; add a multiple of one row to another. None of them changes the solution set.
- Row echelon form: each pivot is to the right of the pivot above it, and rows of zeros are at the bottom.
- Reduced row echelon form (Gauss-Jordan) also makes every pivot $1$ and clears the entries above pivots.
- Partial pivoting: swap in the row with the largest entry in the pivot column to limit rounding error.

## Formulas

To clear entry $a_{ik}$ below pivot $a_{kk}$ use $R_i \leftarrow R_i - \dfrac{a_{ik}}{a_{kk}}\, R_k$.

Cost for an $n \times n$ system: about $\tfrac{2}{3}n^3$ arithmetic operations, so $O(n^3)$. Back-substitution is $O(n^2)$.

## Worked examples

Solve $x + y + z = 6$, $2x + 3y + z = 11$, $2x + y + 2z = 10$.

1. $R_2 \leftarrow R_2 - 2R_1$ gives $y - z = -1$. $R_3 \leftarrow R_3 - 2R_1$ gives $-y = -2$.
2. The last row gives $y = 2$. Then $z = y + 1 = 3$ and $x = 6 - 2 - 3 = 1$.

Check in equation 2: $2 + 6 + 3 = 11$.

## Shortcuts

- Reading the echelon form gives the rank at once, and it gives consistency: a row $[0\ 0\ \cdots\ 0 \mid c]$ with $c \ne 0$ means no solution.
- Pick a pivot of $1$ or $-1$ by swapping rows to avoid fractions.
- The determinant of a square matrix is the product of the pivots, with a sign flip for each row swap.

## Traps

- Multiplying a row by $0$ is not allowed: it destroys information.
- When a row swap happens, the determinant changes sign; forgetting this is a common error.
- A zero pivot does not mean failure: look for a non-zero entry below it and swap.
- Free variables (columns without pivots) mean infinitely many solutions, not no solution.

## Revision sheet

- augmented matrix [A|b] -> row echelon form -> back-substitute
- allowed row operations: swap, scale by non-zero, add a multiple of another row
- rank = number of non-zero rows in echelon form
- row [0 ... 0 | c], c != 0 -> inconsistent
- rank < n with consistent system -> infinitely many solutions
- det = product of pivots, x (-1) per row swap
- cost: O(n^3) elimination, O(n^2) back-substitution
- partial pivoting limits rounding error

## Connections

Prerequisites: [matrix-rank](matrix-rank.md) for reading the result and [system-of-linear-equations](system-of-linear-equations.md) for the three possible outcomes.

## Sources

- GeeksforGeeks, Linear Algebra (LMNs), section on Gaussian elimination: <https://www.geeksforgeeks.org/data-science/lmns-linear-algebra/#gaussian-elimination>
