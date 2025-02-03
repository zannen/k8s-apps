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

helm install atestapp . -n YOUR_NAMESPACE_HERE --create-namespace
```

# Adding some data

```shell
curl -XPOST -H 'Content-type: application/json' --data '{"info":"TEST_DATA"}' "http://$(minikube ip):30880/data"
```
```json
{"error":null,"id":1,"info":"TEST_DATA"}
```

# Getting some data

```shell
curl "http://$(minikube ip):30880/data/1"  # "1" is the ID from above
```
```json
{"error":null,"id":1,"info":"TEST_DATA"}
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

# Delete the MySQL database files:
minikube ssh
sudo rm -rf /mnt/data  # from hostPath of mysql-pv-volume.
```
