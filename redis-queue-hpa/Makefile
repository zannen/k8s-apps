default: docker

# rqmw is redis-queue-monitor-worker
.PHONY: docker
docker:
	@for i in metricsexporter rqmw ; do \
		img="zannen/$$i" && \
		ver=$$(python -c 'import yaml; print(yaml.safe_load(open("values.yaml","r"))["'"$$i"'Version"])') && \
		cd docker && \
		echo "Building $$img:$$ver" && \
		docker build -t "$$img:$$ver" "$$i/" && \
		cd .. ; \
	done
