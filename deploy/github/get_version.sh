#!/usr/bin/env bash
# shellcheck disable=SC2046
echo $(echo $COMMIT_TIME | sed -e 's/\\+.+//' | sed -e 's/[-|:]/\./g' | sed -e 's/ /-/' | sed -e 's/\.[^\.]*$//' | cut -c1-16)
