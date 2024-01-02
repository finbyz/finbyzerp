from typing import Optional

from erpnext.stock.report.stock_balance.stock_balance import StockBalanceFilter, StockBalanceReport
from frappe import _


def execute(filters: Optional[StockBalanceFilter] = None):
	return CustomStockBalanceReport(filters).run()
	
class CustomStockBalanceReport(StockBalanceReport):
	def get_columns(self):
		columns = super().get_columns()

		columns.append(
			{
				"label": _("Stock Ledger"),
				"fieldname": "stock_ledger",
				"fieldtype": "button",
				"width": 140
			}
		)

		return columns

	def prepare_new_data(self):
		super().prepare_new_data()

		for row in self.data:
			row['stock_ledger'] =f"""<button class="btn btn-primary report-button" target="_blank" item_code='{row['item_code']}' warehouse='{row['warehouse']}'
			 	onClick=finbyzerp.open_stock_ledger.open_stock_ledger(this.getAttribute('item_code'),this.getAttribute('warehouse'))>View Stock Ledger</button>"""
