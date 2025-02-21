#!/bin/bash

ip="$(minikube ip)"
base="http://$ip:30880"

token="${TOKEN:-}"
if [[ -z "$token" ]] ; then
	echo -n "Getting a token... "
	response="$(curl --silent \
		-XPOST \
		-H 'Content-type: application/json' \
		--data {} \
		"$base/token")"
	token="$(echo "$response" | jq -r .token)"
	echo "$token"
fi

job_id="${JOB_ID:-}"
if [[ -z "$job_id" ]] ; then
	echo -n "Creating a job ... "
	response="$(curl --silent \
		-XPOST \
		-H "API-Key: $token" \
		-H 'Content-type: application/json' \
		--data '{"data":"test", "hexzeros": 7}' \
		"$base/jobs")"
	job_id="$(echo "$response" | jq -r .job.id)"
	echo "$job_id"
	if [[ "$job_id" == null ]] ; then
		echo "$response"
	fi
	sleep 1
fi

while true ; do
	response="$(curl --silent \
		-XGET \
		-H "API-Key: $token" \
		"$base/jobs/$job_id")"
	status="$(echo "$response" | jq -r .job.status)"
	if [[ "$status" == finished ]] ; then
		echo "$response" | jq .
		break
	else
		nonce="$(echo "$response" | jq -r .job.extra.nonce)"
		echo "$nonce ..."
		if [[ "$nonce" == null ]] ; then
			echo "$response"
		fi
	fi
	sleep 1
done
