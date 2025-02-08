# A Kubernetes Webserver

This app is a simple Kubernetes webserver, using:

* one Deployment, containing one ReplicaSet, containing one Pod, containing one nginx webserver, containing one static webpage
* one Service of type NodePort, with the following ports:
  * 80 - `targetPort`, accessible from inside the webserver docker container
  * 8880 - `port`, accessible from across cluster on the ClusterIP
  * 30880 - `nodePort`, accessible from outside the cluster

# Installing with helm

Get a minikube VM started, then:

```shell
# Point your shell to minikube's docker-daemon
eval $(minikube docker-env)

# Build the webserver container
make docker

# Install the app
helm install atestapp . -n YOUR_NAMESPACE_HERE --create-namespace -f values.yaml
```

# Getting pages on the webserver

## when outside minikube

```shell
curl "http://$(minikube ip):30880/" # use "nodePort"
```

## when logged in to the minikube VM

```shell
# Get the ClusterIP
kubectl get services -n YOUR_NAMESPACE_HERE -o json | jq -r '.items[0].spec.clusterIP'

# Log in to the VM
minikube ssh

# Get the webpage, using the ClusterIP from above
curl http://10.XX.YY.ZZ:8880/ # use "port"
```

## when in the webserver container

```shell
# Log in to the VM
minikube ssh

# Get the webserver container name
ws="$(docker ps --format '{{.Names}}' | grep k8s_awebserver)"
docker exec "$ws" curl -s http://localhost:80/ # use "containerPort"
```

# Upgrading with helm

Remember to bump `webserverVersion` in `values.yaml` and the chart version in `Chart.yaml`, then:

```shell
helm upgrade atestapp . -n YOUR_NAMESPACE_HERE -f values.yaml
```

# Uninstalling with helm

```shell
helm uninstall -n YOUR_NAMESPACE_HERE atestapp
kubectl delete namespace YOUR_NAMESPACE_HERE
```
