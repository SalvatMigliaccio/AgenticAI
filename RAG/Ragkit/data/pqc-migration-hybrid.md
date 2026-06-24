# Post-quantum migration

Migration strategies often rely on hybrid schemes that combine a classical
algorithm such as ECDH with a post-quantum key encapsulation mechanism. Hybrid
deployment keeps confidentiality intact even if one primitive is later broken.

Migration also requires crypto-agility: the ability to inventory and replace
algorithms without redesigning the system.
