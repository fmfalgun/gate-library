---
slug: linear-algebra
kind: topic
title: Linear algebra (overview)
summary: Map of GATE linear algebra, from vector spaces and matrix types to determinants, eigenvalues, LU, projections and SVD, with the key facts and the traps that PYQs test.
syllabus:
  - cs:engineering-mathematics/linear-algebra-matrices
  - cs:engineering-mathematics/linear-algebra-determinants
  - cs:engineering-mathematics/linear-algebra-eigenvalues-and-eigenvectors
  - cs:engineering-mathematics/linear-algebra-lu-decomposition
  - da:linear-algebra/vector-space
  - da:linear-algebra/subspaces
  - da:linear-algebra/linear-dependence-and-independence-of-vectors
  - da:linear-algebra/matrices
  - da:linear-algebra/projection-matrix
  - da:linear-algebra/orthogonal-matrix
  - da:linear-algebra/idempotent-matrix
  - da:linear-algebra/partition-matrix-and-their-properties
  - da:linear-algebra/eigenvalues-and-eigenvectors
  - da:linear-algebra/determinant
  - da:linear-algebra/lu-decomposition
  - da:linear-algebra/singular-value-decomposition
related:
  - matrix-rank
  - system-of-linear-equations
  - gaussian-elimination
sources:
  - label: GeeksforGeeks - Linear Algebra (LMNs)
    url: https://www.geeksforgeeks.org/lmns-linear-algebra/
  - label: GATE 2027 CS syllabus (IIT Madras)
    url: https://gate2027.iitm.ac.in/static/doc/GATE2027_Syllabus/CS_GATE2027_Syllabus.pdf
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

GATE linear algebra is about square matrices: their types, their determinant, their rank, and above all their eigenvalues. A matrix $A$ ($m \times n$) is a linear map from $\mathbb{R}^n$ to $\mathbb{R}^m$. Rank says how many directions survive the map, the determinant says how volume scales, and eigenvalues say which directions are only stretched. CS tests matrices, determinants, linear systems, eigenvalues and LU. DA adds vector spaces, projections, partitioned matrices, quadratic forms and SVD. This page is the map; the detailed pages are [matrix-rank](matrix-rank.md), [system-of-linear-equations](system-of-linear-equations.md) and [gaussian-elimination](gaussian-elimination.md).

## Intuition

- A **vector space** is a set you can add and scale without leaving it. A **subspace** is a flat piece of it that passes through the origin.
- **Independent** vectors each add a new direction. A **basis** is a minimal set of directions that reaches everything, and the **dimension** is how many directions that takes.
- **Determinant**: the factor by which $A$ scales area or volume. If it is $0$, some direction is squashed flat, so $A$ cannot be undone.
- **Eigenvector**: a direction that $A$ only stretches, by the factor $\lambda$.
- **Projection**: drop a vector onto a subspace. Doing it twice changes nothing, so $P^2 = P$.

## Definitions and theorems

**Vector spaces (DA)**
- Subspace test: $W \subseteq V$ is a subspace if and only if $\mathbf{0} \in W$ and $W$ is closed under addition and scalar multiplication.
- Linear independence: $c_1 v_1 + \dots + c_k v_k = \mathbf{0}$ forces every $c_i = 0$.
- Basis: an independent spanning set. Dimension: the size of any basis. $\dim \mathbb{R}^n = n$, $\dim M_{m\times n} = mn$.
- More than $n$ vectors in $\mathbb{R}^n$ are always dependent.
- Subspace dimensions: $\dim(U + W) = \dim U + \dim W - \dim(U \cap W)$.

**Matrix types**

