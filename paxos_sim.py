#!/usr/bin/env python3
"""paxos_sim - Single-decree Paxos consensus simulation."""
import sys

class Proposer:
    def __init__(self, node_id):
        self.id = node_id
        self.proposal_num = 0
        self.value = None
    
    def prepare(self):
        self.proposal_num += 1
        return {"type": "prepare", "n": (self.proposal_num, self.id)}
    
    def propose(self, promises, value):
        # Find highest-numbered accepted value from promises
        accepted = [(p["accepted_n"], p["accepted_v"]) for p in promises
                    if p["promise"] and p.get("accepted_v") is not None]
        if accepted:
            _, self.value = max(accepted)
        else:
            self.value = value
        return {"type": "accept", "n": (self.proposal_num, self.id), "v": self.value}

class Acceptor:
    def __init__(self, node_id):
        self.id = node_id
        self.promised_n = (0, -1)
        self.accepted_n = (0, -1)
        self.accepted_v = None
    
    def handle_prepare(self, msg):
        if msg["n"] > self.promised_n:
            self.promised_n = msg["n"]
            return {"promise": True, "acceptor": self.id,
                    "accepted_n": self.accepted_n, "accepted_v": self.accepted_v}
        return {"promise": False, "acceptor": self.id}
    
    def handle_accept(self, msg):
        if msg["n"] >= self.promised_n:
            self.promised_n = msg["n"]
            self.accepted_n = msg["n"]
            self.accepted_v = msg["v"]
            return {"accepted": True, "acceptor": self.id, "n": msg["n"], "v": msg["v"]}
        return {"accepted": False, "acceptor": self.id}

class Learner:
    def __init__(self):
        self.accepted = {}  # proposal_n -> {acceptor_id: value}
        self.chosen = None
    
    def handle_accepted(self, msg, quorum_size):
        n = msg["n"]
        if n not in self.accepted:
            self.accepted[n] = {}
        self.accepted[n][msg["acceptor"]] = msg["v"]
        if len(self.accepted[n]) >= quorum_size:
            self.chosen = msg["v"]
        return self.chosen

def run_paxos(proposers, acceptors, learner, value):
    quorum = len(acceptors) // 2 + 1
    
    # Phase 1: Prepare
    prep = proposers[0].prepare()
    promises = [a.handle_prepare(prep) for a in acceptors]
    granted = [p for p in promises if p["promise"]]
    
    if len(granted) < quorum:
        return None
    
    # Phase 2: Accept
    accept = proposers[0].propose(granted, value)
    responses = [a.handle_accept(accept) for a in acceptors]
    
    for r in responses:
        if r["accepted"]:
            result = learner.handle_accepted(r, quorum)
            if result is not None:
                return result
    return None

def test():
    # Basic consensus
    proposers = [Proposer(0)]
    acceptors = [Acceptor(i) for i in range(3)]
    learner = Learner()
    
    result = run_paxos(proposers, acceptors, learner, "hello")
    assert result == "hello"
    assert learner.chosen == "hello"
    
    # Competing proposers
    p1 = Proposer(0)
    p2 = Proposer(1)
    acceptors2 = [Acceptor(i) for i in range(5)]
    learner2 = Learner()
    
    # P1 prepares first
    prep1 = p1.prepare()
    promises1 = [a.handle_prepare(prep1) for a in acceptors2]
    
    # P2 prepares with higher number
    prep2 = p2.prepare()
    promises2 = [a.handle_prepare(prep2) for a in acceptors2]
    
    # P1's accept should be rejected (promises broken)
    accept1 = p1.propose([p for p in promises1 if p["promise"]], "A")
    responses1 = [a.handle_accept(accept1) for a in acceptors2]
    accepted1 = sum(1 for r in responses1 if r["accepted"])
    
    # P2's accept should succeed
    accept2 = p2.propose([p for p in promises2 if p["promise"]], "B")
    responses2 = [a.handle_accept(accept2) for a in acceptors2]
    accepted2 = sum(1 for r in responses2 if r["accepted"])
    
    assert accepted2 >= 3  # Majority
    
    for r in responses2:
        if r["accepted"]:
            learner2.handle_accepted(r, 3)
    assert learner2.chosen == "B"
    
    print("All tests passed!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test()
    else:
        print("Usage: paxos_sim.py test")
