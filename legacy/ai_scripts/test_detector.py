from anomaly_detector import predict_environment


# Test 1: Normal environment
normal = predict_environment(
    temperature=28,
    humidity=60,
    smoke=0.10,
    co2=420,
    air_quality=50,
    soil_moisture=55
)

print("Normal environment:")
print(normal)


# Test 2: Fire-like environment
fire = predict_environment(
    temperature=45,
    humidity=15,
    smoke=0.90,
    co2=950,
    air_quality=80,
    soil_moisture=20
)

print("\nFire-like environment:")
print(fire)


# Test 3: Pollution-like environment
pollution = predict_environment(
    temperature=31,
    humidity=40,
    smoke=0.60,
    co2=1200,
    air_quality=180,
    soil_moisture=50
)

print("\nPollution-like environment:")
print(pollution)