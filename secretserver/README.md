# A Kubernetes Secret server

This app is a simple Kubernetes server that serves secrets, using:

* one Deployment, containing one ReplicaSet, containing one Pod, containing one gunicorn server
* one Service of type NodePort, available on port 30880 from outside the cluster

Secrets are taken from `values-secret.yaml` and mounted them in the secretserver container as either files or environmental variables.

# Installing with helm

Get a minikube VM started, then:

```shell
# Point your shell to minikube's docker-daemon:
eval $(minikube docker-env)

# Ensure you have a secrets file.
cp -a values-secret-SAMPLE.yaml values-secret.yaml

# Build the secretserver container:
make docker

# Install the app
helm install atestapp . -n YOUR_NAMESPACE_HERE --create-namespace -f values.yaml -f values-secret.yaml
```

# Getting secrets

```shell
curl "http://$(minikube ip):30880/secrets/superSecretPassword1"
```

# Upgrading with helm

Remember to bump the chart version in `Chart.yaml`, then:

```shell
helm upgrade atestapp . -n YOUR_NAMESPACE_HERE
```

# Uninstalling with helm

```shell
helm uninstall -n YOUR_NAMESPACE_HERE atestapp
kubectl delete namespace YOUR_NAMESPACE_HERE
```

# Running Python app tests

```shell
cd docker/secretserver

# Run all static analysis (flake8, black, isort, mypy, pylint. Then run pytest
../../../.python-app-tests.sh secretserver
```
