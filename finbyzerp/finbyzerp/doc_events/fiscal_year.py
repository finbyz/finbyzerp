from erpnext.accounts.doctype.fiscal_year.fiscal_year import FiscalYear


def before_save(self: FiscalYear, method: str):
    create_fiscal_field(self)

def create_fiscal_field(self: FiscalYear):
    if self.year_start_date and self.year_end_date:
        self.fiscal = str(self.year_start_date)[2:4] + str(self.year_end_date)[2:4]