# Changelog

## Unreleased (2024-10-28)

### Chore

- rewrite CHANGELOG.md 

### Dev

- upgrade flake.nix to self-contain without .venv 

### Docs

- update README.md 
- fix `--dry_run` to `--dry-run` in docs, along with single mispell 

## v1.2.2 (2024-10-04)

### Fixes

- change `--dry_run` into valid `--dry-run` option 

### Chore

- **changelog:** write CHANGELOG.md for version v1.2.2 

## v1.2.1 (2024-10-03)

### Features

- bring back python 3.7 

### Chore

- **changelog:** write CHANGELOG.md for version v1.2.0 
- **changelog:** write CHANGELOG.md for version v1.2.0 

### Docs

- remove ./docs in favor of README.md, convert *.rst to markdown versions 
- add CHANGELOG.md to the header tagble 
- add CHANGELOG.md to README.md file 

### Style

- remove empty line after TestRunenv cause tests on python 3.7 are complaining 

## v1.2.0 (2024-10-03)

### Features

- add support for ${VARIABLES} and support --prefix, --stip-prefix, --verbosity 1,2,3, --dry-run at command line 

### Chore

- **changelog:** write CHANGELOG.md for version v1.2.0 

### Docs

- rewrite README.md from scratch, providing python API fresh documentation, along wiht CLI usage 
- add CHANGELOG.md 

## v1.1.2 (2024-10-03)

### Fixes

- remove distutils in favor of shutil to support python 3.12 

### Build

- remove official support for python <=3.8 

### Docs

- update readme 

### Style

- fix ruff errors, and remove 2.7 python from travis 

## v1.1.1 (2024-10-03)

### Features

- migrate to pyproject.toml 
- add newest python versions to .travis.yml/tox.ini 

### Fixes

- support inline comments in .env files 
- readme.rst 
- get back README.rst 
- **doc:** README.md title 

## v1.0.1 (2017-02-03)

### Docs

- fix syntax error in README.md file 

## v1.0.0 (2017-02-03)

### Features

- add support python 3.5 

### Docs

- refine README.md 

## v0.4.0 (2016-08-08)

### Features

- add support for `search_parent` option to find .env files in parent directories 

## v0.3.1 (2016-06-21)

### Features

- add support for quoting values in .env files 

## v0.3.0 (2016-02-14)

### Build

- mark runenv as stable project 

## v0.2.5 (2015-11-30)

## v0.2.4 (2015-07-06)

### Features

- skip `load_env` if env file does not exists without failing 

## v0.2.3 (2015-06-26)

### Features

- support to run commands without explicite path, using PATH environment variable to find them 

## v0.2.2 (2015-06-16)

### Fixes

- support python 3.x 

## v0.2.1 (2015-06-16)

### Features

- add `strip-prefix` to the `load_env` python API function 

## v0.2.0 (2015-06-16)

### Features

- add `load_env` python API function 

## v0.1.4 (2015-06-15)

### Features

- check whether executable exists before run it 

## v0.1.3 (2015-06-01)

### Features

- add support for commened lines with # in .env files 

## v0.1.2 (2015-06-01)

### Features

- return exit code from runned command 

## v0.1.1 (2015-05-31)

### Fixes

- make runvenv work with many parameters for command 

## v0.1.0 (2015-05-31)

### Features

- Initial version of runenv 

