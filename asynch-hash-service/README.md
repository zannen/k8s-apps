# A Kubernetes asynchronous hash app

This is a Kubernetes app that handles job requests for calculating hashes, using:

* TBD

# Installing with helm

Get a minikube VM started, then:

```shell
# Point your shell to minikube's docker-daemon:
eval $(minikube docker-env)

# Build containers:
make docker

helm install atestapp . -n YOUR_NAMESPACE_HERE --create-namespace -f values.yaml -f vaues-custom-secret.yaml
```

************************TBD

# Upgrading with helm

Remember to bump the chart version in `Chart.yaml`, then:

```shell
helm upgrade atestapp . -n YOUR_NAMESPACE_HERE -f values.yaml -f vaues-custom-secret.yaml
```

# Uninstalling with helm

```shell
helm uninstall -n YOUR_NAMESPACE_HERE atestapp
kubectl delete namespace YOUR_NAMESPACE_HERE

# Delete the MySQL database files:
minikube ssh
sudo rm -rf /mnt/data  # from hostPath of mysql-pv-volume.
```

# Running Python app tests

```shell
cd docker/apiserver

# Run all static analysis (flake8, black, isort, mypy, pylint. Then run pytest
../../../.python-app-tests.sh apiserver
```

