[![GitHub Workflow Status](https://github.com/soda480/with-keepass/workflows/ci/badge.svg)](https://github.com/soda480/with-keepass/actions)
![Coverage](https://raw.githubusercontent.com/soda480/with-keepass/main/badges/coverage.svg)
[![PyPI version](https://badge.fury.io/py/with-keepass.svg)](https://badge.fury.io/py/with-keepass)
[![python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-teal)](https://www.python.org/downloads/)

# with-keepass

A command-line utility that allows you to run any command with environment variables automatically injected from a KeePass database. This is especially useful for securely managing sensitive credentials without hardcoding them into scripts, leaving them in plaintext in your shell history or exposing them in the parent shell.

### Why use `with-keepass`?

Managing secrets is hard:

* .env files leak — credentials often end up in repos, backups, or logs.

* Shell pollution — exporting secrets into your parent shell keeps them around after you’re done.

* Copy/paste risk — copying values from KeePass into terminals or scripts risks accidental exposure.

with-keepass solves this by:

* Loading secrets directly from your KeePass database.

* Injecting them as environment variables only into the child process (never your shell).

* Ensuring secrets are ephemeral — they disappear when the process exits.

* Working with any CLI tool or script (AWS CLI, kubectl, Python apps, etc.).

KeePass stays your single source of truth, while secrets stay safer.

## Installation

```bash
pip install with-keepass
```

## KeePass mapping model

Secrets can be loaded from either a KeePass group or a single entry:

* Group path

  * Each entry inside the group becomes an environment variable.

  * Entry Title is the variable name

  * Custom string field value is the variable value

  ### Group path example

  ```
  Group: EnvVars
  Entry: API_KEY
    Title: API_KEY
    Custom String Field "value": abcd1234
  Entry: DB_PASS
    Title: DB_PASS
    Custom String Field "value": supersecret
  ```
  Produces:

  ```
  API_KEY=abcd1234
  DB_PASS=supersecret
  ```

* Entry path

  * A single entry can hold multiple fields.

  * Each custom string field becomes an environment variable.

  ### Entry path example

  ```
  Entry: MyApp
  Title: MyApp
  Custom String Field "API_KEY": abcd1234
  Custom String Field "DB_PASS": supersecret
  Custom String Field "REGION": us-west-2
  ```

  Produces:

  ```
  API_KEY=abcd1234
  DB_PASS=supersecret
  REGION=us-west-2
  ```

## Usage & Options

```bash
usage: with-keypass [-h] [--db-path DB_PATH] [--path PATH] [--dry-run] ...

Execute a command with environment variables loaded from KeePass.

positional arguments:
  command            Command to execute; must be preceded by -- (not required with --dry-run)

options:
  -h, --help         show this help message and exit
  --db-path DB_PATH  path to KeePass .kdbx database file
                                              (default: $HOME/.keypass/.kp.kdbx)
  --path PATH        path to KeePass entry or KeePass group containing the secrets to load
                                              (default: EnvVars)
  --dry-run          print NAME=value pairs and exit; do not exec a command
                                              (default: False)
```

**Notes**

* `with-keypass` will prompt for the master password of the KeePass database.

* Separate with-keepass options from the target command with --.

* The --path may refer to either a group or an entry.

* Able to set `--db-path` and `--path` via the following environment variables respectively `KEEPASS_DB_PATH` and `KEEPASS_PATH`


## Examples

Run AWS CLI with injected credentials:
```bash
with-keypass \
--path 'AwsSecrets' \
-- aws s3 ls
```

Preview environment variables:
```bash
with-keypass --dry-run
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

Run kubectl with secrets from a custom DB:
```bash
with-keepass \
--db-path "$HOME/.keepass/work.kdbx" \
--path 'Root/Secrets/K8s' \
-- kubectl get pods --namespace=default
```

## Exit Codes
| Code | Description |
| :------- | :------ |
| 0 | Success |
| 1 | Runtime error (failed to open DB, etc.) |
| 2 | Usage error (bad arguments, group not found, no secrets) |
| 130 | User aborted (Ctrl-C or password prompt canceled) |

## Security considerations

* Secrets are injected only into the executed process, never your shell.

* Secrets live in process memory while running; downstream apps may still log them.

* Master password is entered at runtime — do not hard-code it.

* Ensure your KeePass DB file is stored securely.

* Not a replacement for full secret-management services — use appropriately.


## Development

```bash
make dev
```

