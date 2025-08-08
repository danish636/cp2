from Crypto.Cipher import AES
import base64
import json
from django.http import HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from Crypto.Util.Padding import unpad
from rest_framework_simplejwt.authentication import JWTAuthentication
from datetime import date

key = b"RfW3W2i%xi}Tat4qxjR!gmseq$B&E)H@"
iv = b"Cx?Ol%ySeXjXdsMt"


def pkcs7padding(data, block_size=16):
    if type(data) != bytearray and type(data) != bytes:
        raise TypeError("Only support bytearray/bytes !")
    pl = block_size - (len(data) % block_size)
    return data + bytearray([pl for i in range(pl)])


class EncryptionMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_authentication = JWTAuthentication()

    # def __call__(self, request):
    #     response = self.get_response(request)
    #     return response

    def encrypted_aes(self, data):
        new_key = key
        data_json = json.dumps(data).encode("utf-8")
        # padded_data = data_json + b"\0" * (16 - len(data_json) % 16)
        padded_data = pkcs7padding(data_json)
        cipher = AES.new(new_key, AES.MODE_CBC, iv)
        encrypted_data = cipher.encrypt(padded_data)
        return base64.b64encode(encrypted_data).decode("utf-8")

    def decrypted_aes(self, encrypted):
        new_key = key

        encrypted = base64.b64decode(encrypted)
        cipher = AES.new(new_key, AES.MODE_CBC, iv)
        decrypted_data = unpad(cipher.decrypt(encrypted), AES.block_size)
        decrypted_json = json.loads(decrypted_data.decode('utf-8'))
        return decrypted_json

    def process_response(self, request, response):
        if response.get("Content-Type") == "application/json":
            try:
                response_data = json.loads(response.content.decode("utf-8"))
                encrypted_response = self.encrypted_aes(response_data)
                response.content = json.dumps({"data": encrypted_response}).encode("utf-8")
                response["Access-Control-Allow-Origin"] = "*"
                return HttpResponse(response, content_type="application/json")
            except:
                return HttpResponse(response)
        else:
            print("here")
            return response

    def process_request(self, request):
        try:
            user_auth_tuple = self.jwt_authentication.authenticate(request)
            if user_auth_tuple is not None:
                request.user, _ = user_auth_tuple
        except:
            pass
        valid_symbols = ["AAPL", "TSLA", "MSFT", "AMZN", "GOOGL", "META", "SPY", "BRK-A", "XOM", "QQQ"]
        # symbol_urls = ["/etf_stock_exposure/", "/balanceSheet/", "/balanceSheetLock/", "/cashFlow/", "/cashFlowLock/", "/ratiottm/", "/get_company_2", "/get_quarters", "/get_quarters_0", "/option_chain",  "/relative_valuation_2", "/relative_valuation", "/historical_relative_valuation", "/pro_version", "/get_symbol_quarter", "/rv_symbol"]
        # ticker_urls = ["/website_quote"]
        if request.META.get("CONTENT_TYPE") == "application/json":
            # exception_paths = ["/login/", "/header2/", "/user_signup", "/setpassword"]

            res = json.loads(request.body.decode('utf-8'))

            if request.get_full_path() == "/webhook":
                request_data = res
            else:
                request_data = self.decrypted_aes(res["data"])
            # flag = True

            # if request.get_full_path() not in exception_paths:
            #     if request.user.prime_user != True:
            #         if (date.today() - request.user.created_at).days <= 14:
            # if request.get_full_path() in symbol_urls:
            #     if "symbol" in request_data.keys():
            #         if request_data.get("symbol").upper() in valid_symbols:
            #             flag=False
            #             request._body = json.dumps(request_data).encode("utf-8").strip()
            #         else:
            #             return JsonResponse({"data":"You are not authorized for this request"})

            # if request.get_full_path() in ticker_urls:
            #     if "ticker" in request_data.keys():
            #         if request_data.get("ticker").upper() in valid_symbols:
            #             flag=False
            #             request._body = json.dumps(request_data).encode("utf-8").strip()
            #         else:
            #             return JsonResponse({"data":"You are not authorized for this request"})

            #     if "symbol" in request_data.keys():
            #         if request_data.get("symbol").upper() in valid_symbols:
            #             flag=False
            #         else:
            #             return JsonResponse({"data":"You are not authorized for this request", "status":False})

            #     if "ticker" in request_data.keys():
            #         if request_data.get("ticker").upper() in valid_symbols:
            #             flag=False
            #         else:
            #             return JsonResponse({"data":"You are not authorized for this request", "status":False})

            #     if flag:
            #         return JsonResponse({"data":"You are not authorized for this request", "status":False})

            # else:
            #     return JsonResponse({"data":"Your Trail period has been expired.", "status":False})

            try:
                request._body = json.dumps(request_data).encode("utf-8").strip()
            except:
                pass

