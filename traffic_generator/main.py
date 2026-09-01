import httpx
import time
import random

SERVICES = ["auth-service", "payments-service", "api-gateway"]
BASE_URL = "http://localhost:8000"


class ServiceState:
    def __init__(self, name):
        self.name = name
        self.incident = False

    def maybe_toggle_incident(self):
        if self.incident:
            if random.random() < 0.05:
                self.incident = False
        else:
            if random.random() < 0.01:
                self.incident = True

    def emit(self):
        self.maybe_toggle_incident()

        if self.incident:
            level = random.choices(["warn", "error"], weights=[0.4, 0.6])[0]
            latency = max(1, random.gauss(400, 100))
            error_rate = random.uniform(0.1, 0.4)
        else:
            level = random.choices(["info", "warn"], weights=[0.9, 0.1])[0]
            latency = max(1, random.gauss(50, 10))
            error_rate = random.uniform(0.0, 0.02)

        return level, latency, error_rate

    def sleep_interval(self):
        return random.uniform(0.1, 0.3) if self.incident else random.uniform(1.0, 3.0)


def run():
    client = httpx.Client()
    states = {name: ServiceState(name) for name in SERVICES}

    while True:
        for name, state in states.items():
            level, latency, error_rate = state.emit()

            client.post(f"{BASE_URL}/logs", json={
                "service": name,
                "level": level,
                "message": f"{level} event from {name}",
            })
            client.post(f"{BASE_URL}/metrics", json={
                "service": name,
                "metric_name": "request_latency_ms",
                "value": latency,
            })
            client.post(f"{BASE_URL}/metrics", json={
                "service": name,
                "metric_name": "error_rate",
                "value": error_rate,
            })

            time.sleep(state.sleep_interval())


if __name__ == "__main__":
    run()