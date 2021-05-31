from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.modules.import_file import import_file_by_path
import os
from os.path import join


def make_records(path, filters=None):
	if os.path.isdir(path):
		for fname in os.listdir(path):
			# Finbyz Changes Start: Dont update existing dashboards
			if frappe.db.exists('Dashboard',frappe.unscrub(fname)):
				continue
			# Finbyz Changes End
			if os.path.isdir(join(path, fname)):
				if fname == '__pycache__':
					continue
				import_file_by_path("{path}/{fname}/{fname}.json".format(path=path, fname=fname))
