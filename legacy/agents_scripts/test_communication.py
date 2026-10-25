from monitoring_agent import MonitoringAgent


# Agent A1 - normal
a1 = MonitoringAgent(
    agent_id="A1",
    x=1,
    y=1,
    temperature=28,
    humidity=60,
    smoke=0.10,
    co2=420,
    air_quality=50,
    soil_moisture=55
)


# Agent A2 - fire-like condition
a2 = MonitoringAgent(
    agent_id="A2",
    x=2,
    y=1,
    temperature=45,
    humidity=15,
    smoke=0.90,
    co2=950,
    air_quality=80,
    soil_moisture=20
)


# Agent A3 - normal
a3 = MonitoringAgent(
    agent_id="A3",
    x=3,
    y=1,
    temperature=29,
    humidity=58,
    smoke=0.12,
    co2=430,
    air_quality=52,
    soil_moisture=50
)


# Create communication links
a1.add_neighbor(a2)
a2.add_neighbor(a1)

a2.add_neighbor(a3)
a3.add_neighbor(a2)


print("=" * 60)
print("NETWORK")
print("=" * 60)

print("A1 neighbors:", [a.agent_id for a in a1.neighbors])
print("A2 neighbors:", [a.agent_id for a in a2.neighbors])
print("A3 neighbors:", [a.agent_id for a in a3.neighbors])


print("\n" + "=" * 60)
print("ENVIRONMENT ANALYSIS")
print("=" * 60)

print("A1:", a1.analyze_environment())
print("A2:", a2.analyze_environment())
print("A3:", a3.analyze_environment())


print("\n" + "=" * 60)
print("ALERT BROADCAST")
print("=" * 60)

a2.broadcast_alert()


print("\n" + "=" * 60)
print("MESSAGES RECEIVED")
print("=" * 60)

print("A1 messages:", a1.messages)
print("A2 messages:", a2.messages)
print("A3 messages:", a3.messages)