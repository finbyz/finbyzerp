from urllib.parse import urljoin

def get_url(self, *parts):
	self.base_url = "https://gsp.adaequare.com"
	parts = [i for i in parts if i != '']

	if self.BASE_PATH:
		parts.insert(0, self.BASE_PATH)

	if self.sandbox_mode:
		parts.insert(0, "test")

	return urljoin(self.base_url, "/".join(part.strip("/") for part in parts))