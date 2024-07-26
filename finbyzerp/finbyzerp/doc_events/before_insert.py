import frappe

def before_insert(self, method):
    opening_naming_series(self)
    
def opening_naming_series(self):
    if not self.name and self.is_opening == "Yes":
        self.naming_series = "O" + self.naming_series
        if self.naming_series.find("Ofiscal") != -1:
            self.naming_series = self.naming_series.replace("Ofiscal", "O.fiscal")
        
        if self.naming_series.find("Ocompany_series") != -1:
            self.naming_series = self.naming_series.replace("Ocompany_series", "O.company_series")
