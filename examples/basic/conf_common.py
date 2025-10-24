from esp_docs.conf_docs import *  # noqa: F403,F401
from esp_docs.constants import TARGETS


languages = ['en', 'zh_CN']
idf_targets = TARGETS

extensions += ['sphinx_copybutton',
               'sphinxcontrib.wavedrom',
               'esp_docs.generic_extensions.docs_embed',
               ]

# link roles config
github_repo = 'espressif/esp-idf'

# context used by sphinx_idf_theme
html_context['github_user'] = 'espressif'
html_context['github_repo'] = 'esp-docs'

html_static_path = ['../_static']

# Extra options required by sphinx_idf_theme
project_slug = 'esp-docs'

# Contains info used for constructing target and version selector
# Can also be hosted externally, see esp-idf for example
versions_url = './_static/docs_version.js'

# Final PDF filename will contains target and version
pdf_file_prefix = u'esp-docs'

# Wokwi info URL
about_wokwi_url = "https://docs.wokwi.com/"

docs_embed_skip_validation = True