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

# data	zeros	   nonce	hash
# test	    0	       0	cab2614f067dc57faa95a99d2295fac791d16c28996ce54d4cbbca0b5f08330b
# test	    1	      30	0e46f170af1e06d7b6346314c0fe5d21a1955b7f091886bc9d1af8ffacd4fb4f
# test	    2	     227	0083bcbb41080af40a9c581845dd6c5c72bf937272d8bc9df20662b4fb95a703
# test	    3	    1472	00048394de3d4cf79895499a60e93210c0caf35d78a258e0f3c9f4033b4accb4
# test	    7	20553871	0000000133018e8c3653be2de0cfc2d929d3c3c09fc80e41996a30c29b6bfb30

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
