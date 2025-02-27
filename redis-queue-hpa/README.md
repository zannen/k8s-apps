# Kubernetes Redis Queue HPA

This app demonstrates using a Kubernetes custom metric to enable the Kubernetes Horizontal Pod Autoscaler (HPA) to scale based on redis queue (rq) length plus busy worker count.

**NOTE**: If you want to scale on CPU and/or memory, there's no need for this repo or all this complexity. Use the [Metrics Server](https://github.com/kubernetes-sigs/metrics-server#use-cases) instead.

# Generating secrets

```shell
./generate_certificates.sh YOUR_NAMESPACE_HERE
```

Then copy the last part of the output (after `--- 8< ---`) into `values-custom-secret.yaml`.

# Installing with helm

```shell
# Point your shell to minikube's docker-daemon:
eval $(minikube docker-env)

# Build the custom docker containers used for:
# - metrics exporter API server
# - API server and rq worker
make docker

helm install suihei . -n YOUR_NAMESPACE_HERE --create-namespace -f values.yaml -f values-custom.yaml -f values-custom-secret.yaml
```

# Upgrading with helm

Remember to bump the chart version in `Chart.yaml`, then:

```shell
helm upgrade atestapp . -n YOUR_NAMESPACE_HERE -f values.yaml -f values-custom.yaml -f values-custom-secret.yaml
```

# Uninstalling with helm

```shell
helm uninstall -n YOUR_NAMESPACE_HERE suihei
kubectl delete namespace YOUR_NAMESPACE_HERE
```

# Kubernetes custom metrics

- List all metric definitions:

  ```shell
  kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1/" | jq .
  ```

  Sample output:
  ```json
  {
    "kind": "APIResourceList",
    "apiVersion": "v1",
    "groupVersion": "custom.metrics.k8s.io/v1beta1",
    "resources": [
      {
        "name": "deployments.apps/redisqueue_length",
        "singularName": "",
        "namespaced": true,
        "kind": "MetricValueList",
        "verbs": ["get"]
      }
    ]
  }
  ```
- Get metric values for one metric

  ```shell
  namespace=YOUR_NAMESPACE_HERE
  kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1/namespaces/$namespace/deployments.apps/rq-worker/redisqueue_length?metricLabelSelector=queues%3Dhigh-low" | jq .
  ```

  Sample output (see also `MetricValueList` [Golang struct](https://github.com/kubernetes/metrics/blob/342ad4a5669e323882f585879b7c9d4174ab9bcc/pkg/apis/custom_metrics/v1beta2/types.go#L39-L46) and [protobuf message](https://github.com/kubernetes/metrics/blob/342ad4a5669e323882f585879b7c9d4174ab9bcc/pkg/apis/custom_metrics/v1beta2/generated.proto#L78-L84)):
  ```json
  {
    "apiVersion": "custom.metrics.k8s.io/v1beta1",
    "items": [
      {
        "_debug": {
          "all_busy_workers": [
            "26db71be1f254f99b718a2cfa2219145",
            "8ba55f15a5a344968ca35bbdb0a44461"
          ],
          "queue_info": {
            "high": {
              "busy_workers": [
                "8ba55f15a5a344968ca35bbdb0a44461"
              ],
              "queued_job_count": 6
            },
            "low": {
              "busy_workers": [
                "26db71be1f254f99b718a2cfa2219145"
              ],
              "queued_job_count": 1
            }
          }
        },
        "describedObject": {
          "apiVersion": "apps/v1",
          "kind": "Deployment",
          "name": "rq-worker",
          "namespace": "YOUR_NAMESPACE_HERE"
        },
        "metricName": "count",
        "timestamp": "2022-02-04T11:55:41Z",
        "value": "9"
      }
    ],
    "kind": "MetricValueList",
    "metadata": {
      "selflink": "/apis/custom.metrics.k8s.io/v1beta1/"
    }
  }
  ```

# URLs

Use `ip="$(minikube ip)"` to get the IP address of the cluster.

- Enqueue job:

  ```shell
  queue=high
  curl -XPOST \
    -H 'Content-Type: application/json' \
    -d '{"sleep": 60}' \
    "http://$ip:32000/queues/$queue/enqueue"
  ```

  Sample output:
  ```json
  {
    "job": {
      "id": "uuiduuid-uuid-4uid-uuid-uuiduuiduuid",
      "result": null,
      "status": "queued"
    }
  }
  ```

# Running Python app tests

```shell
cd docker/metricsexporter

# Run all static analysis (flake8, black, isort, mypy, pylint. Then run pytest
../../../.python-app-tests.sh metricsexporter
```

# Troubleshooting

## Checking the metrics API service is working

```shell
kubectl get apiservice | grep custom.metrics
```
```
v1beta1.custom.metrics.k8s.io  YOUR_NAMESPACE_HERE/custom-metrics-apiserver  True  1h
```

## Reinstalling the app

If kubernetes won't allow helm to reinstall the app due to lingering objects after an uninstall, use the following:

```shell
kubectl proxy &  # get a proxy listening on port 8001.
namespace=YOUR_NAMESPACE_HERE
curl -k \
  -XPUT \
  -H "Content-Type: application/json" \
  --data-binary '{"apiVersion":"v1","kind":"Namespace","metadata":{"name":"'"$namespace"'"},"spec":{"finalizers":[]}}' \
  "http://127.0.0.1:8001/api/v1/namespaces/$namespace/finalize"
```

## Miscellaneous error messages

- `Error from server (ServiceUnavailable): the server is currently unable to handle the request`
  may indicate that the namespace in the certificates does not match the deployed namespace.
