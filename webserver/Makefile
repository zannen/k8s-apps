default: docker

# Build a webserver docker container using the version pulled from values.yaml
.PHONY: docker
docker:
	@img="zannen/webserver" && \
	ver=$$(python -c 'import yaml; print(yaml.safe_load(open("values.yaml","r"))["webserverVersion"])') && \
	cd docker && \
	echo "Building $$img:$$ver" && \
	docker build -t "$$img:$$ver" webserver/
