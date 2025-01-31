default: docker

.PHONY: docker
docker:
	@for i in cronjob webserver ; do \
		img="zannen/$$i" && \
		ver=$$(python -c 'import yaml; print(yaml.safe_load(open("values.yaml","r"))["'"$$i"'Version"])') && \
		cd docker && \
		echo "Building $$img:$$ver" && \
		docker build -t "$$img:$$ver" "$$i/" && \
		cd .. ; \
	done
