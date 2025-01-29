# A Kubernetes Database app

This is a simple Kubernetes database app that saves and retrieves data to a persistent MySQL database, using:

* two Deployments:
  * the API server, using gunicorn, flask, sqlalchemy
  * a MySQL instance
* two Services:
  * a NodePort, with the following ports:
    * 80 - `targetPort`, accessible from inside the apiserver docker container
    * 8880 - `port`, accessible from across cluster on the ClusterIP
    * 30880 - `nodePort`, accessible from outside the cluster
  * a ClusterIP, so the API server can talk to the database
    * 3306 - `targetPort`, accessible from inside the MySQL docker container
    * 3306 - `port`, accessible from across cluster on the ClusterIP
* a Persistent Volume Claim
* a Persistent Volume, pointing to `/mnt/data` on the minikube VM

# Installing with helm

Get a minikube VM started, then:

```shell
# Point your shell to minikube's docker-daemon:
eval $(minikube docker-env)

# Build the apiserver container:
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
