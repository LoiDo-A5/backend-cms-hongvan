#!/usr/bin/env bash
# shellcheck disable=SC2046
echo $GITHUB_REF | cut -c12-
