default:
	@echo OK

.PHONY: docker
docker:
	@img="zannen/redis-queue-monitor-worker" && \
	ver=$$(python -c 'import yaml; print(yaml.safe_load(open("values.yaml","r"))["redisQueueMonitorWorkerVersion"])') && \
	cd docker && \
	echo "Building $$img:$$ver" && \
	docker build -t "$$img:$$ver" redis-queue-monitor-worker/
