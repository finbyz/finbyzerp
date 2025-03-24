import socket

def get_public_ip():
    """
    Fetches the public IP address of the machine without using an external service.
    
    Returns:
        str: Public IP address as a string.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception as e:
        print(f"Error fetching public IP: {e}")
        return None