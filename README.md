# DSW Nanopub Submission Service

[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/ds-wizard/nanopub-submission-service)](https://github.com/ds-wizard/nanopub-submission-service/releases)
[![Docker Pulls](https://img.shields.io/docker/pulls/datastewardshipwizard/nanopub-submission-service)](https://hub.docker.com/r/datastewardshipwizard/nanopub-submission-service)
[![GitHub](https://img.shields.io/github/license/ds-wizard/nanopub-submission-service)](LICENSE)

Submission service for publishing nanopublications from DSW

## Usage

### Docker

The best is to use this service as part of a `docker-compose.yml` as follows:

```yml
  submission-service:
    image: datastewardshipwizard/nanopub-submission-service:develop
    restart: always
    # If you need to expose a port:
    ports:
      - 8083:80
    volumes:
    # Mount configuration file:
      - ./submission-service/config.yml:/app/config.yml:ro
    # For signing purposes, mount RSA or DSA:
    #  - ./submission-service/id_dsa:/app/id_dsa:ro
    #  - ./submission-service/id_dsa.pub:/app/id_dsa.pub:ro
    #  - ./submission-service/id_rsa:/app/id_rsa:ro
    #  - ./submission-service/id_rsa.pub:/app/id_rsa.pub:ro
```

### Configuration

You can check the example [`config.yml`](config.yml) to see all the options.
The minimal example for with the Docker image is here:

```yml
nanopub:
  servers:
    - http://nanopub:8080
  sign_nanopub: false
  # Or for signing (optional):
  #sign_nanopub: true
  #sign_key_type: RSA
  #sign_private_key: /app/id_rsa

# Security (optional):
security:
  enabled: true
  tokens:
    - mySecretToken1
    - mySecretToken2
```

### Signing keys

To generate the signing keys (RSA or DSA), please use the `np` tool directly:

```shell
$ ./bin/np mkkeys -a DSA -f ./id_dsa
# OR
$ ./bin/np mkkeys -a DSA -f ./id_rsa
```

Then mount the keys (private and public) and edit the configuration appropriately.

## License

This project is licensed under the Apache License v2.0 - see the
[LICENSE](LICENSE) file for more details.
