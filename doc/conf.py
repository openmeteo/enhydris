# -*- coding: utf-8 -*-
#
extensions = []
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
project = 'Enhydris'
copyright = '2009-2011, National Technical University of Athens'
version = 'a'
release = 'b'
today_fmt = '%B %d, %Y'
html_theme_path = ['.']
html_theme = 'enhydris_theme'
html_title = "Enhydris documentation"
html_static_path = ['_static']
html_last_updated_fmt = '%b %d, %Y'
htmlhelp_basename = 'enhydrisdoc'
latex_documents = [
  ('index', 'enhydris.tex', 'Enhydris Documentation',
   'National Technical University of Athens', 'manual'),
]
