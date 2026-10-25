from dataclasses import dataclass
from fractions import Fraction


Q = (2, 3, 5, 7)


@dataclass(frozen=True)
class Variant:
    s: int
    k: int
    M: int
    L: int
    d: int
    q: int
    eps: Fraction

    @classmethod
    def from_s(cls, s: int) -> "Variant":
        s3 = s % 3
        eps = Fraction(1, 10 ** (2 + s3))
        return cls(s=s, k=5 - s3, M=2 + s3, L=3 + s % 5, d=1 + s3, q=Q[s % 4], eps=eps)
