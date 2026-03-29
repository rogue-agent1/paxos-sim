#!/usr/bin/env python3
"""Basic Paxos consensus simulation."""
import sys

class Proposal:
    def __init__(self, number, value): self.number, self.value = number, value

class Acceptor:
    def __init__(self, aid):
        self.id, self.promised, self.accepted = aid, -1, None
    def prepare(self, proposal_num):
        if proposal_num > self.promised:
            self.promised = proposal_num
            return (True, self.accepted)
        return (False, None)
    def accept(self, proposal):
        if proposal.number >= self.promised:
            self.promised = proposal.number; self.accepted = proposal
            return True
        return False

class Proposer:
    def __init__(self, pid, acceptors):
        self.id, self.acceptors, self.next_num = pid, acceptors, pid
    def propose(self, value):
        n = self.next_num; self.next_num += len(self.acceptors) + 1
        # Phase 1: Prepare
        promises = []
        for a in self.acceptors:
            ok, prev = a.prepare(n)
            if ok: promises.append((a, prev))
        if len(promises) <= len(self.acceptors) // 2: return None
        # Use highest accepted value if any
        prev_accepted = [p for _, p in promises if p is not None]
        if prev_accepted:
            value = max(prev_accepted, key=lambda p: p.number).value
        # Phase 2: Accept
        proposal = Proposal(n, value); accepts = 0
        for a, _ in promises:
            if a.accept(proposal): accepts += 1
        if accepts > len(self.acceptors) // 2: return proposal
        return None

def main():
    if len(sys.argv) < 2: print("Usage: paxos_sim.py <demo|test>"); return
    if sys.argv[1] == "test":
        acceptors = [Acceptor(i) for i in range(5)]
        p1 = Proposer(0, acceptors)
        result = p1.propose("value_A")
        assert result is not None; assert result.value == "value_A"
        # All acceptors should have accepted
        assert all(a.accepted is not None for a in acceptors)
        # Second proposer with higher number should still work
        p2 = Proposer(1, acceptors)
        result2 = p2.propose("value_B")
        assert result2 is not None
        # Should pick up previously accepted value
        assert result2.value == "value_A"  # Paxos preserves first accepted
        print("All tests passed!")
    else:
        acceptors = [Acceptor(i) for i in range(3)]
        p = Proposer(0, acceptors)
        r = p.propose("hello"); print(f"Consensus: {r.value if r else 'FAILED'}")

if __name__ == "__main__": main()
