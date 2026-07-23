# Attempted Commands

## Build OpenPLC Runtime Image

```bash
cd /home/kingy/projects/sphere/cps-enclave-model/docker/openplc
sudo bash ./build.sh master
```

Observed result: image build completed as `ghcr.io/sphere-project/sphere-openplc:master` / local `sphere-openplc:master` after Docker Hub TLS/certificate access was corrected.

## Start Controller Container

```bash
sudo docker run -d   --name wd-openplc-controller   -p 502:502   -p 8081:8080   -e OPENPLC_PROGRAM=/programs/wd_controller.st   -v /home/kingy/projects/sphere/sphere-usecases/water-distribution/implementations/openplc/st/wd_controller.st:/programs/wd_controller.st:ro   sphere-openplc:master
```

## Start Simulator Container

```bash
sudo docker run -d   --name wd-openplc-simulator   -p 503:502   -p 8082:8080   -e OPENPLC_PROGRAM=/programs/wd_simulator.st   -v /home/kingy/projects/sphere/sphere-usecases/water-distribution/implementations/openplc/st/wd_simulator.st:/programs/wd_simulator.st:ro   sphere-openplc:master
```

## Check Runtime

```bash
sudo docker ps
sudo docker logs wd-openplc-controller --tail 80
sudo docker logs wd-openplc-simulator --tail 80
```

Observed result: `docker ps` did not show running WD OpenPLC containers; logs showed OpenPLC compilation failures for both mounted ST programs.

## Harness Commands Intended After Runtime Startup

```bash
cd /home/kingy/projects/sphere/sphere-usecases/water-distribution/implementations/openplc
source .venv/bin/activate

python scripts/validation_harness.py   --scenario scenarios/idle.yaml   --output ../../runs/validate-idle   --controller localhost:502   --simulator localhost:503

python scripts/validation_harness.py   --scenario scenarios/nominal_startup.yaml   --output ../../runs/validate-nominal-startup   --controller localhost:502   --simulator localhost:503
```

Observed result: harness execution could not complete because the OpenPLC endpoints were unavailable after container exit.
