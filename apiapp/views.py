import calendar
from django.shortcuts import render
from django.shortcuts import redirect
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import *
from Crypto.Cipher import AES
import base64
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, authentication_classes, permission_classes
import json
import os
import requests
from .config import *
import datetime
from .models import *
from rest_framework import status
from django.core.mail import send_mail
import random
import string
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import RedirectView
from django.http.response import HttpResponse

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView

from django.utils.decorators import decorator_from_middleware
from .middleware import EncryptionMiddleware
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.mail import EmailMultiAlternatives
from email.mime.image import MIMEImage

import chargebee
chargebee.configure("live_cdOArAJmyHR3Rhvn0M0IFoSRlyL6grs78","amassinginvestment")

from datetime import date, timedelta
import pandas as pd

class GoogleLoginView(SocialLoginView): # if you want to use Authorization Code Grant, use this
    adapter_class = GoogleOAuth2Adapter
    callback_url = "http://127.0.0.1:8000/"
    client_class = OAuth2Client

class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False
    def get_redirect_url(self):
        return "http://127.0.0.1:8000/"
    
def get_google_login_url(request):
    return render(request, "login.html")



class UserTokenObtainPairView(TokenObtainPairView):
    serializer_class = UserSerializer

def send_email(subject, html_content, sender, recipient, image_path, image_name):
    email = EmailMultiAlternatives(subject=subject, body="", from_email=sender,
                                   to=recipient if isinstance(recipient, list) else [recipient])
    if all([html_content, image_path, image_name]):
        email.attach_alternative(html_content, "text/html")
        email.content_subtype = 'html'
        email.mixed_subtype = 'related'
        with open(image_path, mode='rb') as f:
            image = MIMEImage(f.read())
            email.attach(image)
            image.add_header('Content-ID', f"<{image_name}>")
    email.send()

