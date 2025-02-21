# Kubernetes Sample Applications

This repo contains various sample Kubernetes applications, in increasing order of complexity.

## Simple webserver

Implement a simple static webserver. See [`webserver`](/webserver/).

## Simple secret server

Implement a simple secret server, which takes secrets from `values-secret.yaml` and mounts them in the secretserver container. See [`secretserver`](/secretserver/).

## Database server

Implement a database server with persistent storage. See [`database`](/database/).

## A webserver with a CronJob

Implement a webserver with a CronJob that updates a webpage. See [`cronjob`](/cronjob/).

## Redis Queue HPA

Use a Kubernetes custom metric to enable the Kubernetes Horizontal Pod Autoscaler (HPA) to scale based on redis queue length plus busy worker count. See [`redis-queue-hpa`](/redis-queue-hpa/).

## Asynchronous Hash App

Implement an app that calculates hashes asynchronously. See [`asynch-hash-service`](/asynch-hash-service/).
