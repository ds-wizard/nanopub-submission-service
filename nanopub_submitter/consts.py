PACKAGE_NAME = 'nanopub_submitter'
NICE_NAME = 'DSW Nanopublication Submission Service'
PACKAGE_VERSION = '1.1.0'
ENV_CONFIG = 'SUBMISSION_CONFIG'
LOGGER_NAME = 'DSW_SUBMITTER'

_DEFAULT_BUILT_AT = 'BUILT_AT'
BUILT_AT = '--BUILT_AT--'
_DEFAULT_VERSION = 'VERSION'
VERSION = '--VERSION--'

COMMENT_INSTRUCTION_DELIMITER = ':'
COMMENT_PRE_QUERY_PREFIX = '#> pre-query:'
COMMENT_POST_QUERY_PREFIX = '#> post-query:'

DEFAULT_ENCODING = 'utf-8'
DEFAULT_CONFIG = '/app/config.yml'
DEFAULT_LOG_LEVEL = 'INFO'
DEFAULT_LOG_FORMAT = '%(asctime)s | %(levelname)s | %(module)s: %(message)s'


BUILD_INFO = {
    'name': NICE_NAME,
    'packageVersion': PACKAGE_VERSION,
    'version': VERSION if VERSION != f'--{_DEFAULT_VERSION}--' else 'unknown',
    'builtAt': BUILT_AT if BUILT_AT != f'--{_DEFAULT_BUILT_AT}--' else 'unknown',
}
