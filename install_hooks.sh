#!/bin/sh

git config --unset-all core.hooksPath
git config core.hooksPath .github/hooks
