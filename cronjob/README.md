# A Kubernetes CronJob

This app is a simple Kubernetes webserver with a CronJob, using:

* one nginx webserver with one page that is updated by the CronJob
* one CronJob, which updates the webserver's one webpage
* one Deployment, with one ReplicaSet, with one Pod
* one Service of type NodePort, with the following ports:
  * 80 - `targetPort`, accessible from inside the webserver docker container
  * 8880 - `port`, accessible from across cluster on the ClusterIP
  * 30880 - `nodePort`, accessible from outside the cluster

# Installing with helm

Get a minikube VM started, then:

```shell
# Point your shell to minikube's docker-daemon:
eval $(minikube docker-env)

# Build the containers:
make docker

helm install atestapp . -n YOUR_NAMESPACE_HERE --create-namespace -f values.yaml
```

# Getting the webserver page

```shell
curl "http://$(minikube ip):30880/"
```

You may see:
* A generic message: no CronJob has been run (yet)
* A timestamped message: the CronJob has been run at the specified time

# Deleting completed CronJob pods

```shell
kubectl delete pod --field-selector=status.phase==Succeeded -n YOUR_NAMESPACE_HERE
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
