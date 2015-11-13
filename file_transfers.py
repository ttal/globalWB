import requests


class FileTransfers:
    def __init__(self, post_file_name, get_file_name,
                 post_ip_address='http://45.79.92.198:8080/api/images',
                 get_ip_address='http://45.79.92.198:8080/api/images/merged'):
        self.post_file_name = post_file_name
        self.get_file_name = get_file_name
        self.post_ip_address = post_ip_address
        self.get_ip_address = get_ip_address

    def post_file(self):
        files = {'file': open(self.post_file_name, 'rb')}
        _ = requests.post(self.post_ip_address, files=files)

    def get_file(self):
        response = requests.get(self.get_ip_address)

        f_out = open(self.get_file_name, 'w')
        for block in response:
            f_out.write(block)

        f_out.close()
