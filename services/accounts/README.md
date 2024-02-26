# GitClub (Python - SQLAlchemy - Flask)

This is an example application based on GitHub that's meant to model GitHub's
permissions system. The app uses the [`oso-cloud`][pypi-oso-cloud] library to
model, manage, and enforce authorization.

[pypi-oso-cloud]: https://pypi.org/project/oso-cloud/

The [Oso Cloud documentation][docs] is a good reference for more information on
Oso's [Python][docs-python] library.

[docs]: https://cloud-docs.osohq.com/
[docs-python]: https://cloud-docs.osohq.com/reference/client-apis/python

## Installation

### Install the Oso Local Binary:
```
wget https://oso-local-development-binary.s3.amazonaws.com/1.1.5
/oso-local-development-binary-linux-x86_64.tar.gz
tar xvf oso-local-development-binary-linux-x86_64.tar.gz
chmod +x standalone
./standalone
```

### Install python

Install `uv`
```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Create virtual environment
```
uv venv
source .venv/bin/activate
```

Install python dependencies

```
uv pip install -r requirements.txt
uv pip install -e .
```

### Setup Oso

Install CLI:

```
curl -L https://cloud.osohq.com/install.sh | bash
```

set environment up:

```
export OSO_URL=http://localhost:8080
export OSO_AUTH=e_0123456789_12345_osotesttoken01xiIn
```

Load policy:

```
oso-cloud policy ../../policy/authorization.polar
```