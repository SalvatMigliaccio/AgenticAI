# The quantum threat

Shor's algorithm, running on a fault-tolerant quantum computer, would break RSA
and elliptic curve cryptography by efficiently solving integer factorization and
the discrete logarithm problem. This is the primary motivation for migrating to
quantum-resistant algorithms before such machines exist.

Grover's algorithm offers only a quadratic speedup against symmetric primitives,
which is mitigated by doubling key lengths.
