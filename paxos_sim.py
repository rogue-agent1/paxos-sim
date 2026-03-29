#!/usr/bin/env python3
"""Simplified Paxos consensus protocol simulation."""
import sys

class Proposer:
    def __init__(self, pid):
        self.pid = pid
        self.proposal_num = 0
    def prepare(self):
        self.proposal_num += 1
        return (self.proposal_num, self.pid)
    def propose(self, value):
        return (self.proposal_num, self.pid), value

class Acceptor:
    def __init__(self, aid):
        self.aid = aid
        self.promised = None
        self.accepted = None
        self.accepted_value = None
    def on_prepare(self, proposal_num):
        if self.promised is None or proposal_num > self.promised:
            self.promised = proposal_num
            return True, self.accepted, self.accepted_value
        return False, None, None
    def on_accept(self, proposal_num, value):
        if self.promised is None or proposal_num >= self.promised:
            self.promised = proposal_num
            self.accepted = proposal_num
            self.accepted_value = value
            return True
        return False

def run_paxos(proposer, acceptors, value):
    prop_num = proposer.prepare()
    promises = []
    for a in acceptors:
        ok, prev_num, prev_val = a.on_prepare(prop_num)
        if ok:
            promises.append((prev_num, prev_val))
    if len(promises) <= len(acceptors) // 2:
        return None
    prev = [(n, v) for n, v in promises if n is not None]
    if prev:
        value = max(prev, key=lambda x: x[0])[1]
    prop_num, val = proposer.propose(value)
    accepts = sum(1 for a in acceptors if a.on_accept(prop_num, val))
    if accepts > len(acceptors) // 2:
        return val
    return None

def test():
    p = Proposer(1)
    acceptors = [Acceptor(i) for i in range(5)]
    result = run_paxos(p, acceptors, "hello")
    assert result == "hello"
    assert all(a.accepted_value == "hello" for a in acceptors)
    p2 = Proposer(2)
    result2 = run_paxos(p2, acceptors, "world")
    assert result2 == "hello"  # must accept previously accepted value
    print("  paxos_sim: ALL TESTS PASSED")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test": test()
    else: print("Paxos consensus simulation")
