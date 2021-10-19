import rdflib  # type: ignore
import requests
import subprocess

from typing import Optional, Tuple

from nanopub_submitter.config import SubmitterConfig
from nanopub_submitter.consts import DEFAULT_ENCODING, PACKAGE_NAME, PACKAGE_VERSION
from nanopub_submitter.logger import LOG
from nanopub_submitter.triple_store import store_to_triple_store

EXIT_SUCCESS = 0


class NanopubProcessingError(RuntimeError):

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message


class NanopubSubmissionResult:

    def __init__(self, location: Optional[str], servers: list[str],
                 triple_store: Optional[bool]):
        self.location = location
        self.servers = servers
        self.triple_store = triple_store

    def __str__(self):
        str = [f'Nanopublication URI: {self.location}']
        if len(self.servers) > 0:
            str.append('Published via servers:')
        for server in self.servers:
            str.append(f'- {server}')
        if self.triple_store:
            str.append('\n+ Nanopublication has been stored to triple-store')
        return '\n'.join(str)


class NanopubProcessingContext:

    def __init__(self, submission_id: str, cfg: SubmitterConfig):
        self.id = submission_id
        self.cfg = cfg
        self.uri = None

    def cleanup(self):
        files = (self.input_file, self.trusty_file, self.signed_file)
        for file_name in files:
            file_path = self.cfg.nanopub.workdir / file_name
            try:
                file_path.unlink(missing_ok=True)
            except Exception:
                pass

    @property
    def input_file(self) -> str:
        return f'{self.id}.trig'

    @property
    def trusty_file(self) -> str:
        return f'{self.id}.trusty.trig'

    @property
    def signed_file(self) -> str:
        return f'{self.id}.sign.trig'

    @property
    def _pre(self) -> str:
        return f'[ID:{self.id}]'

    def debug(self, message: str):
        LOG.debug(f'{self._pre} {message}')

    def info(self, message: str):
        LOG.info(f'{self._pre} {message}')

    def warn(self, message: str):
        LOG.warn(f'{self._pre} {message}')

    def error(self, message: str):
        LOG.error(f'{self._pre} {message}')


def _publish_nanopub(nanopub: str, ctx: NanopubProcessingContext) -> list[str]:
    success = []
    for server in ctx.cfg.nanopub.target_servers:
        ctx.debug(f'Submitting to: {server}')
        r = requests.post(
            url=server,
            data=nanopub,
            headers={
                'Content-Type': f'application/trig; charset={DEFAULT_ENCODING}',
                'User-Agent': f'{PACKAGE_NAME}/{PACKAGE_VERSION}',
            }
        )
        if r.ok:
            ctx.warn(f'Nanopub published via {server}')
            success.append(server)
        else:
            ctx.warn(f'Failed to publish nanopub via {server}')
            ctx.debug(f'status={r.status_code}')
            ctx.debug(r.text)
    return success


def _store_triple_store(nanopub: str, ctx: NanopubProcessingContext) -> bool:
    try:
        store_to_triple_store(
            cfg=ctx.cfg,
            data=nanopub,
            input_format='trig',
        )
    except Exception as e:
        ctx.warn(f'Failed to store nanopub in triple store: {str(e)}')
        return False
    return True