@api_view(['POST'])
@permission_classes([AllowAny])
def user_signup(request):
    data = request.data
    status = data.get("status", False)
    if data.get("status"):
        try:
            if User.objects.filter(email=data.get("email")).exists():
                return Response({"data" : "User with this email already exists.","status" : 500})
            u = User.objects.create(email=data.get("email"))
            u.set_password(data.get("password"))
            u.save()
            return Response({"data" : "data saved","status" : 200})
        except:
            return Response({"data" : "Something went wrong","status" : 500})
    
    if User.objects.filter(email=data.get("email")).exists():
        return Response({"data" : "User with this email already exists.","status" : 500})
    
    #u = User.objects.create(email=data.get("email"))
    random_number = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

    if TempTokenModel.objects.filter(email=data.get("email")).exists():
        TempTokenModel.objects.filter(email=data.get("email")).delete()
        
    TempTokenModel.objects.create(email=data.get("email"), token=random_number)
    
    link = f"https://amassinginvestment.com/set-password/{random_number}"

    html_message = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta http-equiv="X-UA-Compatible" content="IE=edge">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Document</title>
        </head>
        <body>
            <div style="text-align:center;margin-left:auto;margin-right:auto;width:100%;">
                <img src="cid:img1" alt="Logo" style="width:200px;height:100px"></div>
            
            <h1><strong>Set Up Your Amassing Investment Password</strong></h1>
            <p>Dear User,</p>
            <p>Thank you for confirming your account with Amassing Investment. Now it's time to set up your password and secure your access to our platform.</p>
            <p>To create your password, please click on the link below:</p>
            <p><a href="{link}">{link}</a></p>
            <p>Once you've set up your password, you'll be able to log in to your account and explore all the features and investment opportunities we offer.</p>
            <p>If you have any questions or need assistance, feel free to contact our support team at mailto:support@amassinginvestment.com. We're here to help you get started smoothly.</p>
            <p>Thank you for choosing Amassing Investment. We're excited to help you achieve your investment goals!</p>
            <p style="height: 5px;"></p>
        <p><strong>Best Regards,
        <br>The Amassing Investment Team</strong></p>
        <div style="width: 100%; background: #e5e5e5; display: flex; align-items: center; justify-content: center">
            <p style="text-align: center"><strong>PS:</strong> We hope you're enjoying your experience with us! As always, feel free to reach out to us at <a href="mailto:support@amassinginvestment.com">support@amassinginvestment.com</a>.  We'd love to hear from you.</p>
        </div>
        </body>
        </html>
        """

            # message = f"https://skyeduserve.com/register-link/{random_number}"
    print(send_email(subject="Set Up Your Amassing Investment Password", html_content=html_message, sender="Amassing Investment <noreply@amassinginvestment.com>", recipient=[data.get("email")], image_path="logo.jpg", image_name="img1"))
    

    return Response({"data" : "data saved","status" : 200})

@api_view(['POST'])
@permission_classes([AllowAny])
def setpassword(request):
    data = request.data
    token = data.get("token")

    if True:
        temp = TempTokenModel.objects.get(token = token)
        email = temp.email
        
        if User.objects.filter(email=email).exists():
            u = User.objects.get(email=email)
        else:
            u = User.objects.create(email=email)

        u.set_password(data.get("password"))
        u.save()
        return Response({"data" : "Password setup completed","status" : 200})
    # except:
    #     return Response({"data" : "Token does not exist!!","status" : 500})

def encrypted_aes(data):
    new_key = en_de_key
    data_json = json.dumps(data).encode('utf-8')
    padded_data = data_json + b"\0" * (16 - len(data_json) % 16)
    cipher = AES.new(new_key, AES.MODE_CBC, en_de_iv)
    encrypted_data = cipher.encrypt(padded_data)

    return base64.b64encode(encrypted_data).decode('utf-8')


def decrypted_aes(encrypted):
    new_key = en_de_key

    encrypted = base64.b64decode(encrypted)
    cipher = AES.new(new_key, AES.MODE_CBC, en_de_iv)
    decrypted_data = cipher.decrypt(encrypted)
    return decrypted_data.rstrip(b'\0').decode('utf-8')


def read_file_from_local(folder_name, file_name):
    home_path = os.path.expanduser("~")
    #home_path = "/home/cp1invexwealth/external_api_data/Jsons"
    home_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Jsons") #@danish
    with open(os.path.join(home_path, folder_name, file_name), "r", encoding="utf-8") as file:
        read_data = file.read()
        return json.loads(read_data)


def read_file_exists(folder_name, file_name):
    home_path = os.path.expanduser("~")
    #home_path = "/home/cp1invexwealth/external_api_data/Jsons"
    home_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Jsons")  # @danish
    file_path = os.path.join(home_path, folder_name, file_name)

    return os.path.exists(file_path)

def readDirAndGetData(folder_name):
    #home_path = "/home/cp1invexwealth/external_api_data/Jsons"
    home_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Jsons")  # @danish
    folder_path = os.path.join(home_path, folder_name)
    read_data = os.listdir(folder_path)
    
    all_data = []
    for element in read_data:
        all_data.extend(read_file_from_local(folder_name, element))

    return  all_data

@api_view(['POST'])
@permission_classes([AllowAny])
def decript_to_test_en_de(request):
    data = request.data.get("data")
    data = decrypted_aes(data).strip().replace("null", "None", 10000000000)
    data = eval(data)
    return Response({"data" : data,"status" : 200})


@api_view(['POST'])
@permission_classes([AllowAny])
def encript_given_data(request):
    data = request.data
    print(data)
    data = encrypted_aes(data)
    return Response({"data" : data,"status" : 200})


@api_view(['POST'])
@permission_classes([AllowAny])
def etf_stock_exposure(request):
    request = json.loads(json.loads(request.body))
    folder_name = "Etf Stock Exposure"
    symbol = request.get("symbol")

    file_name = f"{symbol}.json"

    if read_file_exists(folder_name, file_name):
        data = read_file_from_local(folder_name, file_name)
        if data != []:
            return Response({"data" : data,"status" : 200})
    response = requests.get(
        f"{fmp_domain}/v3/etf-stock-exposure/{symbol}?apikey={fmp_token}")
    if response.status_code == 200:
        data = response.json()
        return Response({"data" : data,"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)




@api_view(['POST'])
@permission_classes([AllowAny])
def balanceSheet(request):
    # request = json.loads(json.loads(request.body))
    request = request.data
    symbol = request.get("symbol")
    period = request.get("period")
    if not period:
        period = "annual"

    last = request.get("last")
    if not last:
        last = "5"
    if last != "max":
        folder_name = f"Bs {period} {last}y"
    else:
        folder_name = f"Bs {period} {last}"

    file_name = f"{symbol}.json"

    if read_file_exists(folder_name, file_name):
        data = read_file_from_local(folder_name, file_name)
        if data != []:
            return Response({"data" : data,"status" : 200})

    response = requests.get(
        f"{fmp_domain}/v3/balance-sheet-statement/{symbol}?period={period}&limit={last}&apikey={fmp_token}")
    if response.status_code == 200:
        data = response.json()
        return Response({"data" : data,"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)
    
@api_view(['POST'])
@permission_classes([AllowAny])
def balanceSheetLock(request):
    # request = json.loads(json.loads(request.body))
    request = request.data
    symbol = request.get("symbol")
    period = request.get("period")
    if not period:
        period = "annual"

    last = request.get("last")
    if not last:
        last = "5"
    if last != "max":
        folder_name = f"Bs {period} {last}y"
    else:
        folder_name = f"Bs {period} {last}"

    file_name = f"{symbol}.json"

    lockKeys = [
            "cashAndCashEquivalents",
            "shortTermInvestments",
            "cashAndShortTermInvestments",
            "netReceivables",
            "inventory",
            "otherCurrentAssets",
            "totalCurrentAssets",
            "propertyPlantEquipmentNet",
            "goodwill",
            "intangibleAssets",
            "goodwillAndIntangibleAssets",
            "longTermInvestments",
            "taxAssets",
            "otherNonCurrentAssets",
            "totalNonCurrentAssets",
            "otherAssets",
            "totalAssets",
            "accountPayables",
            "shortTermDebt",
            "taxPayables",
            "deferredRevenue",
            "otherCurrentLiabilities",
            "totalCurrentLiabilities",
            "longTermDebt",
            "deferredRevenueNonCurrent",
            "deferredTaxLiabilitiesNonCurrent",
            "otherNonCurrentLiabilities",
            "totalNonCurrentLiabilities",
            "otherLiabilities",
            "capitalLeaseObligations",
            "totalLiabilities",
            "preferredStock",
            "commonStock",
            "retainedEarnings",
            "accumulatedOtherComprehensiveIncomeLoss",
            "othertotalStockholdersEquity",
            "totalStockholdersEquity",
            "totalEquity",
            "totalLiabilitiesAndStockholdersEquity",
            "minorityInterest",
            "totalLiabilitiesAndTotalEquity",
            "totalInvestments",
            "totalDebt",
            "netDebt",
          ]

    if read_file_exists(folder_name, file_name):
        data = read_file_from_local(folder_name, file_name)
        if data != []:
            for i in data:
                for j in i :
                    if j in lockKeys:
                        i[j] = None
            return Response({"data" : data,"status" : 200})

    response = requests.get(
        f"{fmp_domain}/v3/balance-sheet-statement/{symbol}?period={period}&limit={last}&apikey={fmp_token}")
    if response.status_code == 200:
        data = response.json()
        for i in data:
                for j in i :
                    if j in lockKeys:
                        i[j] = None
        print(data)
        return Response({"data" : data,"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def cashFlow(request):
    request = request.data
    symbol = request.get("symbol")
    period = request.get("period")
    if not period:
        period = "annual"

    last = request.get("last")
    if not last:
        last = "5"
    if last != "max":
        folder_name = f"Cs {period} {last}y"
    else:
        folder_name = f"Cs {period} {last}"

    file_name = f"{symbol}.json"

    if read_file_exists(folder_name, file_name):
        data = read_file_from_local(folder_name, file_name)
        if data != []:
            return Response({"data" : data,"status" : 200})

    response = requests.get(
        f"{fmp_domain}/v3/cash-flow-statement/{symbol}?period={period}&limit={last}&apikey={fmp_token}")
    if response.status_code == 200:
        data = response.json()
        return Response({"data" : data,"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def cashFlowLock(request):
    # request = json.loads(json.loads(request.body))
    request = request.data
    symbol = request.get("symbol")
    period = request.get("period")
    if not period:
        period = "annual"

    last = request.get("last")
    if not last:
        last = "5"
    if last != "max":
        folder_name = f"Cs {period} {last}y"
    else:
        folder_name = f"Cs {period} {last}"

    file_name = f"{symbol}.json"
    lockKeys = [
            "netIncome",
            "depreciationAndAmortization",
            "deferredIncomeTax",
            "stockBasedCompensation",
            "changeInWorkingCapital",
            "accountsReceivables",
            "inventory",
            "accountsPayables",
            "otherWorkingCapital",
            "otherNonCashItems",
            "netCashProvidedByOperatingActivities",
            "investmentsInPropertyPlantAndEquipment",
            "acquisitionsNet",
            "purchasesOfInvestments",
            "salesMaturitiesOfInvestments",
            "otherInvestingActivites",
            "netCashUsedForInvestingActivites",
            "debtRepayment",
            "commonStockIssued",
            "commonStockRepurchased",
            "dividendsPaid",
            "otherFinancingActivites",
            "netCashUsedProvidedByFinancingActivities",
            "effectOfForexChangesOnCash",
            "netChangeInCash",
            "cashAtEndOfPeriod",
            "cashAtBeginningOfPeriod",
            "operatingCashFlow",
            "capitalExpenditure",
            "freeCashFlow",
          ]

    if read_file_exists(folder_name, file_name):
        data = read_file_from_local(folder_name, file_name)
        if data != []:
            for i in data:
                for j in i :
                    if j in lockKeys:
                        i[j] = None
            return Response({"data" : data,"status" : 200})

    response = requests.get(
        f"{fmp_domain}/v3/cash-flow-statement/{symbol}?period={period}&limit={last}&apikey={fmp_token}")
    if response.status_code == 200:
        data = response.json()
        for i in data:
            for j in i :
                if j in lockKeys:
                    i[j] = None
        return Response({"data" : data,"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)
    

@api_view(['POST'])
@permission_classes([AllowAny])
def ratiottm(request):
    request = json.loads(json.loads(request.body))
    
    symbol = request.get("symbol")
    file_name = f"{symbol}.json"
    folder_name = "Ttm cf"
    if read_file_exists(folder_name, file_name):
        data = read_file_from_local(folder_name, file_name)
        if data != []:
            return Response({"data" : data,"status" : 200})
    response = requests.get(
        f"{fmp_domain}/v3/ratios-ttm/{symbol}?apikey={fmp_token}")
    if response.status_code == 200:
        data = response.json()
        return Response({"data" : data,"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def historicalChart(request):
    request_ = json.loads(request.body)
    print(request_)
    # request_ = request.data
    symbol = request_.get("symbol")
    period = request_.get("period")
    current_date = datetime.datetime.now()
    if not period or period == "1min":
        period = "1min"
        url_dict = {"1min" : f"{fmp_domain}/v3/historical-chart/{period}/{symbol}?from={current_date}&to={current_date}&apikey={fmp_token}"}

    else:
        url_dict = {
            "1d": f"{fmp_domain}/v3/historical-chart/{period}/{symbol}?apikey={fmp_token}",
            "1w": f"{fmp_domain}/v3/historical-chart/{period}/{symbol}?from={(current_date - datetime.timedelta(weeks=1)).strftime('%Y-%m-%d')}&to={current_date}&serietype=bar&apikey={fmp_token}",
            "1m": f"{fmp_domain}/v3/historical-chart/{period}/{symbol}?from={(current_date - datetime.timedelta(days=31)).strftime('%Y-%m-%d')}&to={current_date}&serietype=bar&apikey={fmp_token}",
            "3m": f"{fmp_domain}/v3/historical-chart/{period}/{symbol}?from={(current_date - datetime.timedelta(days=92)).strftime('%Y-%m-%d')}&to={current_date}&serietype=bar&apikey={fmp_token}",
            "6m": f"{fmp_domain}/v3/historical-chart/{period}/{symbol}?from={(current_date - datetime.timedelta(days=180)).strftime('%Y-%m-%d')}&to={current_date}&serietype=bar&apikey={fmp_token}",
            "1y": f"{fmp_domain}/v3/historical-chart/{period}/{symbol}?from={(current_date - datetime.timedelta(days=365)).strftime('%Y-%m-%d')}&to={current_date}&serietype=bar&apikey={fmp_token}",
            "5y": f"{fmp_domain}/v3/historical-chart/{period}/{symbol}?from={(current_date - datetime.timedelta(days=1825)).strftime('%Y-%m-%d')}&to={current_date}&serietype=bar&apikey={fmp_token}",
            "5D": f"{fmp_domain}/v3/historical-chart/5min/{symbol}?from={(current_date - datetime.timedelta(days=7)).strftime('%Y-%m-%d')}&to={current_date}&apikey={fmp_token}",
            "1M": f"{fmp_domain}/v3/historical-chart/1day/{symbol}?from={(current_date - datetime.timedelta(days=31)).strftime('%Y-%m-%d')}&to={current_date}&apikey={fmp_token}",
            "1Y": f"{fmp_domain}/v3/historical-chart/1day/{symbol}?from={(current_date - datetime.timedelta(days=365)).strftime('%Y-%m-%d')}&to={current_date}&apikey={fmp_token}",
            "5Y": f"{fmp_domain}/v3/historical-chart/1week/{symbol}?from={(current_date - datetime.timedelta(days=1825)).strftime('%Y-%m-%d')}&to={current_date}&apikey={fmp_token}",
            "max": f"{fmp_domain}/v3/historical-chart/1week/{symbol}?from=1900-01-01&to={current_date}&apikey={fmp_token}"
        }
    try:
        resposne = requests.get(url_dict[period])
        data = resposne.json()
        return Response({"data" : data, "status" : True})
    except:
        return Response({"message" : "Something went wrong", "status" : False})


@api_view(['POST'])
@permission_classes([AllowAny])
def historicalPrice(request):
    # request_ = request.data
    request_ = json.loads(json.loads(request.body))
    symbol = request_.get("symbol")
    period = request_.get("period")
    current_date = datetime.datetime.now()

    if not period:
        period = "1d"

    url_dict = {
        "1d": f"{fmp_domain}/v3/historical-chart/{period}/{symbol}?apikey={fmp_token}",
        "1w": f"{fmp_domain}/v3/historical-chart/{period}/{symbol}?from={(current_date - datetime.timedelta(weeks=1)).strftime('%Y-%m-%d')}&to={current_date}&serietype=bar&apikey={fmp_token}",
        "1m": f"{fmp_domain}/v3/historical-chart/{period}/{symbol}?from={(current_date - datetime.timedelta(days=31)).strftime('%Y-%m-%d')}&to={current_date}&serietype=bar&apikey={fmp_token}",
        "3m": f"{fmp_domain}/v3/historical-chart/{period}/{symbol}?from={(current_date - datetime.timedelta(days=92)).strftime('%Y-%m-%d')}&to={current_date}&serietype=bar&apikey={fmp_token}",
        "6m": f"{fmp_domain}/v3/historical-chart/{period}/{symbol}?from={(current_date - datetime.timedelta(days=180)).strftime('%Y-%m-%d')}&to={current_date}&serietype=bar&apikey={fmp_token}",
        "1y": f"{fmp_domain}/v3/historical-chart/{period}/{symbol}?from={(current_date - datetime.timedelta(days=365)).strftime('%Y-%m-%d')}&to={current_date}&serietype=bar&apikey={fmp_token}",
        "5y": f"{fmp_domain}/v3/historical-chart/{period}/{symbol}?from={(current_date - datetime.timedelta(days=1825)).strftime('%Y-%m-%d')}&to={current_date}&serietype=bar&apikey={fmp_token}",
        "5D": f"{fmp_domain}/v3/historical-chart/5min/{symbol}?from={(current_date - datetime.timedelta(days=7)).strftime('%Y-%m-%d')}&to={current_date}&apikey={fmp_token}",
        "1M": f"{fmp_domain}/v3/historical-chart/1day/{symbol}?from={(current_date - datetime.timedelta(days=31)).strftime('%Y-%m-%d')}&to={current_date}&apikey={fmp_token}",
        "1Y": f"{fmp_domain}/v3/historical-chart/1day/{symbol}?from={(current_date - datetime.timedelta(days=365)).strftime('%Y-%m-%d')}&to={current_date}&apikey={fmp_token}",
        "5Y": f"{fmp_domain}/v3/historical-chart/1week/{symbol}?from={(current_date - datetime.timedelta(days=1825)).strftime('%Y-%m-%d')}&to={current_date}&apikey={fmp_token}",
        "max": f"{fmp_domain}/v3/historical-chart/1week/{symbol}?from={(current_date - datetime.timedelta(days=1)).strftime('%Y-%m-%d')}&to={current_date}&apikey={fmp_token}"
    }

    try:
        resposne = requests.get(url_dict[period])
        data = resposne.json()
        return Response({"data" : data, "status" : True})
    except:
        return Response({"message" : "Something went wrong", "status" : False})



@api_view(['POST'])
@permission_classes([AllowAny])
def incomeStatement(request):
    # request_ = json.loads(json.loads(request.body))
    request_ = request.data
    symbol = request_.get("symbol")
    period = request_.get("period")


    file_name = f"{symbol}.json"

##################################################################################################################
# Reading last 4 quarter data
    last4_quarter = ""  
    if read_file_exists("Is quarter 5y", file_name):
            data = read_file_from_local("Is quarter 5y", file_name)
            if data != []:
                last4_quarter = data[:4]
    if last4_quarter == "":
        last4_quarter = requests.get(f"{fmp_domain}/v3/income-statement/{symbol}?period=quarter&limit=4&apikey={fmp_token}").json()
    ttm1 = last4_quarter[0]
    ttm2 = last4_quarter[1]
    ttm3 = last4_quarter[2]
    ttm4 = last4_quarter[3]
    ttm = {}
    for key in ttm1.keys():
        if isinstance(ttm1[key], (int, float)):
            ttm[key] = ttm1[key] + ttm2[key] + ttm3[key] + ttm4[key]
        else:
            ttm[key] = ttm1[key] 
    ttm["is_ttm"] = True
#################################################################################################################

    if not period:
        period = "quarter"

    last = request_.get("last")
    if not last:
        last = "5"
    if last != "max":
        folder_name = f"Is {period} {last}y"
    else:
        folder_name = f"Is {period} {last}"


    if read_file_exists(folder_name, file_name):
        data = read_file_from_local(folder_name, file_name)
        if data != []:
            data.append(ttm)
            return Response({"data" : data,"status" : 200})

    response = requests.get(
        f"{fmp_domain}/v3/income-statement/{symbol}?period={period}&limit={last}&apikey={fmp_token}")
    if response.status_code == 200:
        data = response.json()
        data.append(ttm)
        return Response({"data" : data,"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def incomeStatementLock(request):
    # request_ = json.loads(json.loads(request.body))
    request_ = request.data
    symbol = request_.get("symbol")
    period = request_.get("period")


    file_name = f"{symbol}.json"

##################################################################################################################
# Reading last 4 quarter data
    last4_quarter = ""  
    if read_file_exists("Is quarter 5y", file_name):
            data = read_file_from_local("Is quarter 5y", file_name)
            if data != []:
                last4_quarter = data[:4]
    if last4_quarter == "":
        last4_quarter = requests.get(f"{fmp_domain}/v3/income-statement/{symbol}?period=quarter&limit=4&apikey={fmp_token}").json()
    ttm1 = last4_quarter[0]
    ttm2 = last4_quarter[1]
    ttm3 = last4_quarter[2]
    ttm4 = last4_quarter[3]
    ttm = {}
    for key in ttm1.keys():
        if isinstance(ttm1[key], (int, float)):
            ttm[key] = ttm1[key] + ttm2[key] + ttm3[key] + ttm4[key]
        else:
            ttm[key] = ttm1[key]  
#################################################################################################################

    if not period:
        period = "quarter"

    last = request_.get("last")
    if not last:
        last = "5"
    if last != "max":
        folder_name = f"Is {period} {last}y"
    else:
        folder_name = f"Is {period} {last}"
    lockKeys = [
            "revenue",
            "costOfRevenue",
            "grossProfit",
            "grossProfitRatio",
            "researchAndDevelopmentExpenses",
            "generalAndAdministrativeExpenses",
            "sellingAndMarketingExpenses",
            "sellingGeneralAndAdministrativeExpenses",
            "otherExpenses",
            "operatingExpenses",
            "costAndExpenses",
            "interestIncome",
            "interestExpense",
            "depreciationAndAmortization",
            "ebitda",
            "ebitdaratio",
            "operatingIncome",
            "operatingIncomeRatio",
            "totalOtherIncomeExpensesNet",
            "incomeBeforeTax",
            "incomeBeforeTaxRatio",
            "incomeTaxExpense",
            "netIncome",
            "netIncomeRatio",
            "eps",
            "epsdiluted",
            "weightedAverageShsOut",
            "weightedAverageShsOutDil",
          ]


    if read_file_exists(folder_name, file_name):
        data = read_file_from_local(folder_name, file_name)
        if data != []:
            data.append(ttm)
            for i in data:
                for j in i :
                    if j in lockKeys:
                        i[j] = None

            return Response({"data" : data,"status" : 200})

    response = requests.get(
        f"{fmp_domain}/v3/income-statement/{symbol}?period={period}&limit={last}&apikey={fmp_token}")
    if response.status_code == 200:
        data = response.json()
        data.append(ttm)
        for i in data:
            for j in i :
                if j in lockKeys:
                    i[j] = None
        return Response({"data" : data,"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def companyProfile(request):
    # request_ = json.loads(json.loads(request.body))
    request_ = request.data
    symbol = request_.get("symbol")


    if read_file_exists("", "values.json"):
        data = read_file_from_local("", "values.json")
        final_data = []
        flag = False
        if data != []:
            for symbol in symbol.split(","):
                for i in data:
                    if i.get("symbol") == symbol:
                        flag = True
                        final_data.append(i)
                        break
    if flag:
        return Response({"data": final_data, "status": True})
    
    response = requests.get(f"{fmp_domain}/v3/profile/{symbol}?apikey={fmp_token}")
    if response.status_code == 200:
        data = response.json()
        return Response({"data" : data,"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def companyOutllok(request):   
    # request_ = json.loads(json.loads(request.body))
    request_ = request.data
    symbol = request_.get("symbol")           

    response = requests.get(f"{fmp_domain}/v4/company-outlook?symbol={symbol}&apikey={fmp_token}")
    if response.status_code == 200:
        data = response.json()
        return Response({"data" : data,"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def companyQuote(request): 
    request_ = request.data
    symbol = request_.get("symbol") 

    if read_file_exists("header2_currency", f"{symbol}.json"):
        data = read_file_from_local("header2_currency", f"{symbol}.json")
        if data != []:
            return Response({"data" : data,"status" : 200})

    response = requests.get(f"{fmp_domain}/v3/quote/{symbol}?apikey={fmp_token}")
    if response.status_code == 200:
        data = response.json()
        return Response({"data" : data,"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def stockPeers(request):
    request_ = request.data
    symbol = request_.get("symbol")
    print(request_)

    if read_file_exists("Name", f"{symbol}.json"):
        data = read_file_from_local("Name", f"{symbol}.json")
        if data != []:
            return Response({"data" : data,"status" : 200})

    response = requests.get(f"{fmp_domain}/v4/stock_peers?symbol={symbol}&apikey={fmp_token}")
    if response.status_code == 200:
        data = response.json()
        return Response({"data" : data,"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500) 


@api_view(['GET'])
@permission_classes([AllowAny])
def stockMarketActives(request):
    if read_file_exists("", "header1.json"):
        data = read_file_from_local("", "header1.json")
        if data != []:
            return Response({"data" : data,"status" : 200})
        
    response = requests.get(f"{fmp_domain}/v3/stock_market/actives?apikey={fmp_token}")
    if response.status_code == 200:
        data = response.json()
        return Response({"data" : data,"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500) 



@api_view(['POST'])
@permission_classes([AllowAny])
def stockDividend(request):
    request_ = request.data
    symbol = request_.get("symbol")

    if read_file_exists("HP Stock Divident", symbol + ".json"):
        data = read_file_from_local("HP Stock Divident", symbol + ".json")
        if data != []:
            return Response({"data" : data,"status" : 200})
        
    response = requests.get(f"{fmp_domain}/v3/historical-price-full/stock_dividend/{symbol}?apikey={fmp_token}")
    if response.status_code == 200:
        data = response.json()
        return Response({"data" : data,"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)
    

@api_view(['POST'])
@permission_classes([AllowAny])
def stockDividendLock(request):
    request_ = request.data
    symbol = request_.get("symbol")

    if read_file_exists("HP Stock Divident", symbol + ".json"):
        data = read_file_from_local("HP Stock Divident", symbol + ".json")
        if data != []:
            return Response({"data" : data,"status" : 200})
        
    response = requests.get(f"{fmp_domain}/v3/historical-price-full/stock_dividend/{symbol}?apikey={fmp_token}")
    if response.status_code == 200:
        data = response.json()
        return Response({"data" : data,"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)
    
@api_view(['POST'])
@permission_classes([AllowAny])
def stockDividendLock(request):
    request_ = request.data
    symbol = request_.get("symbol")

    if read_file_exists("HP Stock Divident", symbol + ".json"):
        data = read_file_from_local("HP Stock Divident", symbol + ".json")
        if data != []:
            if len(data.get("historical")) > 10:
                data["historical"] = data.get("historical")[0:10][::-1]
            return Response({"data" : data,"status" : 200})
        
    response = requests.get(f"{fmp_domain}/v3/historical-price-full/stock_dividend/{symbol}?apikey={fmp_token}")
    if response.status_code == 200:
        data = response.json()
        if len(data.get("historical")) > 10:
            data["historical"] = data.get("historical")[0:10][::-1]
        return Response({"data" : data,"status" : 200})
        
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)
        
@api_view(['POST'])
@permission_classes([AllowAny])
def earnings(request):
    request_ = request.data
    symbol = request_.get("symbol")

    if read_file_exists("Earning Surprise", symbol + ".json"):
        data = read_file_from_local("Earning Surprise", symbol + ".json")
        if data != []:
            return Response({"data" : data,"status" : 200})
        
    response = requests.get(f"{fmp_domain}/v3/earnings-surprises/{symbol}?apikey={fmp_token}")
    if response.status_code == 200:
        data = response.json()
        return Response({"data" : data,"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)
    
@api_view(['POST'])
@permission_classes([AllowAny])
def earningsLock(request):
    request_ = request.data
    symbol = request_.get("symbol")

    if read_file_exists("Earning Surprise", symbol + ".json"):
        data = read_file_from_local("Earning Surprise", symbol + ".json")
        if data != []:
            return Response({"data" : data[0:5][::-1],"status" : 200})
            
        
    response = requests.get(f"{fmp_domain}/v3/earnings-surprises/{symbol}?apikey={fmp_token}")
    if response.status_code == 200:
        data = response.json()
        return Response({"data" : data[0:5][::-1],"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)
    

@api_view(['POST'])
@permission_classes([AllowAny])
def companyNews(request):
    request_ = request.data
    symbol = request_.get("symbol")

    if read_file_exists('', 'relates_News.json'):
        data = read_file_from_local('', 'relates_News.json')
        if data != []:
            return Response({"data" : data,"status" : 200})
        
    response = requests.get(f"{fmp_domain}/v3/stock_news?tickers={symbol}&page=0&apikey={fmp_token}")
    if response.status_code == 200:
        data = response.json()
        return Response({"data" : data,"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)
    


@api_view(['POST'])
@permission_classes([AllowAny])
def stockPriceChange(request):
    request_ = request.data
    symbol = request_.get("symbol")

    if read_file_exists("Stock Price Change",symbol + ".json"):
        data = read_file_from_local("Stock Price Change",symbol + ".json")
        if data != []:
            return Response({"data" : data,"status" : 200})

    response = requests.get(f"{fmp_domain}/v3/stock-price-change/{symbol}?apikey={fmp_token}")
    if response.status_code == 200:
        data = response.json()
        return Response({"data" : data,"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)
    
@api_view(['POST'])
@permission_classes([AllowAny])
def prePostMarketTrade(request):
    request_ = request.data
    symbol = request_.get("symbol")

    response = requests.get(f"{fmp_domain}/v4/pre-post-market-trade/{symbol}?apikey={fmp_token}")
    if response.status_code == 200:
        data = response.json()
        return Response({"data" : data,"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)
    
@api_view(['POST'])
@permission_classes([AllowAny])
def secFilings(request):
    request_ = request.data
    symbol = request_.get("symbol")
    page = request_.get("page")
    type = request_.get("type")
    query = ""
    if page:
        query += "&page=" + str(page)
    if type:
        query += "&type=" + str(type)

    if read_file_exists('SEC Filing', symbol + '.json'):
        data = read_file_from_local('SEC Filing', symbol + '.json')
        if data != []:
            return Response({"data" : data,"status" : 200})
    response = requests.get(f"{fmp_domain}/v3/sec_filings/{symbol}?apikey={fmp_token}{query}")
    if response.status_code == 200:
        data = response.json()
        return Response({"data" : data,"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)
    
@api_view(['POST'])
@permission_classes([AllowAny])
def etfStockExposure(request):
    request_ = request.data
    symbol = request_.get("symbol")

    if read_file_exists('Etf Stock Exposure', symbol + '.json'):
        data = read_file_from_local('Etf Stock Exposure', symbol + '.json')
        if data != []:
            return Response({"data" : data,"status" : 200})
    response = requests.get(f"{fmp_domain}/v3/etf-stock-exposure/{symbol}?apikey={fmp_token}")
    if response.status_code == 200:
        data = response.json()
        return Response({"data" : data,"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)
    
@api_view(['POST'])
@permission_classes([AllowAny])
def etfStockExposureLock(request):
    request_ = json.loads(request.body.decode('utf-8'))
    symbol = request_.get("symbol")

    if read_file_exists('Etf Stock Exposure', symbol + '.json'):
        data = read_file_from_local('Etf Stock Exposure', symbol + '.json')
        if data != []:
            return Response({"data" : data[0:10],"status" : 200})
    response = requests.get(f"{fmp_domain}/v3/etf-stock-exposure/{symbol}?apikey={fmp_token}")
    if response.status_code == 200:
        data = response.json()
        return Response({"data" : data[0:10],"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)
    

@api_view(['POST'])
@permission_classes([AllowAny])
def macroEconomicsEconomy(request):
    request_ = request.data
    symbol = request_.get("symbol")

    if read_file_exists('Macro Economics', symbol + '.json'):
        data = read_file_from_local('Macro Economics', symbol + '.json')
        if data != []:
            return Response({"data" : data,"status" : 200})
    response = requests.get(f"{fmp_domain}/v4/economic?name={symbol}&apikey={fmp_token}")

    if response.status_code == 200:
        try:
            data = response.json()
            return Response({"data" : data,"status" : 200})
        except:
            return Response({"error":"Data Not Found", "status" : False})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def stockMarketGainers(request):
    if read_file_exists('', 'gainer.json'):
        data = read_file_from_local('', 'gainer.json')
        if data != []:
            return Response({"data" : data,"status" : 200})
    response = requests.get(f"{fmp_domain}/v3/stock_market/gainers?apikey={fmp_token}")
    if response.status_code == 200:
        data = response.json()
        return Response({"data" : data,"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def stockMarketLosers(request):
    request_ = request.data

    if read_file_exists('', 'losers.json'):
        data = read_file_from_local('', 'losers.json')
        if data != []:
            return Response({"data" : data,"status" : 200})
    response = requests.get(f"{fmp_domain}/v3/stock_market/losers?apikey={fmp_token}")
    if response.status_code == 200:
        data = response.json()
        return Response({"data" : data,"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def stockNews(request):
    request_ = request.data
    page = request_.get("page", 0)

    if read_file_exists('', 'stock_market.json'):
        data = read_file_from_local('', 'stock_market.json')
        if data != []:
            return Response({"data" : data,"status" : 200})
    response = requests.get(f"{fmp_domain}/v3/stock_news?page={page}&apikey={fmp_token}")
    if response.status_code == 200:
        data = response.json()
        return Response({"data" : data,"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def generalNews(request):
    request_ = request.data
    page = request_.get("page", 0)

    if read_file_exists('', 'general.json'):
        data = read_file_from_local('', 'general.json')
        if data != []:
            return Response({"data" : data,"status" : 200})
    response = requests.get(f"{fmp_domain}/v4/general_news?page={page}&apikey={fmp_token}")
    if response.status_code == 200:
        data = response.json()
        return Response({"data" : data,"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def macroEconomicsCommodity(request):
    request_ = request.data
    symbol = request_.get("symbol")
    if read_file_exists("Macro Economics", symbol + ".json"):
        data = read_file_from_local("Macro Economics", symbol + ".json")
        if data != []:
            return Response({"data" : data,"status" : 200})
    response = requests.get(f"{fmp_domain}/v3/historical-price-full/{symbol}?serietype=line&apikey={fmp_token}")
    if response.status_code == 200:
        data = response.json()
        return Response({"data" : data,"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def companyQuote(request):
    request_ = request.data
    symbol = request_.get("symbol")

    if read_file_exists('header2_currency', symbol + '.json'):
        data = read_file_from_local('header2_currency', symbol + '.json')
        if data != []:
            return Response({"data" : data,"status" : 200})
    response = requests.get(f"{fmp_domain}/v3/quote/{symbol}?apikey={fmp_token}")
    if response.status_code == 200:
        data = response.json()
        return Response({"data" : data,"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)



@api_view(['POST'])
@permission_classes([AllowAny])
def statistics(request):
    try:
        request_data = request.data
        symbol = request_data.get("symbol")
        period = request_data.get("period")
        print(request_data)
        if not period:
            period = "quarter"

        last = request_data.get("last")
        if not last:
            last = "5"
        if last != "max":
            data1_filename = f"{period} cf {last}y"
            data2_filename = f"{period} ck {last}y"
        else:
            data1_filename = f"{period} cf {last}"
            data2_filename = f"{period} ck {last}"

        data = []
        ttm_data = {}

        ttm_data1 = read_file_from_local("Ttm cf", f"{symbol}.json") if read_file_exists("Ttm cf", f"{symbol}.json") else requests.get(f"{fmp_domain}/v3/ratios-ttm/{symbol}?apikey={fmp_token}").json()
        ttm_data2 = read_file_from_local("Ttm ck", f"{symbol}.json") if read_file_exists("Ttm ck", f"{symbol}.json") else requests.get(f"{fmp_domain}/v3/key-metrics-ttm/{symbol}?apikey={fmp_token}").json()

        full_ttm_data = {**ttm_data1[0], **ttm_data2[0]}

        if read_file_exists(data1_filename, f"{symbol}.json"):
            data1 = read_file_from_local(data1_filename, f"{symbol}.json")
        else:
            data1 = requests.get(f"{fmp_domain}/v3/ratios/{symbol}?period={period}&limit={last}&apikey={fmp_token}").json()

        if read_file_exists(data2_filename, f"{symbol}.json"):
            data2 = read_file_from_local(data2_filename, f"{symbol}.json")
        else:
            data2 = requests.get(f"{fmp_domain}/v3/key-metrics/{symbol}?period={period}&limit={last}&apikey={fmp_token}").json()
            
        ttmkey = [
            "assetTurnoverTTM",
      "capitalExpenditureCoverageRatioTTM",
      "cashConversionCycleTTM",
      "cashFlowCoverageRatiosTTM",
      "cashPerShareTTM",
      "cashRatioTTM",
      "currentRatioTTM",
      "daysOfInventoryOutstandingTTM",
      "daysOfPayablesOutstandingTTM",
      "daysOfSalesOutstandingTTM",
      "debtEquityRatioTTM",
      "dividendPaidAndCapexCoverageRatioTTM",
      "payoutRatioTTM",
      "dividendYieldTTM",
      "ebtPerEbitTTM",
      "effectiveTaxRateTTM",
      "enterpriseValueMultipleTTM",
      "fixedAssetTurnoverTTM",
      "freeCashFlowOperatingCashFlowRatioTTM",
      "freeCashFlowPerShareTTM",
      "grossProfitMarginTTM",
      "interestCoverageTTM",
      "inventoryTurnoverTTM",
      "longTermDebtToCapitalizationTTM",
      "netIncomePerEBTTTM",
      "netProfitMarginTTM",
      "operatingCashFlowPerShareTTM",
      "operatingCashFlowSalesRatioTTM",
      "operatingCycleTTM",
      "operatingProfitMarginTTM",
      "payablesTurnoverTTM",
      "pretaxProfitMarginTTM",
      "priceEarningsRatioTTM",
      "priceEarningsToGrowthRatioTTM",
      "priceToBookRatioTTM",
      "priceToFreeCashFlowsRatioTTM",
      "priceToOperatingCashFlowsRatioTTM",
      "priceToSalesRatioTTM",
      "quickRatioTTM",
      "receivablesTurnoverTTM",
      "returnOnAssetsTTM",
      "returnOnCapitalEmployedTTM",
      "returnOnEquityTTM",
      "shortTermCoverageRatiosTTM",
      "totalDebtToCapitalizationTTM",
      "bookValuePerShareTTM",
      "capexPerShareTTM",
      "capexToDepreciationTTM",
      "capexToOperatingCashFlowTTM",
      "capexToRevenueTTM",
      "debtToAssetsTTM",
      "earningsYieldTTM",
      "enterpriseValueTTM",
      "evToFreeCashFlowTTM",
      "evToOperatingCashFlowTTM",
      "evToSalesTTM",
      "freeCashFlowYieldTTM",
      "grahamNumberTTM",
      "incomeQualityTTM",
      "intangiblesToTotalAssetsTTM",
      "interestDebtPerShareTTM",
      "investedCapitalTTM",
      "marketCapTTM",
      "netCurrentAssetValueTTM",
      "netDebtToEBITDATTM",
      "netIncomePerShareTTM",
      "researchAndDdevelopementToRevenueTTM",
      "returnOnTangibleAssetsTTM",
      "revenuePerShareTTM",
      "salesGeneralAndAdministrativeToRevenueTTM",
      "stockBasedCompensationToRevenueTTM",
      "tangibleAssetValueTTM",
      "tangibleBookValuePerShareTTM",
      "workingCapitalTTM",
            ]

        ttm_data = {}

        for key in ttmkey:
            new_key = key[:-3]
            ttm_data[new_key] = full_ttm_data.get(key, None)

        data = []

        for i in range(len(data1)):
            ob = {}
            full_ob = {**data1[i], **data2[i]}
            
            keys = [
                "symbol",
            "date",
            "period",
            "assetTurnover",
            "capitalExpenditureCoverageRatio",
            "cashConversionCycle",
            "cashFlowCoverageRatios",
            "cashPerShare",
            "cashRatio",
            "currentRatio",
            "daysOfInventoryOutstanding",
            "daysOfPayablesOutstanding",
            "daysOfSalesOutstanding",
            "debtEquityRatio",
            "dividendPaidAndCapexCoverageRatio",
            "dividendPayoutRatio",
            "dividendYield",
            "ebtPerEbit",
            "effectiveTaxRate",
            "enterpriseValueMultiple",
            "fixedAssetTurnover",
            "freeCashFlowOperatingCashFlowRatio",
            "freeCashFlowPerShare",
            "grossProfitMargin",
            "interestCoverage",
            "inventoryTurnover",
            "longTermDebtToCapitalization",
            "netIncomePerEBT",
            "netProfitMargin",
            "operatingCashFlowPerShare",
            "operatingCashFlowSalesRatio",
            "operatingCycle",
            "operatingProfitMargin",
            "payablesTurnover",
            "pretaxProfitMargin",
            "priceEarningsRatio",
            "priceEarningsToGrowthRatio",
            "priceToBookRatio",
            "priceToFreeCashFlowsRatio",
            "priceToOperatingCashFlowsRatio",
            "priceToSalesRatio",
            "quickRatio",
            "receivablesTurnover",
            "returnOnAssets",
            "returnOnCapitalEmployed",
            "returnOnEquity",
            "shortTermCoverageRatios",
            "totalDebtToCapitalization",
            "bookValuePerShare",
            "capexPerShare",
            "capexToDepreciation",
            "capexToOperatingCashFlow",
            "capexToRevenue",
            "debtToAssets",
            "earningsYield",
            "enterpriseValue",
            "evToFreeCashFlow",
            "evToOperatingCashFlow",
            "evToSales",
            "freeCashFlowYield",
            "grahamNumber",
            "incomeQuality",
            "intangiblesToTotalAssets",
            "interestDebtPerShare",
            "investedCapital",
            "marketCap",
            "netCurrentAssetValue",
            "netDebtToEBITDA",
            "netIncomePerShare",
            "researchAndDdevelopementToRevenue",
            "returnOnTangibleAssets",
            "revenuePerShare",
            "salesGeneralAndAdministrativeToRevenue",
            "stockBasedCompensationToRevenue",
            "tangibleAssetValue",
            "tangibleBookValuePerShare",
            "workingCapital",
            ]

            for key in keys:
                ob[key] = full_ob.get(key, None)

            data.append(ob)
        return Response({
            'ttmData': {'dividendPayoutRatio': ttm_data.get('payoutRatio', None), **ttm_data},
            'data': data,
        })
    except Exception as e:
        print("error", e)
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)



@api_view(['POST'])
@permission_classes([AllowAny])
def statisticsLock(request):
    try:
        request_data = request.data
        symbol = request_data.get("symbol")
        period = request_data.get("period")
        if not period:
            period = "quarter"

        last = request_data.get("last")
        if not last:
            last = "5"
        if last != "max":
            data1_filename = f"{period} cf {last}y"
            data2_filename = f"{period} ck {last}y"
        else:
            data1_filename = f"{period} cf {last}"
            data2_filename = f"{period} ck {last}"

        data = []
        ttm_data = {}

        ttm_data1 = read_file_from_local("Ttm cf", f"{symbol}.json") if read_file_exists("Ttm cf", f"{symbol}.json") else requests.get(f"{fmp_domain}/v3/ratios-ttm/{symbol}?apikey={fmp_token}").json()
        ttm_data2 = read_file_from_local("Ttm ck", f"{symbol}.json") if read_file_exists("Ttm ck", f"{symbol}.json") else requests.get(f"{fmp_domain}/v3/key-metrics-ttm/{symbol}?apikey={fmp_token}").json()

        full_ttm_data = {**ttm_data1[0], **ttm_data2[0]}

        if read_file_exists(data1_filename, f"{symbol}.json"):
            data1 = read_file_from_local(data1_filename, f"{symbol}.json")
        else:
            data1 = requests.get(f"{fmp_domain}/v3/ratios/{symbol}?period={period}&limit={last}&apikey={fmp_token}").json()

        if read_file_exists(data2_filename, f"{symbol}.json"):
            data2 = read_file_from_local(data2_filename, f"{symbol}.json")
        else:
            data2 = requests.get(f"{fmp_domain}/v3/key-metrics/{symbol}?period={period}&limit={last}&apikey={fmp_token}").json()
            
        ttmkey = [
            "assetTurnoverTTM",
      "capitalExpenditureCoverageRatioTTM",
      "cashConversionCycleTTM",
      "cashFlowCoverageRatiosTTM",
      "cashPerShareTTM",
      "cashRatioTTM",
      "currentRatioTTM",
      "daysOfInventoryOutstandingTTM",
      "daysOfPayablesOutstandingTTM",
      "daysOfSalesOutstandingTTM",
      "debtEquityRatioTTM",
      "dividendPaidAndCapexCoverageRatioTTM",
      "payoutRatioTTM",
      "dividendYieldTTM",
      "ebtPerEbitTTM",
      "effectiveTaxRateTTM",
      "enterpriseValueMultipleTTM",
      "fixedAssetTurnoverTTM",
      "freeCashFlowOperatingCashFlowRatioTTM",
      "freeCashFlowPerShareTTM",
      "grossProfitMarginTTM",
      "interestCoverageTTM",
      "inventoryTurnoverTTM",
      "longTermDebtToCapitalizationTTM",
      "netIncomePerEBTTTM",
      "netProfitMarginTTM",
      "operatingCashFlowPerShareTTM",
      "operatingCashFlowSalesRatioTTM",
      "operatingCycleTTM",
      "operatingProfitMarginTTM",
      "payablesTurnoverTTM",
      "pretaxProfitMarginTTM",
      "priceEarningsRatioTTM",
      "priceEarningsToGrowthRatioTTM",
      "priceToBookRatioTTM",
      "priceToFreeCashFlowsRatioTTM",
      "priceToOperatingCashFlowsRatioTTM",
      "priceToSalesRatioTTM",
      "quickRatioTTM",
      "receivablesTurnoverTTM",
      "returnOnAssetsTTM",
      "returnOnCapitalEmployedTTM",
      "returnOnEquityTTM",
      "shortTermCoverageRatiosTTM",
      "totalDebtToCapitalizationTTM",
      "bookValuePerShareTTM",
      "capexPerShareTTM",
      "capexToDepreciationTTM",
      "capexToOperatingCashFlowTTM",
      "capexToRevenueTTM",
      "debtToAssetsTTM",
      "earningsYieldTTM",
      "enterpriseValueTTM",
      "evToFreeCashFlowTTM",
      "evToOperatingCashFlowTTM",
      "evToSalesTTM",
      "freeCashFlowYieldTTM",
      "grahamNumberTTM",
      "incomeQualityTTM",
      "intangiblesToTotalAssetsTTM",
      "interestDebtPerShareTTM",
      "investedCapitalTTM",
      "marketCapTTM",
      "netCurrentAssetValueTTM",
      "netDebtToEBITDATTM",
      "netIncomePerShareTTM",
      "researchAndDdevelopementToRevenueTTM",
      "returnOnTangibleAssetsTTM",
      "revenuePerShareTTM",
      "salesGeneralAndAdministrativeToRevenueTTM",
      "stockBasedCompensationToRevenueTTM",
      "tangibleAssetValueTTM",
      "tangibleBookValuePerShareTTM",
      "workingCapitalTTM",
            ]

        ttm_data = {}

        for key in ttmkey:
            new_key = key[:-3]
            ttm_data[new_key] = full_ttm_data.get(key, None)

        data = []

        for i in range(len(data1)):
            ob = {}
            full_ob = {**data1[i], **data2[i]}
            
            keys = [
                "symbol",
            "date",
            "period",
            "assetTurnover",
            "capitalExpenditureCoverageRatio",
            "cashConversionCycle",
            "cashFlowCoverageRatios",
            "cashPerShare",
            "cashRatio",
            "currentRatio",
            "daysOfInventoryOutstanding",
            "daysOfPayablesOutstanding",
            "daysOfSalesOutstanding",
            "debtEquityRatio",
            "dividendPaidAndCapexCoverageRatio",
            "dividendPayoutRatio",
            "dividendYield",
            "ebtPerEbit",
            "effectiveTaxRate",
            "enterpriseValueMultiple",
            "fixedAssetTurnover",
            "freeCashFlowOperatingCashFlowRatio",
            "freeCashFlowPerShare",
            "grossProfitMargin",
            "interestCoverage",
            "inventoryTurnover",
            "longTermDebtToCapitalization",
            "netIncomePerEBT",
            "netProfitMargin",
            "operatingCashFlowPerShare",
            "operatingCashFlowSalesRatio",
            "operatingCycle",
            "operatingProfitMargin",
            "payablesTurnover",
            "pretaxProfitMargin",
            "priceEarningsRatio",
            "priceEarningsToGrowthRatio",
            "priceToBookRatio",
            "priceToFreeCashFlowsRatio",
            "priceToOperatingCashFlowsRatio",
            "priceToSalesRatio",
            "quickRatio",
            "receivablesTurnover",
            "returnOnAssets",
            "returnOnCapitalEmployed",
            "returnOnEquity",
            "shortTermCoverageRatios",
            "totalDebtToCapitalization",
            "bookValuePerShare",
            "capexPerShare",
            "capexToDepreciation",
            "capexToOperatingCashFlow",
            "capexToRevenue",
            "debtToAssets",
            "earningsYield",
            "enterpriseValue",
            "evToFreeCashFlow",
            "evToOperatingCashFlow",
            "evToSales",
            "freeCashFlowYield",
            "grahamNumber",
            "incomeQuality",
            "intangiblesToTotalAssets",
            "interestDebtPerShare",
            "investedCapital",
            "marketCap",
            "netCurrentAssetValue",
            "netDebtToEBITDA",
            "netIncomePerShare",
            "researchAndDdevelopementToRevenue",
            "returnOnTangibleAssets",
            "revenuePerShare",
            "salesGeneralAndAdministrativeToRevenue",
            "stockBasedCompensationToRevenue",
            "tangibleAssetValue",
            "tangibleBookValuePerShare",
            "workingCapital",
            ]

            for key in keys:
                ob[key] = full_ob.get(key, None)

            data.append(ob)
            lockKeys = [
      "enterpriseValueMultiple",
      "evToFreeCashFlow",
      "evToOperatingCashFlow",
      "evToSales",
      "grahamNumber",
      "priceEarningsRatio",
      "priceEarningsToGrowthRatio",
      "priceToBookRatio",
      "priceToFreeCashFlowsRatio",
      "priceToOperatingCashFlowsRatio",
      "priceToSalesRatio",
      "assetTurnover",
      "fixedAssetTurnover",
      "inventoryTurnover",
      "payablesTurnover",
      "receivablesTurnover",
      "returnOnAssets",
      "returnOnCapitalEmployed",
      "returnOnEquity",
      "returnOnTangibleAssets",
      "ebtPerEbit",
      "grossProfitMargin",
      "netIncomePerEBT",
      "netProfitMargin",
      "operatingProfitMargin",
      "pretaxProfitMargin",
      "researchAndDevelopmentToRevenue",
      "salesGeneralAndAdministrativeToRevenue",
      "cashFlowCoverageRatios",
      "debtEquityRatio",
      "debtToAssets",
      "interestCoverage",
      "interestDebtPerShare",
      "longTermDebtToCapitalization",
      "netDebtToEBITDA",
      "shortTermCoverageRatios",
      "totalDebtToCapitalization",
      "cashConversionCycle",
      "cashPerShare",
      "cashRatio",
      "currentRatio",
      "daysOfInventoryOutstanding",
      "daysOfPayablesOutstanding",
      "daysOfSalesOutstanding",
      "operatingCycle",
      "quickRatio",
      "dividendPaidAndCapexCoverageRatio",
      "dividendPayoutRatio",
      "dividendYield",
      "earningsYield",
      "netIncomePerShare",
      "freeCashFlowOperatingCashFlowRatio",
      "freeCashFlowPerShare",
      "freeCashFlowYield",
      "incomeQuality",
      "operatingCashFlowPerShare",
      "operatingCashFlowSalesRatio",
    ]
            for i in data:
                for j in i :
                    if j in lockKeys:
                        i[j] = None
            return Response({
                'ttmData': {'dividendPayoutRatio': ttm_data.get('payoutRatio', None), **ttm_data},
                'data': data,
            })
    except Exception as e:
        print("error", e)
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)





@api_view(['POST'])
@permission_classes([AllowAny])
def historicalPriceWithDate(request):
    request_data = request.data
    symbol = request_data.get("symbol")
    period = request_data.get("period")
    date_to = datetime.datetime.now()


    if period == "1d":
        return requests.get(f"{fmp_domain}/v3/historical-chart/1min/{symbol}?apikey={fmp_token}").json()
    elif period == "1w" or period == "1m" or period == "3m" or period == "6m" or period == "1y" or period == "5y" or period == "max":
        if period == "1w":
            from_date = from_date = (date_to - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        elif period == "1m":
            from_date = (date_to - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        elif period == "3m":
            from_date = (date_to - datetime.timedelta(days=90)).strftime("%Y-%m-%d")
        elif period == "6m":
            from_date = (date_to - datetime.timedelta(days=180)).strftime("%Y-%m-%d")
        elif period == "1y":
            from_date = (date_to - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
        elif period == "5y":
            from_date = (date_to - datetime.timedelta(days=5*365)).strftime("%Y-%m-%d")
        elif period == "max":
            from_date = (date_to - datetime.timedelta(days=30*365)).strftime("%Y-%m-%d")
            
        response =  requests.get(f"{fmp_domain}/v3/historical-price-full/{symbol}?from={from_date}&to={date_to}&serietype=bar&apikey={fmp_token}")
    else:
        response =  requests.get(f"{fmp_domain}/v3/historical-chart/1min/{symbol}?apikey={fmp_token}")

    if response.status_code == 200:
        data = response.json()
        return Response({"data" : data,"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)
    


@api_view(['GET'])
@permission_classes([AllowAny])
def header2(request):
    currency = readDirAndGetData('header2_currency')

    index = None
    if read_file_exists('', 'header2_index.json'):
        index = read_file_from_local('', 'header2_index.json')
        index = [i for i in index if i["symbol"] in ["^TNX","^VIX","^DJI","^IXIC","^GSPC","^FTSE","^RUT","^HSI","^N225"]]
    else:
        index = requests.get(f"{fmp_domain}/v3/quote/%5ETNX,%5EVIX,%5EDJI,%5EIXIC,%5EGSPC,%5EFTSE,%5ERUT,%5EHSI?apikey={fmp_token}").json()
    
    commodity = None
    if read_file_exists('', 'header2_commodity.json'):
        commodity = read_file_from_local('', 'header2_commodity.json')
        commodity = [i for i in commodity if i["symbol"] in ["PLUSD","CTUSX","NGUSD","CLUSD","HOUSD","ZGUSD"]]
    else:
        commodity = requests.get(f"{fmp_domain}/v3/quote/PLUSD,CTUSX,NGUSD,CLUSD,HOUSD,ZGUSD?apikey={fmp_token}").json()
    
    res = json.dumps({"data":{ "index": index, "currency": currency, "commodity": commodity }, "status" : 200})
    return HttpResponse(res,content_type = "application/json")


@api_view(['POST'])
@permission_classes([AllowAny])
def earning_calendar(request):
    period = request.data.get("period", "default")
    from_date = datetime.datetime.now()
    if period == "this_month":
        last_day_of_month = calendar.monthrange(from_date.year, from_date.month)[1]
        to = from_date.replace(day=last_day_of_month)
    elif period == "next_month":
        last_day_of_month = calendar.monthrange(from_date.year, from_date.month)[1]
        to = from_date.replace(day=last_day_of_month)
        to = to + datetime.timedelta(days=31)
    else:
        days_until_end_of_week = 6 - from_date.weekday() 
        to = from_date + datetime.timedelta(days=days_until_end_of_week)

    if read_file_exists('', 'Earning_calendar.json'):
        data = read_file_from_local('', 'Earning_calendar.json')
        if data != []:
            found = [item for item in data if from_date < datetime.datetime.strptime(item['date'], '%Y-%m-%d') < to]
            if found:
                return Response({"data" : found,"status" : 200})

        response = requests.get(f"{fmp_domain}/v4/earning-calendar-confirmed?from={from_date.strftime('%Y-%m-%d')}&to={to.strftime('%Y-%m-%d')}&apikey={fmp_token}")
        if response.status_code == 200:
            data = response.json()
            return Response({"data" : data,"status" : 200})
        else:
            return JsonResponse({"error": "Failed to retrieve data"}, status=500)
                
i=0
today_date = date.today()
while True:
    if i > 0:
        today_date = today_date - timedelta(days=1)
        # date_string = str(today_date).split(" ")[0].replace("-", "")
    try: 
        curr_date = str(today_date).replace('-', '')
        #search_df = pd.read_csv(f'/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/screener_data/screener_{curr_date}.csv', usecols=["companyName", "exchangeShortName", "exchange", "symbol"])
        base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Media","screener_data")
        csv_file = os.path.join(base_path, f"screener_{curr_date}.csv")
        search_df = pd.read_csv(csv_file, usecols=["companyName", "exchangeShortName", "exchange", "symbol"]) #@danish

        # screener_data = pd.read_csv('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/screener_data/screener_'+str(curr_date)+'.csv')
        break
    except:
        i = i + 1

@api_view(['GET'])
@permission_classes([AllowAny])
def search(request):   
    # keyword = request.GET.get("keyword")
    # print(f"{fmp_domain}/v3/search-ticker?query={keyword}&apikey={fmp_token}")
    # response = requests.get(f"{fmp_domain}/v3/search-ticker?query={keyword}&apikey={fmp_token}")
    # if response.status_code == 200:
    #     data = response.json()
    #     return Response({"data" : data,"status" : 200})
    # else:
    #     return JsonResponse({"error": "Failed to retrieve data"}, status=500)
    keyword = request.GET.get("keyword")
    
    # df = pd.read_csv("screener_20240620.csv")

    # df = df[["companyName", "exchangeShortName", "exchange", "symbol"]]
    df = search_df[(search_df["companyName"].str.contains(keyword, regex=True, case=False)) | (search_df["symbol"].str.contains(keyword, regex=True, case=False))]
    df["exact_match"] = df["symbol"].str.lower() == keyword.lower()

    # Sort by the exact match column (descending) and then by symbol
    df = df.sort_values(by=["exact_match", "symbol"], ascending=[False, True])

    # Drop the helper column
    df = df.drop(columns=["exact_match"])

    return HttpResponse(json.dumps(df.to_dict("records"), indent=4, default=str), content_type="application/json")
    
@api_view(['POST'])
@permission_classes([AllowAny])
def companyProfileQuoteMultiple(request): 
    symbol = request.data.get("symbols")
    print(symbol)
    flag=False
    # company Profile
    if read_file_exists("", "values.json"):
        data = read_file_from_local("", "values.json")
        if data != []:
            data_profile = []
            for i in data:
                if i.get("symbol") in symbol.split(","):
                    data_profile.append(i)  
                else:
                    flag=True
                    break
    else:
        flag=False
    if flag:
        response = requests.get(f"{fmp_domain}/v3/profile/{symbol}?apikey={fmp_token}")
        if response.status_code == 200:
            data_profile = response.json()

    if read_file_exists("header2_currency", f"{symbol}.json"):
        data_quote = read_file_from_local("header2_currency", f"{symbol}.json")
    else:
        response = requests.get(f"{fmp_domain}/v3/quote/{symbol}?apikey={fmp_token}")
        if response.status_code == 200:
            data_quote = response.json()

    # ratiottm

    if read_file_exists("Ttm cf", symbol + ".json"):
        data_ttm_cf = read_file_from_local("Ttm cf", symbol + ".json")
    else:
        response = requests.get(f"{fmp_domain}/v3/ratios-ttm/{symbol}?apikey={fmp_token}")
        if response.status_code == 200:
            data_ttm_cf = response.json()

    if type(data_ttm_cf) != list:
            data_ttm_cf = [data_ttm_cf]

    # stockDividend

    if read_file_exists("HP Stock Divident", symbol + ".json"):
        data_sd = read_file_from_local("HP Stock Divident", symbol + ".json")
    else: 
        response = requests.get(f"{fmp_domain}/v3/historical-price-full/stock_dividend/{symbol}?apikey={fmp_token}")
        if response.status_code == 200:
            data_sd = response.json()

    # stockPriceChange

    if read_file_exists("Stock Price Change",symbol + ".json"):
        data_spc = read_file_from_local("Stock Price Change",symbol + ".json")
    else:
        response = requests.get(f"{fmp_domain}/v3/stock-price-change/{symbol}?apikey={fmp_token}")
        if response.status_code == 200:
            data_spc = response.json()
    
    if type(data_spc) != list:
            data_spc = [data_spc]

    # pre post market trade
    final_list = []
    for i in data_profile:
        main_data = {}
        symbol_curr = i.get("symbol")
        response = requests.get(f"{fmp_domain}/v4/pre-post-market-trade/{symbol_curr}?apikey={fmp_token}")
        if response.status_code == 200:
            main_data["prePostMarketTrade"] = response.json()
        found_data2 = next((ite for ite in data_quote if ite['symbol'] == symbol_curr), None)
        if found_data2:
            main_data.update(found_data2)
        foundData5 = next((ite for ite in data_spc if ite['symbol'] == symbol_curr), None)
        if foundData5:
            main_data['stockPriceChange'] = foundData5
        
        foundData3 = next((ite for ite in data_ttm_cf if ite.get('symbol') == symbol_curr), None)
        if foundData3:
            main_data.update({
                'dividendPerShareTTM': foundData3['dividendPerShareTTM'],
                'enterpriseValueMultipleTTM': foundData3['enterpriseValueMultipleTTM'],
                'priceToBookRatioTTM': foundData3['priceToBookRatioTTM'],
            })
        date = "-"
        if data_sd and 'historicalStockList' in data_sd and data_sd['historicalStockList']:
            foundData4 = next((ite for ite in data_sd['historicalStockList'] if ite['symbol'] == symbol_curr), None)
            if foundData4 and 'historical' in foundData4 and foundData4['historical']:
                date = foundData4['historical'][0]['date']
            main_data['exDividendDate'] = date

        final_list.append(main_data)
    return Response({"data" : final_list,"status" : 200})



# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def addProfile(request):
#     data = request.data
#     email = request.email
#     if User.objects.filter(email = email).exists():
#         return Response({"message" : "EmailId is already registered with another account.","status":True}, status=status.HTTP_202_ACCEPTED)
#     else:
#         try:
#             User.objects.create(**data)
#             return Response({"message" : "Your profile added successfully.", "status" : True}, status=status.HTTP_201_CREATED)
#         except Exception as e:
#             print(str(e))
#             return Response({"message" : "Something went wrong", "status" : False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def viewProfile(request,id):
#     if User.objects.filter(id = id).exists():
#         user = User.objects.get(id = id)
#         data = UserCustomSerializer(user,fields = ["id","email","firstName","middleName","lastName","mobile","bod","addressLine1","addressLine2","pincode","city","state","country"])
#         return Response({"data": data.data, "message" : "User profile successfully.","status":True}, status=status.HTTP_200_OK)
#     else:
#         return Response({"message" : "Data not found.", "status" : False}, status=status.HTTP_404_NOT_FOUND)

# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def fetchUserDcfCalculatorFilter(request):
#     user_id = request.data.user_id
#     if UserDcfCalculatorFilter.objects.filter(user__id = user_id).exists():
#         user_data = UserDcfCalculatorFilter.objects.filter(user__id = user_id)
#         data = UserDcfCalculatorFilterSerializer(user_data)
#         return Response({"data":data.data, "message":"Your list of dcf calculator filter successfully.","status":202, "success":True})
#     else:
#         return Response({"message":"Data not found.","status":404,"success":False})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fetchUserDcfCalculatorFilter(request):
    try:
        data = request.data
        user_id = data.get('user_id')
        user_dcf_calculator_filters = UserDcfCalculatorFilter.objects.filter(user__id=user_id)
        if user_dcf_calculator_filters:
            response_data = [{"dcf_calculator_filter_name": item.dcf_calculator_filter_name, "filter_values": item.filter_values} for item in user_dcf_calculator_filters]
            return JsonResponse({"message": "Your list of DCF calculator filters successfully.", "data": response_data, "status": 202, "success": True})
        else:
            return JsonResponse({"message": "Data not found.", "data": [], "status": 404, "success": False})

    except Exception as e:
        return JsonResponse({"message": "Failed to fetch user DCF calculator filters", "status": 500, "success": False})

# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def fetchUserScreenerFilter(request):
#     user_id = request.data.user_id
#     if UserScreenerFilter.objects.filter(user__id = user_id).exists():
#         user_data = UserScreenerFilter.objects.filter(user__id = user_id)
#         data = UserScreenerFilterSerializer(user_data)
#         return Response({"data":data.data, "message":"Your list of screener filter successfully.","status":202, "success":True})
#     else:
#         return Response({"message":"Data not found.","status":404,"success":False})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fetchUserScreenerFilter(request):
    try:
        data = request.data
        user_id = data.get('user_id')
        user_screener_filters = UserScreenerFilter.objects.filter(user__id=user_id)

        if user_screener_filters:
            response_data = [{"screener_name": item.screener_name, "filter_values": item.filter_values} for item in user_screener_filters]
            return JsonResponse({"message": "Your list of screener filters successfully.", "data": response_data, "status": 202, "success": True})
        else:
            return JsonResponse({"message": "Data not found.", "data": [], "status": 404, "success": False})

    except Exception as e:
        return JsonResponse({"message": "Failed to fetch user screener filters", "status": 500, "success": False})



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def storeUserPortfolio(request):
    print(request.user)
    if True:
        data = request.data

        user_id = data.get('user_id')
        portfolio_id = data.get('portfolio_id')
        portfolio_name = data.get('portfolio_name')
        portfolio_slug = data.get('portfolio_slug')
        reinvesting_dividends = data.get('reinvesting_dividends')
        currency = data.get('currency')
        portfolio_description = data.get('portfolio_description')
        ticker_values = data.get('ticker_values')

        if UserPortfolio.objects.filter(user_id=user_id, id=portfolio_id).exists():
            user_portfolio = UserPortfolio.objects.get(user_id=user_id, id=portfolio_id)
            user_portfolio.portfolio_name = portfolio_name
            user_portfolio.reinvesting_dividends = reinvesting_dividends
            user_portfolio.currency = currency
            user_portfolio.portfolio_description = portfolio_description
            user_portfolio.ticker_values = ticker_values
            user_portfolio.portfolio_slug = portfolio_slug
            user_portfolio.save()
            return JsonResponse({"message": "Your Portfolio updated successfully.", "status": 201, "success": True})
        
        else:
            UserPortfolio.objects.create(
                portfolio_name=portfolio_name,
                reinvesting_dividends=reinvesting_dividends,
                currency=currency,
                portfolio_description=portfolio_description,
                ticker_values=ticker_values,
                portfolio_slug=portfolio_slug,
                user_id=user_id
            )

            return JsonResponse({"message": "Your Portfolio added successfully.", "status": 201, "success": True})

    # except Exception as e:
    #     return JsonResponse({"message": "Failed to edit profile", "status": 500, "success": False})

@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def storeUserDcfCalculatorFilter(request):
    try:
        data = request.data
        user_id = data.get('user_id')
        dcf_calculator_filter_name = data.get('dcf_calculator_filter_name')
        
        if  data.get('isDelete', False):
            if UserDcfCalculatorFilter.objects.filter(user_id=user_id, dcf_calculator_filter_name=dcf_calculator_filter_name).exists():
                u = UserDcfCalculatorFilter.objects.get(user_id=user_id, dcf_calculator_filter_name=dcf_calculator_filter_name)
                u.delete()
                return JsonResponse({"message": "Entry Deleted Successfully.", "status": 201, "success": True})
            return JsonResponse({"message": "Not Found", "status": 400, "success": False})
        filters = json.dumps(data.get('filters'))

        user_dcf_calculator_filter = UserDcfCalculatorFilter.objects.filter(
            user_id=user_id, dcf_calculator_filter_name=dcf_calculator_filter_name
        ).first()

        if user_dcf_calculator_filter:
            user_dcf_calculator_filter.dcf_calculator_filter_name = dcf_calculator_filter_name
            user_dcf_calculator_filter.filter_values = filters
            user_dcf_calculator_filter.save()

            return JsonResponse({"message": "Your DCF calculator filter updated successfully.", "status": 201, "success": True})

        else:
            UserDcfCalculatorFilter.objects.create(
                dcf_calculator_filter_name=dcf_calculator_filter_name,
                filter_values=filters,
                user_id=user_id
            )

            return JsonResponse({"message": "Your DCF calculator filter added successfully.", "status": 201, "success": True})

    except Exception as e:
        return JsonResponse({"message": "Failed to save User DCF Calculator Filter", "status": 500, "success": False})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def storeUserScreenerFilter(request):
    if True:
        data = request.data
        user_id = data.get('user_id')
        screener = data.get('screener')
        filters = data.get('filters')

        user_screener_filter = UserScreenerFilter.objects.filter(
            user_id=user_id, screener_name=screener
        ).first()

        if user_screener_filter:
            user_screener_filter.screener_name = screener
            user_screener_filter.filter_values = json.dumps(filters)
            user_screener_filter.save()

            return JsonResponse({"message": "Your screener filter updated successfully.", "status": 201, "success": True})

        else:
            UserScreenerFilter.objects.create(
                screener_name=screener,
                filter_values=json.dumps(filters),
                user_id=user_id
            )

            return JsonResponse({"message": "Your screener filter added successfully.", "status": 201, "success": True})

    # except Exception as e:
    #     return JsonResponse({"message": "Failed to edit profile", "status": 500, "success": False})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def listOfCourse(request):
    try:
        # Retrieve distinct courses
        course_data = Course.objects.values(
            'courseId', 'courseName', 'author', 'courseDescription', 'image'
        ).distinct()

        # Serialize the data
        serializer = CourseSerializer(course_data, many=True, fields = ['courseId', 'courseName', 'author', 'courseDescription', 'image'])

        # Return the response
        if serializer.data:
            return Response(
                {
                    'message': 'Your list of courses successfully.',
                    'data': serializer.data,
                    'status': 1
                },
                status=status.HTTP_202_ACCEPTED
            )
        else:
            return Response(
                {'message': 'Data not found.', 'data': [], 'status': 0},
                status=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        return Response(
            {'message': 'Failed to list courses.', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def listOfChapter(request, id):
    try:
        # Retrieve chapter data for a specific course
        chapter_data = Course.objects.filter(courseId=id).values('courseId', 'chapterName', 'materials')

        # Serialize the data
        serializer = CourseSerializer(chapter_data, many=True, fields = ['courseId', 'courseName', 'author', 'courseDescription', 'image'])

        # Return the response
        if serializer.data:
            result = []
            for item in serializer.data:
                data = item['materials']  # Assuming materials is a JSON field
                result.append({
                    'courseId': item['courseId'],
                    'chapterName': item['chapterName'],
                    'materials': data,
                })

            return JsonResponse(
                {
                    'message': 'Your list of chapters successfully.',
                    'data': result,
                    'status': 1
                },
                status=status.HTTP_202_ACCEPTED
            )
        else:
            return JsonResponse(
                {'message': 'Data not found.', 'data': [], 'status': 0},
                status=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        return JsonResponse(
            {'message': 'Failed to list chapters.', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fetchUserPortfolioLists(request):
    if True:
        user_id = request.data.get('user_id')
        if user_id is None:
            return JsonResponse(
                {'message': 'user_id is required in the request data.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Retrieve user portfolio data for a specific user
        user_portfolio_data = UserPortfolio.objects.filter(user_id=user_id).values()

        # Serialize the data
        serializer = UserPortfolioSerializer(user_portfolio_data, many=True, fields=["portfolio_name", "portfolio_id", "portfolio_slug", "header_title", "header_description", "ticker_values", "description", "image_url","id"])

        # Return the response
        if serializer.data:
            return JsonResponse(
                {
                    'message': 'Your list of user portfolio fetched successfully.',
                    'data': serializer.data,
                    'status': 1
                },
                status=status.HTTP_202_ACCEPTED
            )
        else:
            return JsonResponse(
                {'message': 'Data not found.', 'data': [], 'status': 0},
                status=status.HTTP_404_NOT_FOUND
            )
    # except Exception as e:
    #     return JsonResponse(
    #         {'message': 'Failed to fetch user portfolio lists.', 'error': str(e)},
    #         status=status.HTTP_500_INTERNAL_SERVER_ERROR
    #     )


@api_view(['POST'])
@permission_classes([AllowAny])
def fetchPortfolioDetail(request):
    try:
        portfolio_slug = request.data.get('portfolio_slug')
        # user_id = request.data.get('user_id')

        if portfolio_slug is None:
            return JsonResponse(
                {'message': 'portfolio_slug is required in the request data.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Retrieve user portfolio data for a specific user and portfolio_slug
        user_portfolio_data = UserPortfolio.objects.filter(user__is_admin=True, portfolio_slug=portfolio_slug).first()

        # Serialize the data
        serializer = UserPortfolioSerializer(user_portfolio_data)

        # Return the response
        if user_portfolio_data:
            return JsonResponse(
                {
                    'message': 'Your portfolio fetched successfully.',
                    'data': serializer.data,
                    'status': 1
                },
                status=status.HTTP_202_ACCEPTED
            )
        else:
            return JsonResponse(
                {'message': 'Data not found.', 'data': [], 'status': 0},
                status=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        return JsonResponse(
            {'message': 'Failed to fetch portfolio detail.', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
@api_view(['POST'])
@permission_classes([AllowAny])
def marketsymbols(request):
    try:
        portfolio_slug = request.data.get('portfolio_slug')

        if portfolio_slug is None:
            return JsonResponse(
                {'message': 'Both portfolio_slug and user_id are required in the request data.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Retrieve user portfolio data for a specific user and portfolio_slug
        user_portfolio_data = UserPortfolio.objects.filter(portfolio_slug=portfolio_slug).first()

        # Serialize the data
        serializer = UserPortfolioSerializer(user_portfolio_data, fields=["ticker_values"])

        # Return the response
        if user_portfolio_data:
            return JsonResponse(
                {
                    'message': 'Your portfolio fetched successfully.',
                    'data': serializer.data,
                    'status': 1
                },
                status=status.HTTP_202_ACCEPTED
            )
        else:
            return JsonResponse(
                {'message': 'Data not found.', 'data': [], 'status': 0},
                status=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        return JsonResponse(
            {'message': 'Failed to fetch portfolio detail.', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deletePortfolio(request):
    try:
        portfolio_id = request.data.get('id')

        if portfolio_id is None:
            return JsonResponse(
                {'message': 'Portfolio ID is required in the request data.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Delete user portfolio
        delete_data = UserPortfolio.objects.filter(id=portfolio_id).delete()

        if delete_data:
            return JsonResponse(
                {'message': 'Portfolio is deleted', 'status': 1},
                status=status.HTTP_201_CREATED
            )
        else:
            return JsonResponse(
                {'message': 'Portfolio not found.', 'status': 0},
                status=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        return JsonResponse(
            {'message': 'Failed to delete portfolio.', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def storeUserPortfolio(request):
    if True:
        user_id = request.data.get('user_id')
        portfolio_id = request.data.get('portfolio_id')
        portfolio_name = request.data.get('portfolio_name')
        portfolio_slug = request.data.get('portfolio_slug')
        reinvesting_dividends = request.data.get('reinvesting_dividends')
        currency = request.data.get('currency')
        portfolio_description = request.data.get('portfolio_description')
        ticker_values = json.dumps(request.data.get('ticker_values'))

        if portfolio_id:
            # Update existing portfolio
            user_portfolio = UserPortfolio.objects.filter(user_id=user_id, id=portfolio_id).first()
            if user_portfolio:
                user_portfolio.portfolio_name = portfolio_name
                user_portfolio.reinvesting_dividends = reinvesting_dividends
                user_portfolio.currency = currency
                user_portfolio.portfolio_description = portfolio_description
                user_portfolio.ticker_values = ticker_values
                user_portfolio.portfolio_slug = portfolio_slug
                user_portfolio.save()

                return JsonResponse(
                    {'message': 'Your Portfolio updated successfully.', 'status': 1},
                    status=status.HTTP_201_CREATED
                )
        else:
            # Create new portfolio
            UserPortfolio.objects.create(
                portfolio_name=portfolio_name,
                reinvesting_dividends=reinvesting_dividends,
                currency=currency,
                portfolio_description=portfolio_description,
                ticker_values=ticker_values,
                portfolio_slug=portfolio_slug,
                user_id=user_id
            )

            return JsonResponse(
                {'message': 'Your Portfolio added successfully.', 'status': 1},
                status=status.HTTP_201_CREATED
            )

        return JsonResponse(
            {'message': 'Portfolio not found.', 'status': 0},
            status=status.HTTP_404_NOT_FOUND
        )
    # except Exception as e:
    #     return JsonResponse(
    #         {'message': 'Failed to edit profile.', 'error': str(e)},
    #         status=status.HTTP_500_INTERNAL_SERVER_ERROR
    #     )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def countOfData(request):
    try:
        count_data = User.objects.filter(status=1).aggregate(active_user_count=Count('id'))

        obj = {}
        obj['activeuser'] = count_data['active_user_count']
        obj['course'] = 16

        if count_data['active_user_count'] > 0:
            return JsonResponse({"message": "Count of Data successfully.", "data": obj, "status": 200, "success": True})
        else:
            return JsonResponse({"message": "Data not found.", "data": [], "status": 404, "success": False})

    except Exception as e:
        return JsonResponse({"message": "Failed to count data of users", "status": 500, "success": False})


async def generate_token():
    async def gen():
        hentoken = token()
        user_data = await User.filter(user_token=hentoken).first()
        print("userData", user_data)
        if user_data:
            await gen()
        else:
            return hentoken

    return await gen()

def token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def userPaymentSuccess(request):
    try:
        data = request.POST
        event_type = data.get('event_type')
        content = data.get('content', {})
        customer = content.get('customer', {})
        subscription = content.get('subscription', {})

        if event_type in ["subscription_cancelled", "subscription_reactivated"]:
            found_user = Customer.objects.filter(customer_id=customer.get('id')).first()
            if found_user:
                User.objects.filter(id=found_user.user_id).update(prime_user=(event_type == "subscription_reactivated"))
                return JsonResponse({"message": "You are registered successfully.", "data": {}, "status": 201, "success": True})
            else:
                return JsonResponse({"message": "Something went wrong", "data": {}, "status": 500, "success": False})

        elif event_type == "customer_changed":
            found_user = Customer.objects.filter(customer_id=customer.get('id')).first()
            if found_user:
                User.objects.filter(id=found_user.user_id).update(
                    firstName=customer.get('first_name'),
                    lastName=customer.get('last_name'),
                    email=customer.get('email')
                )
                return JsonResponse({"message": "You are registered successfully.", "data": {}, "status": 201, "success": True})
            else:
                return JsonResponse({"message": "Something went wrong", "data": {}, "status": 500, "success": False})

        elif event_type == "subscription_created":
            user_data = User.objects.filter(email=customer.get('email')).first()
            if user_data:
                return JsonResponse({"message": "User is Already Registered", "data": [], "status": 202, "success": False})
            else:
                gen_token = generate_token()
                data = {
                    'firstName': customer.get('first_name'),
                    'lastName': customer.get('last_name'),
                    'email': customer.get('email'),
                    'user_token': gen_token,
                    'prime_user': True
                }
                registered_data = User.objects.create(**data)
                if registered_data:
                    customer_data = {
                        'customer_id': customer.get('id'),
                        'user_id': registered_data.id,
                        'plan_id': subscription.get('id')
                    }
                    customer_obj = {
                        'user_id': registered_data.id,
                        'customer_id': customer.get('id'),
                        'firstName': registered_data.firstName,
                        'lastName': registered_data.lastName,
                        'email': registered_data.email,
                        'plan_id': subscription.get('id')
                    }

                    Customer.objects.create(**customer_data)
                    send_mail(
                        "SignupEmail",
                        {
                            'username': f"{customer.get('first_name')} {customer.get('last_name') or ''}",
                            'link': f"{process.env.ADMIN_PORTAL_URL}/set-password/{gen_token}",
                        },
                        customer.get('email'),
                        "Please set password to access portal - Amassing Investment"
                    )
                    print(send_mail(subject="Agent Invitation", html_message=html_message, from_email=sender, recipient_list=receivers, fail_silently=True,message=plain_message))

                    return JsonResponse({"message": "You are registered successfully.", "data": customer_obj, "status": 201, "success": True})
                else:
                    return JsonResponse({"message": "Data not found.", "data": [], "status": 404, "success": False})

        else:
            return JsonResponse({"message": "Event type not handled", "data": {}, "status": 400, "success": False})

    except Exception as e:
        return JsonResponse({"message": "Failed to user registration", "status": 500, "success": False})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@decorator_from_middleware(EncryptionMiddleware)
def storeUserPortfolioPublish(request):
    if True:
        data = request.POST
        id = data.get('id')
        header_title = data.get('header_title')
        header_description = data.get('header_description')
        title = data.get('title')
        description = data.get('description')
        image_url = data.get('image_url')
        without_login = True if data.get('without_login') == "true" else False
        paid_user = True if data.get('paid_user') == "true" else False
        is_free = True if data.get('is_free') == "true" else False
        show_ticker = True if data.get('show_ticker') == "true" else False

        print(id)
        if UserPortfolio.objects.filter(id=id).exists():
            # user_data = UserPortfolio.objects.get(id=id)
            upload_object = {
                'header_title': header_title,
                'header_description': header_description,
                'image_url': image_url,
                'title': title,
                'description': description,
                'without_login': without_login,
                'paid_user': paid_user,
                'is_free': is_free,
                'is_published': True,
                'show_ticker':show_ticker,
            }

            uploaded_image = request.FILES.get('image')
            if uploaded_image:
                image_path = default_storage.save(f'media/{id}_{uploaded_image.name}', ContentFile(uploaded_image.read()))
                upload_object['image_url'] = image_path

            # UserPortfolio.objects.get(id=user_data.id).update(**upload_object)
            print(upload_object)
            UserPortfolio.objects.filter(id=id).update(**upload_object)
            return JsonResponse({"message": "Your Portfolio updated successfully.", "status": 201, "success": True})
        else:
            print("else part")
            return JsonResponse({"message": "Failed to publish store user portfolio", "status": 500, "success": False})
            

    # except Exception as e:
    #     return JsonResponse({"message": "Failed to publish store user portfolio", "status": 500, "success": False})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def updateUserPortfolioPublish(request):
    try:
        data = request.data
        portfolio_id = data.get('portfolio_id')

        if UserPortfolio.objects.filter(id=portfolio_id).exists():
            UserPortfolio.objects.filter(id=portfolio_id).update(is_published=False)

            return JsonResponse({"message": "Your Portfolio updated successfully.", "status": 201, "success": True})
        else:
            return JsonResponse({"message": "Data not found.", "status": 404, "success": False})

    except Exception as e:
        return JsonResponse({"message": "Failed to update store user portfolio", "status": 500, "success": False})
    

@api_view(['GET'])
def social_login_urls(request):
    print(request.build_absolute_uri(reverse('google_login')))
    return Response({
        "google_login_url": request.build_absolute_uri(reverse('google_login')),
        # "facebook_login_url": request.build_absolute_uri(reverse('facebook_login')),
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_data(request):
    print(request.user)
    return Response({"user":request.user})

@api_view(['POST'])
@permission_classes([AllowAny])
def test(response):
    print(response.POST)

@api_view(['POST'])
@permission_classes([AllowAny])
def extra_apis(request):
    request_data = request.data
    url = request_data.get("url")
    response = requests.get(url)
 
    if response.status_code == 200:
        data = response.json()
        return Response({"data" : data,"status" : 200})
    else:
        return JsonResponse({"error": "Failed to retrieve data"}, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def listPublished(request):
    request_data = request.data
    # data = UserPortfolio.objects.filter(is_published=True)
    data = UserPortfolio.objects.filter(is_published=True)
    if request_data.get("without_login",False):
        data = data.filter(without_login=True)
    
    if request_data.get("paid_user",False):
        data = data.filter(paid_user=True)
    
    if request_data.get("is_free",False):
        data = data.filter(is_free=True)

    print(data)
    data = UserPortfolioSerializer(data,  many=True, fields=["portfolio_name", "portfolio_id", "portfolio_slug", "header_title", "header_description", "ticker_values", "description", "image_url"]).data

    return Response({"data":data, "status":200})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_subscription(request):
    user = request.user
    req = request.data
    
    if req.get("plan") == "monthly":
        plan = "BETA-USD-Monthly"
    else:
        plan = "BETA-USD-Yearly"
    
    try:
        result = chargebee.Customer.create({
        "id": user.email,
        "company": f"{user.email}",
        "card" : {
            "number" : req.get("number"),
            "expiry_month" : req.get("expiry_month"),
            "expiry_year" : req.get("expiry_year"),
            "cvv" : req.get("cvv"),
        },
        "email" : f"{user.email}",
        "billing_address": {
            "email": user.email,
            "zip": req.get("zip")
        }
        })
    except Exception as e:
        return Response({"data":str(e), "status":500})


    print(result)

    try:
        if (date.today() - request.user.created_at).days > 14:
            if req.get("coupon", False):
                result = chargebee.Subscription.create_with_items(user.email,{
                "subscription_items" : [
                    {
                        "item_id" : "BETA",
                        "item_price_id" : plan,
                    }],
                    "coupon_ids" : [req.get("coupon")]
                })
            else:
                result = chargebee.Subscription.create_with_items(user.email,{
                "subscription_items" : [
                    {
                        "item_id" : "BETA",
                        "item_price_id" : plan,
                    }]
                })
        else:
            created_date = request.user.created_at
            created_datetime = datetime.datetime.combine(created_date, datetime.datetime.min.time())
            if req.get("coupon",False):
                result = chargebee.Subscription.create_with_items(user.email,{
                "subscription_items" : [
                    {
                        "item_id" : "BETA",
                        "item_price_id" : plan,
                    }],
                    "start_date" : int((created_datetime + timedelta(days=14)).timestamp()),
                    "coupon_ids" : [req.get("coupon")]
                })
            else:
                result = chargebee.Subscription.create_with_items(user.email,{
                "subscription_items" : [
                    {
                        "item_id" : "BETA",
                        "item_price_id" : plan,
                    }],
                    "start_date" : int((created_datetime + timedelta(days=14)).timestamp())
                })
        subscription = result.subscription
        invoice = result.invoice
        unbilled_charges = result.unbilled_charges
        print(result)
        print(subscription)
    except:
        chargebee.Customer.delete(user.email)
        return Response({"data":"Not valid card data", "status":500})

    user.prime_user = True
    user.subscription_id = subscription.id
    user.is_subscribed = True
    user.save()
    
    return Response({"data":"Subscription Successfully Created", "status":200})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reactivate_subscription(request):
    user = request.user
    if request.user.is_subscribed:
        try:
            result = chargebee.Subscription.reactivate(user.subscription_id,{
            "invoice_immediately" : True,
            })
        except Exception as e:
            return Response({"data":str(e), "status":500, "is_error":True})

        user.prime_user = True
        user.save()
        return Response({"data":"Successfully Reactivated.", "status":200})
    else:
        return Response({"data":"User has never subscribed before", "status":200, "is_error":True})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_subscription(request):
    user = request.user
    try:  
        if (date.today() - request.user.created_at).days < 14:
            result = chargebee.Subscription.cancel_for_items(user.subscription_id,{})
            user.prime_user = False
            user.save()
        else:
            result = chargebee.Subscription.cancel_for_items(user.subscription_id,{
            "end_of_term" : True
            })
    except Exception as e:
        return Response({"data":str(e), "status":500, "is_error":True})
    
    return Response({"data":"Subscription has been cancelled." ,"status":200})

@api_view(['POST'])
@permission_classes([AllowAny])
def contact_us(request):
    req = request.data
    name = req.get("fullName")
    email = req.get("email")
    message = req.get("message")
    
    send_mail( "Contact Email",
               f"name:- {name} email:- {email} message:- {message}",
               "noreply@amassinginvestment.com",
                ["support@amassinginvestment.com", "askicorp@gmail.com", "danishinvex@gmail.com"],
                fail_silently=False
            )
    return Response({"data":"Email has been sent." ,"status":200})

@api_view(['POST'])
@permission_classes([AllowAny])
def webhook(request):
    res = request.data
    email = res["content"]["customer"]["email"]
    if User.objects.filter(email=email).exists():
        u = User.objects.get(email=email)
    else:
        return Response({"data":"User not found" ,"status":200})
    
    u.prime_user = False
    u.save()
    return Response({"data":request.data})

@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    data = request.data
    if not User.objects.filter(email=data.get("email")).exists():
        return Response({"data" : "User with this email not exists.","status" : 500})
    random_number = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

    if TempTokenModel.objects.filter(email=data.get("email")).exists():
        TempTokenModel.objects.filter(email=data.get("email")).delete()
        
    TempTokenModel.objects.create(email=data.get("email"), token=random_number)
    
    link = f"https://amassinginvestment.com/set-password/{random_number}"

    html_message = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta http-equiv="X-UA-Compatible" content="IE=edge">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Document</title>
        </head>
        <body>
            <div style="text-align:center;margin-left:auto;margin-right:auto;width:100%;">
                <img src="cid:img1" alt="Logo" style="width:200px;height:100px"></div>
            
            <h1><strong>Reset Your Amassing Investment Password</strong></h1>
            <p>Dear User,</p>
            <p>We received a request to reset the password associated with your Amassing Investment account. To complete the process, please click on the link below:</p>
            <p><a href="{link}">{link}</a></p>
            <p>If you did not request this password reset, please ignore this email. Your account security is important to us, and no action is required on your part.</p>
            <p>If you have any questions or need further assistance, please don't hesitate to contact our support team at mailto:support@amassinginvestment.com.</p>
            <p style="height: 5px;"></p>
        <p><strong>Best Regards,
        <br>The Amassing Investment Team</strong></p>
        <div style="width: 100%; background: #e5e5e5; display: flex; align-items: center; justify-content: center">
            <p style="text-align: center"><strong>PS:</strong> We hope you're enjoying your experience with us! As always, feel free to reach out to us at <a href="mailto:support@amassinginvestment.com">support@amassinginvestment.com</a>.  We'd love to hear from you.</p>
        </div>
        </body>
        </html>
        """

            # message = f"https://skyeduserve.com/register-link/{random_number}"
    print(send_email(subject="Reset Your Amassing Investment Password", html_content=html_message, sender="Amassing Investment <noreply@amassinginvestment.com>", recipient=[data.get("email")], image_path="logo.jpg", image_name="img1"))

    return Response({"data" : "data saved","status" : 200})
    