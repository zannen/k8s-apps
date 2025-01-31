#!/bin/sh

cat >/usr/share/nginx/html/index.html <<EOF
<!DOCTYPE html>
<html>
<head><title>A Webserver</title></head>
<body>
<h1>A Webserver!</h1>
<p>This page was last updated at: $(date).</p>
</body>
</html>
EOF
