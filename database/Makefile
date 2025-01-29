default: docker

.PHONY: docker
docker:
	@img="zannen/apiserver" && \
	ver=$$(python -c 'import yaml; print(yaml.safe_load(open("values.yaml","r"))["apiVersion"])') && \
	cd docker && \
	echo "Building $$img:$$ver" && \
	docker build -t "$$img:$$ver" apiserver/
