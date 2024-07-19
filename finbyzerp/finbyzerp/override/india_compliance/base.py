from urllib.parse import urljoin

BASE_URL = "https://gsp.adaequare.com"

def get_url(self, *parts):
	parts = list(parts)

	# If the first part is a URL, return it as it is
	if parts and parts[0].startswith("https"):
		return parts[0]

	if self.BASE_PATH:
		parts.insert(0, self.BASE_PATH)

	if self.sandbox_mode:
		parts.insert(0, "test")

	return urljoin(BASE_URL, "/".join(part.strip("/") for part in parts))