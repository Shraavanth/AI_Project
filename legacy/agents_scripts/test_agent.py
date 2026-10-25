from monitoring_agent import MonitoringAgent


# Create a normal environmental agent
normal_agent = MonitoringAgent(
    agent_id="A1",
    x=2,
    y=3,
    temperature=28,
    humidity=60,
    smoke=0.10,
    co2=420,
    air_quality=50,
    soil_moisture=55
)

print("=" * 60)
print("NORMAL ENVIRONMENT TEST")
print("=" * 60)

result = normal_agent.analyze_environment()

print("Agent ID:", normal_agent.agent_id)
print("Readings:", normal_agent.get_readings())
print("AI Result:", result)


# Create a fire-like environmental agent
fire_agent = MonitoringAgent(
    agent_id="A2",
    x=5,
    y=6,
    temperature=45,
    humidity=15,
    smoke=0.90,
    co2=950,
    air_quality=80,
    soil_moisture=20
)

print("\n" + "=" * 60)
print("FIRE-LIKE ENVIRONMENT TEST")
print("=" * 60)

result = fire_agent.analyze_environment()

print("Agent ID:", fire_agent.agent_id)
print("Readings:", fire_agent.get_readings())
print("AI Result:", result)