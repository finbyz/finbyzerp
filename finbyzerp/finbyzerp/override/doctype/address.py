from frappe.contacts.doctype.address.address import Address as _Address
from india_compliance.gst_india.utils.gstin_info import get_gstin_info
import frappe

class Address(_Address):
    def before_validate(self):
        try:
            if self.fetch_from_gst_no:
                if self.gstin:
                    gst_data=get_gstin_info(self.gstin)
                    data=gst_data["permanent_address"]
                    self.pincode=data.get("pincode","")
                    self.address_line1=data.get("address_line1","")
                    self.address_line2=data.get("address_line2","")
                    self.city=data.get("city","")
                    self.state=data.get("state","")
                    self.country=data.get("country","")
                    self.address_title= gst_data["business_name"]  
                    self.fetch_from_gst_no=0     
        except Exception as e:
            frappe.throw(str(e))
        if hasattr(_Address, 'before_validate'):
            super(_Address, self).before_validate()

