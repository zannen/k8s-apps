# Redis queue monitor and worker

This docker image acts as:

- a REST custom metrics API server
- a REST API server, for monitoring and enqueing jobs
- a redis queue worker, processing jobs from a queue
