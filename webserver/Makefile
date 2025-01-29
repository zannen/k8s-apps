default: docker

.PHONY: docker
docker:
	@img="zannen/webserver" && \
	ver=$$(python -c 'import yaml; print(yaml.safe_load(open("values.yaml","r"))["webserverVersion"])') && \
	cd docker && \
	echo "Building $$img:$$ver" && \
	docker build -t "$$img:$$ver" webserver/
