default: docker

.PHONY: docker
docker:
	@img="zannen/secretserver" && \
	ver=$$(python -c 'import yaml; print(yaml.safe_load(open("values.yaml","r"))["secretserverVersion"])') && \
	cd docker && \
	echo "Building $$img:$$ver" && \
	docker build -t "$$img:$$ver" secretserver/
