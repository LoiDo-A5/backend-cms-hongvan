#!/usr/bin/env bash
echo $(git show -s --format=%ci HEAD | sed -e 's/\\+.+//' | sed -e 's/[-|:]/\./g' | sed -e 's/ /-/' | sed -e 's/\.[^\.]*$//')
