import fastapi
import fastapi.responses
import os
import pathlib
import uuid

from typing import Tuple

from nanopub_submitter.config import cfg_parser
from nanopub_submitter.consts import NICE_NAME, VERSION, BUILD_INFO,\
    ENV_CONFIG, DEFAULT_CONFIG, DEFAULT_ENCODING
from nanopub_submitter.logger import LOG, init_default_logging, init_config_logging
from nanopub_submitter.nanopub import process, NanopubProcessingError

app = fastapi.FastAPI(
    title=NICE_NAME,
    version=VERSION,
)
cfg = cfg_parser.config


def _valid_token(request: fastapi.Request) -> bool:
    if not cfg.security.enabled:
        LOG.debug('Security disabled, authorized directly')
        return True
    auth = request.headers.get('Authorization', '')  # type: str
    if not auth.startswith('Bearer '):
        LOG.debug('Invalid token (missing or without "Bearer " prefix')
        return False
    token = auth.split(' ', maxsplit=1)[1]
    return token in cfg.security.tokens


def _extract_content_type(header: str) -> Tuple[str, str]:
    type_headers = header.lower().split(';')
    input_format = type_headers[0]
    if len(type_headers) == 0:
        return input_format, DEFAULT_ENCODING
    encoding_header = type_headers[0].strip()
    if encoding_header.startswith('charset='):
        return input_format, encoding_header[9:]
    return input_format, DEFAULT_ENCODING


@app.get(path='/')
async def get_info():
    return fastapi.responses.JSONResponse(
        content=BUILD_INFO,
    )


@app.post(path='/submit')
async def submit_nanopub(request: fastapi.Request):
    # (1) Verify authorization
    if not _valid_token(request=request):
        return fastapi.responses.PlainTextResponse(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            content='Unauthorized submission request.\n\n'
                    'The submission service is not configured properly.\n'
        )
    # (2) Extract data
    submission_id = str(uuid.uuid4())
    data = await request.body()
    input_format, encoding = _extract_content_type(request.headers.get('Content-Type'))
    if input_format != 'application/trig':
        return fastapi.responses.Response(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            content=f'Unsupported content-type: {input_format}\n'
                    f'Nanopublication must be in TriG format'
        )
    # (3) Process
    try:
        result = process(
            cfg=cfg,
            submission_id=submission_id,
            data=data.decode(encoding),
        )
    except NanopubProcessingError as e:
        return fastapi.responses.PlainTextResponse(
            status_code=e.status_code,
            content=e.message,
        )
    except Exception as e:
        LOG.error(f'[{submission_id}] Unexpected processing error: {str(e)}')
        return fastapi.responses.PlainTextResponse(
            status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
            content='Failed to process the nanopublication',
        )
    # (4) Return
    return fastapi.responses.Response(
        status_code=fastapi.status.HTTP_201_CREATED,
        headers={
            'Location': result.location,
        },
        content=str(result),
    )


@app.on_event("startup")
async def app_init():
    global cfg
    init_default_logging()
    config_file = os.getenv(ENV_CONFIG, DEFAULT_CONFIG)
    try:
        with pathlib.Path(config_file).open() as fp:
            cfg = cfg_parser.parse_file(fp=fp)
        init_config_logging(config=cfg)
    except Exception as e:
        LOG.warn(f'Failed to load config: {config_file}')
        LOG.debug(str(e))
    LOG.info(f'Loaded config: {config_file}')
