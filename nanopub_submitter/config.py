import pathlib
import random
import yaml

from typing import List, Optional


class MissingConfigurationError(Exception):

    def __init__(self, missing: List[str]):
        self.missing = missing


class NanopubConfig:

    def __init__(self, servers: List[str], client_exec: str,
                 strategy: str, strategy_number: int,
                 client_timeout: int, workdir: str, sign_key_type: str,
                 sign_nanopub: bool, sign_private_key: Optional[str]):
        self.servers = servers
        self.strategy = strategy.lower()
        self.strategy_number = strategy_number
        self.client_exec = client_exec
        self.client_timeout = client_timeout
        self.sign_nanopub = sign_nanopub
        self.sign_key_type = sign_key_type
        self.sign_private_key = sign_private_key
        self.workdir = pathlib.Path(workdir)

    @property
    def target_servers(self) -> list[str]:
        if self.strategy.startswith('random'):
            return random.choices(self.servers, k=self.strategy_number)
        return self.servers


class TripleStoreConfig:

    def __init__(self, enabled: bool, sparql_endpoint: str, auth_method: str,
                 auth_username: str, auth_password: str, graph_class: str,
                 graph_named: str, graph_type: str, extra_queries: bool,
                 strategy: str):
        self.enabled = enabled
        self.sparql_endpoint = sparql_endpoint
        self.auth_method = auth_method
        self.auth_username = auth_username
        self.auth_password = auth_password
        self.graph_class = graph_class
        self.graph_named = graph_named
        self.graph_type = graph_type
        self.extra_queries = extra_queries
        self.strategy = strategy


class SecurityConfig:

    def __init__(self, enabled: bool, tokens: List[str]):
        self.enabled = enabled
        self.tokens = tokens


class LoggingConfig:

    def __init__(self, level, message_format: str):
        self.level = level
        self.format = message_format


class MailConfig:

    def __init__(self, enabled: bool, name: str, email: str,
                 host: str, port: int, security: str, auth: bool,
                 username: str, password: str, recipients: list[str]):
        self.enabled = enabled
        self.name = name
        self.email = email
        self.host = host
        self.port = port
        self.security = security.lower()
        self.auth = auth
        self.username = username
        self.password = password
        self.recipients = recipients


class SubmitterConfig:

    def __init__(self, nanopub: NanopubConfig, security: SecurityConfig,
                 triple_store: TripleStoreConfig, logging: LoggingConfig,
                 mail: MailConfig):
        self.nanopub = nanopub
        self.security = security
        self.triple_store = triple_store
        self.logging = logging
        self.mail = mail


class SubmitterConfigParser:

    DEFAULTS = {
        'nanopub': {
            'servers': ['http://nanopub-server:8080'],
            'strategy': 'all',
            'strategy_number': 1,
            'client_exec': 'np',
            'client_timeout': 10,
            'sign_nanopub': False,
            'sign_key_type': 'DSA',
            'sign_private_key': '',
            'workdir': '/app/workdir',
        },
        'triple_store': {
            'enabled': False,
            'sparql_endpoint': '',
            'auth': {
                'method': 'NONE',
                'username': '',
                'password': '',
            },
            'graph': {
                'class': 'ConjuctiveGraph',
                'named': False,
                'type': '',
            },
            'extra_queries': False,
            'strategy': 'basic',
        },
        'security': {
            'enabled': False,
            'tokens': [],
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s | %(levelname)s | %(module)s: %(message)s',
        },
        'mail': {
            'enabled': False,
            'name': 'Nanopub Submitter',
            'email': '',
            'host': '',
            'port': '',
            'security': 'plain',
            'authEnabled': False,
            'username': '',
            'password': '',
            'recipients': [],
        }
    }

    REQUIRED = []  # type: List[List[str]]

    def __init__(self):
        self.cfg = dict()

    def has(self, *path):
        x = self.cfg
        for p in path:
            if not hasattr(x, 'keys') or p not in x.keys():
                return False
            x = x[p]
        return True

    def _get_default(self, *path):
        x = self.DEFAULTS
        for p in path:
            x = x[p]
        return x

    def get_or_default(self, *path):
        x = self.cfg
        for p in path:
            if not hasattr(x, 'keys') or p not in x.keys():
                return self._get_default(*path)
            x = x[p]
        return x

    def validate(self):
        missing = []
        for path in self.REQUIRED:
            if not self.has(*path):
                missing.append('.'.join(path))
        if len(missing) > 0:
            raise MissingConfigurationError(missing)

    @property
    def _nanopub(self):
        return NanopubConfig(
            servers=self.get_or_default('nanopub', 'servers'),
            strategy=self.get_or_default('nanopub', 'strategy'),
            strategy_number=self.get_or_default('nanopub', 'strategy_number'),
            client_exec=self.get_or_default('nanopub', 'client_exec'),
            client_timeout=self.get_or_default('nanopub', 'client_timeout'),
            sign_nanopub=self.get_or_default('nanopub', 'sign_nanopub'),
            sign_key_type=self.get_or_default('nanopub', 'sign_key_type'),
            sign_private_key=self.get_or_default('nanopub', 'sign_private_key'),
            workdir=self.get_or_default('nanopub', 'workdir'),
        )

    @property
    def _security(self):
        return SecurityConfig(
            enabled=self.get_or_default('security', 'enabled'),
            tokens=self.get_or_default('security', 'tokens'),
        )

    @property
    def _logging(self):
        return LoggingConfig(
            level=self.get_or_default('logging', 'level'),
            message_format=self.get_or_default('logging', 'format'),
        )

    @property
    def _triple_store(self):
        return TripleStoreConfig(
            enabled=self.get_or_default('triple_store', 'enabled'),
            sparql_endpoint=self.get_or_default('triple_store', 'sparql_endpoint'),
            auth_method=self.get_or_default('triple_store', 'auth', 'method'),
            auth_username=self.get_or_default('triple_store', 'auth', 'username'),
            auth_password=self.get_or_default('triple_store', 'auth', 'password'),
            graph_class=self.get_or_default('triple_store', 'graph', 'class'),
            graph_named=self.get_or_default('triple_store', 'graph', 'named'),
            graph_type=self.get_or_default('triple_store', 'graph', 'type'),
            extra_queries=self.get_or_default('triple_store', 'extra_queries'),
            strategy=self.get_or_default('triple_store', 'strategy'),
        )

    @property
    def _mail(self):
        return MailConfig(
            enabled=self.get_or_default('mail', 'enabled'),
            name=self.get_or_default('mail', 'name'),
            email=self.get_or_default('mail', 'email'),
            host=self.get_or_default('mail', 'host'),
            port=self.get_or_default('mail', 'port'),
            security=self.get_or_default('mail', 'security'),
            auth=self.get_or_default('mail', 'authEnabled'),
            username=self.get_or_default('mail', 'username'),
            password=self.get_or_default('mail', 'password'),
            recipients=self.get_or_default('mail', 'recipients'),
        )

    def parse_file(self, fp) -> SubmitterConfig:
        self.cfg = yaml.full_load(fp)
        self.validate()
        return self.config

    @property
    def config(self) -> SubmitterConfig:
        return SubmitterConfig(
            nanopub=self._nanopub,
            security=self._security,
            logging=self._logging,
            triple_store=self._triple_store,
            mail=self._mail,
        )


cfg_parser = SubmitterConfigParser()