def _np(*args, ctx: NanopubProcessingContext) -> Tuple[int, str, str]:
    p = subprocess.Popen(
        args=[ctx.cfg.nanopub.client_exec, *args],
        cwd=str(ctx.cfg.nanopub.workdir),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = p.communicate(timeout=ctx.cfg.nanopub.client_timeout)
    return p.returncode, stdout.decode(DEFAULT_ENCODING), stderr.decode(DEFAULT_ENCODING)


def _run_np_trusty(ctx: NanopubProcessingContext) -> str:
    exit_code, stdout, stderr = _np(
        'mktrusty', '-o', ctx.trusty_file, ctx.input_file,
        ctx=ctx
    )
    if exit_code != EXIT_SUCCESS:
        LOG.warn(f'Failed to make TrustyURI ({exit_code}):\n{stdout}\n\n{stderr}')
        raise NanopubProcessingError(
            status_code=500,
            message='Failed to make TrustyURI for nanopub.'
        )
    return ctx.trusty_file


def _run_np_sign(ctx: NanopubProcessingContext) -> str:
    exit_code, stdout, stderr = _np(
        'sign', '-a', ctx.cfg.nanopub.sign_key_type,
        '-k', ctx.cfg.nanopub.sign_private_key,
        '-o', ctx.signed_file, ctx.input_file,
        ctx=ctx
    )
    if exit_code != EXIT_SUCCESS:
        LOG.warn(f'Failed to make TrustyURI ({exit_code}):\n{stdout}\n\n{stderr}')
        raise NanopubProcessingError(
            status_code=500,
            message='Failed to make TrustyURI for nanopub.'
        )
    return ctx.signed_file


def _extract_np_uri(nanopub: str) -> Optional[str]:
    for line in nanopub.splitlines():
        if '@prefix this:' in line:
            try:
                return line.split('<', maxsplit=1)[1].split('>', maxsplit=1)[0]
            except Exception:
                continue
    return None


def process(cfg: SubmitterConfig, submission_id: str, data: str) -> NanopubSubmissionResult:
    ctx = NanopubProcessingContext(submission_id=submission_id, cfg=cfg)
    ctx.debug('Preprocessing nanopublication as RDF')
    try:
        graph = rdflib.ConjunctiveGraph()
        graph.parse(data=data, format='trig')
    except Exception as e:
        ctx.warn(f'Failed to preprocess nanopub: {str(e)}')
        raise NanopubProcessingError(400, f'Invalid RDF:\n{str(e)}')

    ctx.debug('Storing nanopub as file locally')
    np_file = cfg.nanopub.workdir / ctx.input_file
    try:
        np_file.parent.mkdir(parents=True, exist_ok=True)
        np_file.write_text(data, encoding=DEFAULT_ENCODING)
    except Exception as e:
        ctx.error(f'Failed to store nanopub: {str(e)}')
        ctx.cleanup()
        raise NanopubProcessingError(500, 'Failed to store nanopub locally')

    ctx.debug('Generating trusty URIs for the nanopub')
    result_file = _run_np_trusty(ctx=ctx)

    if cfg.nanopub.sign_nanopub:
        ctx.debug('Signing nanopub with private key')
        result_file = _run_np_sign(ctx=ctx)
    else:
        ctx.debug('Signing nanopub skipped (disabled by config)')

    ctx.debug('Reading final nanopub')
    result_path = cfg.nanopub.workdir / result_file
    try:
        nanopub = result_path.read_text(encoding=DEFAULT_ENCODING)
        nanopub_uri = _extract_np_uri(nanopub)
    except Exception as e:
        ctx.error(f'Failed to read nanopub: {str(e)}')
        ctx.cleanup()
        raise NanopubProcessingError(500, 'Failed to read nanopub locally')

    if nanopub_uri is None:
        ctx.error('Failed to extract nanopub URI')
        ctx.cleanup()
        raise NanopubProcessingError(400, 'Failed to get nanopub URI')

    ctx.debug('Submitting nanopub to server(s)')
    servers = _publish_nanopub(nanopub=nanopub, ctx=ctx)

    if len(servers) == 0:
        ctx.error('Failed to publish nanopub')
        ctx.cleanup()
        raise NanopubProcessingError(500, 'Could not publish nanopublication'
                                          ' to any nanopub server.')

    triple_store = None
    if cfg.triple_store.enabled:
        ctx.debug(f'Sending nanopub to: {cfg.triple_store.sparql_endpoint}')
        triple_store = _store_triple_store(nanopub=nanopub, ctx=ctx)

    ctx.debug('Processing finished')
    ctx.cleanup()
    return NanopubSubmissionResult(
        location=nanopub_uri,
        servers=servers,
        triple_store=triple_store,
    )
