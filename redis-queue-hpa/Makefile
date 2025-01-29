default: docker

.PHONY: docker
docker:
	@img="zannen/redis-queue-monitor-worker" && \
	ver=$$(python -c 'import yaml; print(yaml.safe_load(open("values.yaml","r"))["rqmwVersion"])') && \
	cd docker && \
	echo "Building $$img:$$ver" && \
	docker build -t "$$img:$$ver" redis-queue-monitor-worker/