| Type | Condition | Key facts |
|---|---|---|
| Symmetric | $A^T = A$ | real eigenvalues; eigenvectors for distinct $\lambda$ are orthogonal; always diagonalisable |
| Skew-symmetric | $A^T = -A$ | zero diagonal; eigenvalues $0$ or purely imaginary; $\det A = 0$ when $n$ is odd |
| Orthogonal | $A^TA = I$ | $\det = \pm 1$; every eigenvalue has $\lvert\lambda\rvert = 1$ (it may be complex); preserves lengths |
| Idempotent | $A^2 = A$ | eigenvalues $0$ or $1$; $\operatorname{tr}A = \operatorname{rank}A$; singular unless $A = I$ |
| Nilpotent | $A^k = 0$ for some $k$ | all eigenvalues $0$; $\operatorname{tr}A = 0$, $\det A = 0$; $I - A$ is invertible |
| Involutory | $A^2 = I$ | eigenvalues $\pm 1$; $A^{-1} = A$ |

**Determinant and inverse**
- $\det A^T = \det A$, $\det(AB) = \det A \det B$, $\det(kA) = k^n \det A$ for $n \times n$.
- Row operations: a swap flips the sign, scaling a row by $k$ multiplies $\det$ by $k$, and adding a multiple of another row leaves it unchanged.
- Triangular matrix: $\det$ = product of the diagonal.
- $A \operatorname{adj}(A) = \det(A)\, I$, so $A^{-1} = \operatorname{adj}(A)/\det A$ exactly when $\det A \ne 0$.
- $\det(\operatorname{adj}A) = (\det A)^{n-1}$ and $\operatorname{adj}(\operatorname{adj}A) = (\det A)^{n-2} A$ for $n \ge 2$.

**Rank, null space and systems** (detail in [matrix-rank](matrix-rank.md) and [system-of-linear-equations](system-of-linear-equations.md))
- Null space: $N(A) = \{x : Ax = \mathbf 0\}$. It always contains $\mathbf 0$.
- Rank-nullity: $\operatorname{rank}A + \operatorname{nullity}A = n$, the number of columns.
- $Ax = b$ is consistent if and only if $\operatorname{rank}A = \operatorname{rank}[A \mid b]$. It has a unique solution when that common rank is $n$.

**Eigenvalues**
- $\lambda$ is an eigenvalue if and only if $\det(A - \lambda I) = 0$. Eigenvectors are the non-zero solutions of $(A - \lambda I)v = \mathbf 0$.
- $\sum \lambda_i = \operatorname{tr}A$ and $\prod \lambda_i = \det A$, counting multiplicity.
- Triangular matrix: the eigenvalues are its diagonal entries.
- Cayley–Hamilton: every square matrix satisfies its own characteristic polynomial.
- Diagonalisable if and only if there are $n$ independent eigenvectors. Distinct eigenvalues are enough but not necessary.
- Algebraic multiplicity $\ge$ geometric multiplicity $\ge 1$.

**LU decomposition**
- $A = LU$ with $L$ unit lower triangular (Doolittle) and $U$ upper triangular. The multipliers of Gaussian elimination are the entries of $L$.
- It exists without row swaps when every leading principal minor is non-zero. Otherwise use $PA = LU$.
- Solve $Ax = b$ in two steps: $Ly = b$ forward, then $Ux = y$ backward.

**Projections and partitioned matrices (DA)**
- Orthogonal projection onto the column space of $A$ (full column rank): $P = A(A^TA)^{-1}A^T$. It is symmetric and idempotent.
- Onto a single vector $a$: $P = \dfrac{aa^T}{a^Ta}$, which has rank 1.
- Every idempotent matrix is a projection, but an *orthogonal* projection must also be symmetric.
- Block triangular: $\det\begin{pmatrix} A & B \\ 0 & D \end{pmatrix} = \det A \det D$.

**SVD (DA)**
- Every real $m \times n$ matrix factors as $A = U\Sigma V^T$, with $U$ and $V$ orthogonal and $\Sigma$ diagonal with entries $\sigma_1 \ge \sigma_2 \ge \dots \ge 0$.
- $\sigma_i = \sqrt{\lambda_i(A^TA)}$. The columns of $V$ are eigenvectors of $A^TA$, and the columns of $U$ are eigenvectors of $AA^T$.
- The rank of $A$ is the number of non-zero singular values.

## Formulas

