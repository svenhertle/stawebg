#!/bin/bash

tmp_file=$(mktemp)

html=$(tee "$tmp_file" | man -l - | col -b)

title="$(grep "\.TH" "$tmp_file" | awk '{print $2}' | sed -r "s/\"(.*)\"/\1/g")"

echo "<h1>$title</h1>"
echo "<pre>"
echo "$html"
echo "</pre>"

rm -f "$tmp_file"
