# SPHERE Modbus Bridge Container
#
# Generic bridge that selects behavior based on USECASE environment variable.
# Supports: wt (Water Treatment), wd (Water Distribution), ps (Power Hydro)

FROM python:3.11-slim

WORKDIR /app

# Install pymodbus
RUN pip install --no-cache-dir pymodbus==3.6.9

# Copy bridge script
COPY bridge.py /app/bridge.py

# Default environment
ENV CONTROLLER_ADDR="controller:502"
ENV SIMULATOR_ADDR="simulator:502"
ENV USECASE="wt"
ENV CYCLE_MS="100"

CMD ["python", "-u", "/app/bridge.py"]
