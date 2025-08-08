from Crypto.Cipher import AES
import base64
import json
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

key = b"RfW3W2i%xi}Tat4qxjR!gmseq$B&E)H@"
iv = b"Cx?Ol%ySeXjXdsMt"


class EncryptionMiddleware(MiddlewareMixin):

    def encrypted_aes(self, data):
        new_key = key
        data_json = json.dumps(data).encode("utf-8")
        padded_data = data_json + b"\0" * (16 - len(data_json) % 16)
        cipher = AES.new(new_key, AES.MODE_CBC, iv)
        encrypted_data = cipher.encrypt(padded_data)
        return base64.b64encode(encrypted_data).decode("utf-8")

    def decrypted_aes(self, encrypted):
        new_key = key

        encrypted = base64.b64decode(encrypted)
        cipher = AES.new(new_key, AES.MODE_CBC, iv)
        decrypted_data = cipher.decrypt(encrypted)
        return decrypted_data.rstrip(b'\0').decode('utf-8')

    def process_response(self, request, response):
        if response.get("Content-Type") == "application/json" and response.status_code == 200:
            response_data = json.loads(response.content.decode("utf-8"))
            encrypted_response = self.encrypted_aes(response_data)
            response.content = json.dumps({"data": encrypted_response}).encode("utf-8")
        return response

    def process_request(self, request):
        if request.META.get("CONTENT_TYPE") == "application/json":
            # print(request.body)
            # print(request.body.decode('utf-8').strip().replace('\r\n', '').replace(' ', ''))
            res = json.loads(request.body.decode('utf-8'))

            request_data = self.decrypted_aes(res["data"])
            # print(request_data)
            try:
                request._body = json.dumps(request_data).encode("utf-8")
            except:
                pass

