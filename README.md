# Kubernetes Sample Applications

## Redis Queue HPA

Use a Kubernetes custom metric to enable the Kubernetes Horizontal Pod Autoscaler (HPA) to scale based on redis queue length plus busy worker count. See [`redis-queue-hpa`](/redis-queue-hpa/).

## Simple webserver

Implement a simple static webserver. See [`webserver`](/webserver/).

## Simple secret server

Implement a simple secret server, which takes secrets from `values-secret.yaml` and mounts them in the secretserver container. See [`secretserver`](/secretserver/).
