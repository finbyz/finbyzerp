# -*- coding: utf-8 -*-
from __future__ import unicode_literals

__version__ = '14.0.5'

from india_compliance.gst_india.report.gstr_1 import gstr_1
from finbyzerp.finbyzerp.override.gstr_1 import execute 
gstr_1.execute = execute