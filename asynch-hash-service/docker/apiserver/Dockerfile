FROM python:3.12-alpine
RUN addgroup -g 1000 runner && adduser -g Runner -D -G runner -u 1000 runner
RUN apk update && \
	apk add mariadb-dev && \
	apk add --virtual \
		build-deps \
		gcc \
		musl-dev \
		python3-dev \
	&& \
	pip install mysqlclient==2.2.7 && \
	cp $(find /root/.cache/pip/wheels -name 'mysqlclient*.whl') /tmp/ && \
	apk del build-deps
USER runner
WORKDIR /home/runner
ENV FLASK_APP=server FLASK_ENV=development PATH="/home/runner/.local/bin:$PATH" PYTHONPATH=/home/runner
RUN python -m pip install --user --upgrade pip
RUN pip install --user /tmp/mysqlclient-*.whl
ADD requirements.txt ./
RUN pip install --user -r requirements.txt
ADD /app ./app
