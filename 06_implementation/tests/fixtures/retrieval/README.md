# Independently calculated retrieval fixtures

These invented four-document examples verify arithmetic and API behavior. They
are not incident pilot rankings, E5 output, human judgments, or quality evidence.
Expected values were derived from the equations below before executing the
retrieval implementation. No production retrieval function generated them.

## BM25

Use natural logarithms, `k1 = 1.2`, `b = 0.75`, and unique query terms.
Document lengths are `3, 3, 2, 2`, so average length is `2.5`.
The query terms `alpha` and `beta` each occur in two of the four documents:

`idf = ln(1 + (4 - 2 + 0.5)/(2 + 0.5)) = ln(2)`.

For length 3, the length penalty is `1.2*(0.25 + 0.75*3/2.5) = 1.38`.
For length 2, it is `1.02`. The scores follow directly:

| Document | Calculation | Expected score |
|---|---|---:|
| A | `ln(2) * (4.4/3.38 + 2.2/2.38)` | 1.5430460580611978 |
| C | `ln(2) * 2.2/2.02` | 0.754912770906871 |
| B | `ln(2) * 2.2/2.38` | 0.6407242845512099 |
| D | no query term overlap | absent |

The required order is A, C, B. Floating point comparison uses absolute tolerance
`1e-12`. Tests also check explicit technical tokens, repeated query terms,
lexical ties, empty inputs, positive custom parameters, and invalid arguments.

## Reciprocal rank fusion

The two lists are `(A, B, C)` and `(D, B, A)`. Each weight is 1 and the constant
is 60. A candidate missing from a list contributes zero for that list.

| Candidate | Calculation | Expected score |
|---|---|---:|
| A | `1/61 + 1/63` | 0.032266458495966696 |
| B | `1/62 + 1/62` | 0.03225806451612903 |
| D | `1/61` | 0.01639344262295082 |
| C | `1/63` | 0.015873015873015872 |

The required order is A, B, D, C. The lexical and dense-like input score scales
are deliberately different; changing those raw scores must not affect fusion.
Absolute tolerance is `1e-14`. Weighted expectations are calculated directly
as `2/(60 + rank_1) + 1/(60 + rank_2)` in the test.

## Exact cosine fixture

Vectors are invented two-dimensional unit vectors. Against query `(1, 0)`,
vectors `(1, 0)`, `(0.6, 0.8)`, `(0, 1)`, and `(-1, 0)` have exact cosines
`1`, `0.6`, `0`, and `-1`. They are not generated E5 embeddings. Tolerance is
`1e-6` to permit a float32 search matrix. Additional cases check ties,
non-finite values, zero vectors, dimensions, duplicate IDs, and short rankings.
