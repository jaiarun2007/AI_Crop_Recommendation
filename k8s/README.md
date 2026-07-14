# Kubernetes Deployment

Manifests for the single containerized FastAPI app (see `../Dockerfile`) — matches the
existing single-service architecture of this repo, not the full ~10-microservice split
described in the Executive Summary's long-term vision.

## Files

| File | Purpose |
|---|---|
| `namespace.yaml` | `ai-crop-recommendation` namespace |
| `configmap.yaml` | Non-secret env vars (DB URL, token TTL) |
| `secret.example.yaml` | Template for `JWT_SECRET_KEY` / `ANTHROPIC_API_KEY` — copy to `secret.yaml` (gitignored), fill in real values |
| `pvc.yaml` | Persistent volume for the SQLite database file |
| `deployment.yaml` | The app deployment (1 replica — see caveat below) |
| `service.yaml` | ClusterIP service, port 80 → 8000 |
| `ingress.yaml` | Nginx ingress + TLS (replace the placeholder domain) |
| `hpa.yaml` | Horizontal Pod Autoscaler (defined but only meaningfully useful once SQLite is replaced — see below) |

## Important: SQLite and replica count

The default `DATABASE_URL` is a SQLite file on a `ReadWriteOnce` PVC. That only works
correctly with **exactly one pod replica** — multiple pods writing to the same SQLite file
concurrently can corrupt it. `deployment.yaml` is set to `replicas: 1` for this reason, and the
HPA's `maxReplicas: 3` will not actually be safe to reach until `DATABASE_URL` is switched to a
real multi-writer database (e.g. managed PostgreSQL, as the Executive Summary recommends for
production). This wasn't glossed over — it's the honest state of a demo-scoped deployment, and
the fix (swap the DB) is a `DATABASE_URL` env var change, not a code change.

## Applying

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
cp k8s/secret.example.yaml k8s/secret.yaml   # edit with real values first
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml   # edit the placeholder domain first
kubectl apply -f k8s/hpa.yaml
```

Build and push the image first (`docker build -t <your-registry>/ai-crop-recommendation:latest .`
then update `image:` in `deployment.yaml`), or point your cluster at a local image if using
kind/minikube.

## What was and wasn't verified

All YAML files parse correctly (validated with PyYAML) and follow standard Deployment/Service/
Ingress/HPA/PVC shapes. **They were not applied to a live cluster** — this was built in a sandbox
with no Kubernetes cluster available. Similarly, `docker build` could not be completed end-to-end
in this sandbox: the sandbox's network policy blocks pulling the `python:3.11-slim` base image
from Docker Hub (the same class of restriction that blocks the weather API — see the main
README's network-access notes). The `Dockerfile` and `docker-compose.yml` are written to a
standard, defensible pattern (multi-layer build, requirements cached separately from source,
non-root-friendly `WORKDIR`, healthcheck), but **do a real `docker compose up --build` and
`kubectl apply --dry-run=client -f k8s/` in an environment with normal registry/cluster access
before relying on this for the actual deployment.**
