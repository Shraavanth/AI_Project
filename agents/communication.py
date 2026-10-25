"""
Agent-to-agent messaging over the mesh network.

A message can only be delivered if the network graph has a path between the
sender and the receiver (one or more hops). Failed agents are not in the graph,
so they can neither send nor receive. Every delivered (or dropped) message is
recorded so it can be shown in the UI and stored in the database.

Heartbeats are implicit: being linked in the graph for a tick counts as having
heard the neighbour (see SimulationEngine._exchange_heartbeats).
"""

import itertools
from collections import deque
from datetime import datetime, timezone

MESSAGE_TYPES = [
    "INCIDENT_ALERT",
    "SENSOR_EVIDENCE",
    "CONSENSUS_UPDATE",
    "COORDINATOR_CHANGE",
    "TASK_PROPOSAL",
    "TASK_ACCEPTED",
    "TASK_DECLINED",
    "FAILURE_ALERT",
    "TASK_REASSIGNED",
    "RESPONSE_PROGRESS",
    "TASK_COMPLETED",
]


class CommunicationManager:

    def __init__(self, network):
        self.network = network
        self._counter = itertools.count(1)
        self.recent = deque(maxlen=600)   # newest first
        self.outbox = []                  # drained by the persistence layer
        self.delivered = 0
        self.dropped = 0

    def reset(self):
        self.recent.clear()
        self.outbox.clear()
        self.delivered = 0
        self.dropped = 0

    def send(self, tick: int, sender, receiver, msg_type: str, incident_id=None, payload=None):
        """
        Send one message. sender/receiver are Agent objects.
        Returns the message dict (with "delivered" True/False).
        """
        if msg_type not in MESSAGE_TYPES:
            raise ValueError(f"Unknown message type {msg_type}")

        hops = self.network.hops(sender.agent_id, receiver.agent_id)
        delivered = sender.operational and receiver.operational and hops is not None

        message = {
            "message_id": f"MSG-{next(self._counter):06d}",
            "tick": tick,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sender": sender.agent_id,
            "receiver": receiver.agent_id,
            "type": msg_type,
            "incident_id": incident_id,
            "payload": payload or {},
            "hops": hops,
            "delivered": delivered,
        }

        if sender.operational:
            sender.messages_sent += 1
            sender.last_comm_tick = tick
        if delivered:
            receiver.receive(message, tick)
            self.delivered += 1
        else:
            self.dropped += 1

        self.recent.appendleft(message)
        self.outbox.append(message)
        return message

    def broadcast_to_neighbors(self, tick, sender, agents_by_id, msg_type, incident_id=None, payload=None):
        """Send the same message to every direct (one-hop) neighbour."""
        sent = []
        for neighbor_id in list(sender.neighbors):
            receiver = agents_by_id.get(neighbor_id)
            if receiver is not None:
                sent.append(self.send(tick, sender, receiver, msg_type, incident_id, payload))
        return sent

    def drain_outbox(self):
        items, self.outbox = self.outbox, []
        return items
