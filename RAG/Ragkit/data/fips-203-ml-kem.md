# ML-KEM (FIPS 203)

ML-KEM, standardized as FIPS 203, is a key encapsulation mechanism based on the
hardness of the module learning with errors problem. It is derived from
CRYSTALS-Kyber and establishes shared secret keys that resist attacks by
large-scale quantum computers.

A sender encapsulates against a public key, producing a ciphertext and a shared
secret; the holder of the private key decapsulates to recover the same secret.
ML-KEM is the primary NIST recommendation for post-quantum key establishment.