| Matrix | Eigenvalues | Does not apply when |
|---|---|---|
| $kA$ | $k\lambda$ | — |
| $A + cI$ | $\lambda + c$ | the shift is by a non-scalar matrix |
| $A^m$ | $\lambda^m$ | — (eigenvectors stay the same) |
| $A^{-1}$ | $1/\lambda$ | $A$ is singular (some $\lambda = 0$) |
| $\operatorname{adj}A$ | $\det A / \lambda$ | some $\lambda = 0$ (use the rank of adj instead) |
| $A^T$ | same $\lambda$ | eigenvectors are generally different |
| $AB$ and $BA$ | same eigenvalues | — (both square) |

For a $2 \times 2$ matrix: $\lambda^2 - (\operatorname{tr}A)\lambda + \det A = 0$.

$\operatorname{rank}(\operatorname{adj}A) = n$ if $\operatorname{rank}A = n$, $1$ if $\operatorname{rank}A = n-1$, and $0$ otherwise.

$\operatorname{tr}(A+B) = \operatorname{tr}A + \operatorname{tr}B$ and $\operatorname{tr}(AB) = \operatorname{tr}(BA)$. But $\operatorname{tr}(ABC) \ne \operatorname{tr}(BAC)$ in general: only cyclic shifts are allowed.

## Worked examples

**1. Eigenvalues and eigenvectors.** $A = \begin{pmatrix} 4 & 1 \\ 2 & 3 \end{pmatrix}$.
- $\operatorname{tr}A = 7$ and $\det A = 12 - 2 = 10$, so $\lambda^2 - 7\lambda + 10 = 0$, giving $\lambda = 5$ or $\lambda = 2$.
- $\lambda = 5$: $A - 5I = \begin{pmatrix} -1 & 1 \\ 2 & -2 \end{pmatrix}$, so $v = (1, 1)$. Check: $A(1,1)^T = (5, 5)^T$.
- $\lambda = 2$: $A - 2I = \begin{pmatrix} 2 & 1 \\ 2 & 1 \end{pmatrix}$, so $v = (1, -2)$. Check: $A(1,-2)^T = (2, -4)^T$.
- Cross-check: $5 + 2 = 7 = \operatorname{tr}A$ and $5 \cdot 2 = 10 = \det A$.

**2. Doolittle LU.** $A = \begin{pmatrix} 2 & 3 \\ 4 & 7 \end{pmatrix}$.
- The multiplier is $l_{21} = 4/2 = 2$. Then $R_2 - 2R_1 = (0, 1)$.
- So $L = \begin{pmatrix} 1 & 0 \\ 2 & 1 \end{pmatrix}$ and $U = \begin{pmatrix} 2 & 3 \\ 0 & 1 \end{pmatrix}$.
- Check: $LU = \begin{pmatrix} 2 & 3 \\ 4 & 6 + 1 \end{pmatrix} = A$, and $\det A = 2 \cdot 1 = 2 = 14 - 12$.

**3. Projection onto a line.** $a = (1, 1)^T$.
- $P = \dfrac{aa^T}{a^Ta} = \dfrac12\begin{pmatrix} 1 & 1 \\ 1 & 1 \end{pmatrix}$.
- $P^2 = \dfrac14\begin{pmatrix} 2 & 2 \\ 2 & 2 \end{pmatrix} = P$. Its eigenvalues are $1$ and $0$, and $\operatorname{tr}P = 1 = \operatorname{rank}P$.

## Shortcuts

- Read off trace and determinant first: they give $\sum\lambda$ and $\prod\lambda$ without solving anything.
- If every row of $A$ sums to $s$, then $s$ is an eigenvalue with eigenvector $(1, \dots, 1)$.
- A rank-1 matrix $uv^T$ ($n \times n$) has eigenvalues $v^Tu$ (once) and $0$ ($n-1$ times).
- $\det A = 0$ if and only if $0$ is an eigenvalue, which happens if and only if $\operatorname{rank}A < n$.
- Cayley–Hamilton turns $A^{-1}$ or a high power $A^k$ into a short polynomial in $A$.
- Check an answer by plugging the eigenvector back in: $Av$ must equal $\lambda v$.

## Traps

- Eigenvalues of $A + B$ are **not** $\lambda_A + \lambda_B$, and eigenvalues of $AB$ are not $\lambda_A \lambda_B$, unless the matrices commute and share eigenvectors.
- Row operations change the eigenvalues. Never row-reduce before finding $\lambda$.
- $\det(A + B) \ne \det A + \det B$, and $\det(kA) = k^n \det A$, not $k \det A$.
- Orthogonal matrices have $\lvert\lambda\rvert = 1$, not $\lambda = \pm 1$. A rotation by $90^\circ$ has eigenvalues $\pm i$. (The LMN page states $\pm1$.)
- Eigenvectors of an orthogonal matrix are not automatically orthogonal to one another. That guarantee belongs to symmetric (more generally, normal) matrices with distinct eigenvalues. (The LMN page implies otherwise.)
- The null space always contains $\mathbf 0$. What is required to be non-zero is an eigenvector, not a null-space vector.
- Repeated eigenvalues do not by themselves rule out diagonalisation: $I$ is diagonal. Check the geometric multiplicity.
- LU without pivoting fails when a pivot is $0$, even for an invertible matrix such as $\begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix}$.

## Revision sheet

- subspace: contains 0, closed under + and scalar *
- > n vectors in R^n -> dependent; dim(U+W) = dimU + dimW - dim(U∩W)
- rank + nullity = n (columns); null space always contains 0
- Ax=b consistent <=> rank A = rank [A|b]; unique iff that rank = n
- det: swap flips sign, scale by k -> x k, add multiple -> unchanged
- det(kA) = k^n det A; det(adj A) = (det A)^(n-1)
- rank(adj A) = n, 1, 0 for rank A = n, n-1, <= n-2
- sum λ = trace, product λ = det
- triangular: λ = diagonal entries
- A^m -> λ^m; A^-1 -> 1/λ; A + cI -> λ + c; kA -> kλ; A^T -> same λ
- adj A -> det A / λ
- 2x2: λ^2 - (tr)λ + det = 0
- rank-1 uv^T: λ = v^T u, then zeros
- row sums all s -> λ = s
- symmetric: real λ, orthogonal eigenvectors (distinct λ), diagonalisable
- skew-symmetric: λ = 0 or pure imaginary; odd n -> det 0
- orthogonal: det ±1, |λ| = 1 (can be complex)
- idempotent: λ ∈ {0,1}, trace = rank
- nilpotent: all λ = 0, trace 0, det 0
- diagonalisable <=> n independent eigenvectors
- Cayley-Hamilton: A satisfies its characteristic polynomial
- LU (Doolittle): L unit lower = multipliers, U = echelon form
- LU needs non-zero leading principal minors, else PA = LU
- projection: P = A(A^T A)^-1 A^T, P^2 = P, P^T = P
- SVD: A = UΣV^T, σ = sqrt(eig(A^T A)), rank = # non-zero σ
- tr(AB) = tr(BA), only cyclic shifts allowed

## Connections

- Detailed pages: [matrix-rank](matrix-rank.md), [system-of-linear-equations](system-of-linear-equations.md) and [gaussian-elimination](gaussian-elimination.md).
- Graph theory: the eigenvalues of an adjacency matrix sum to $0$ for a graph without self-loops, because the trace is $0$ (GATE CS 2023).
- Machine learning (DA): PCA is the eigen-decomposition of the covariance matrix, which amounts to an SVD of the centred data. Least squares is the projection $P = A(A^TA)^{-1}A^T$.
- Algorithms: Gaussian elimination and LU take $O(n^3)$ time. Matrix-chain multiplication is a separate algorithms topic.

## Sources

- GeeksforGeeks, Linear Algebra (LMNs): <https://www.geeksforgeeks.org/lmns-linear-algebra/>. Corrections to the page are flagged in Traps.
- GATE 2027 CS syllabus: <https://gate2027.iitm.ac.in/static/doc/GATE2027_Syllabus/CS_GATE2027_Syllabus.pdf>
