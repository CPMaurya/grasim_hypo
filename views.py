from django.http import JsonResponse, HttpResponse
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.permissions import *
from rest_framework.response import Response
from django.db import transaction


from .calc import calc_hypo
from .pi_data_push import write_single_value
from .serializers import *
from .models import *
from braces.views import CsrfExemptMixin
import csv
from django.contrib.auth import authenticate
import random
from django.core.mail import send_mail
from django.conf import settings
from datetime import date, timedelta, datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import copy
from main.utils import get_data_from_pi, validate_input_data


class DosageDetailView(CsrfExemptMixin, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = []
    serializer_class = DosageSerializer
    queryset = Dosage.objects.all()


class DosageListView(CsrfExemptMixin, generics.ListCreateAPIView):
    permission_classes = []
    serializer_class = DosageCreateSerializer
    queryset = Dosage.objects.all()


class ExportView(APIView):
    def get(self, request):
        today_date = date.today()
        print(today_date)
        user_id = request.query_params['id']
        dosage = Dosage.objects.filter(user=user_id, date=today_date)
        response = HttpResponse('')
        response['Content-Disposition'] = 'attachment; filename = dosage_all.csv'
        writer = csv.writer(response)
        # writer.writerow(['User'])
        # dosage_fields = dosage.values_list('user')
        # for dosage in dosage_fields:
        #     print(dosage)
        #     writer.writerow(dosage)
        writer.writerow([
            'date', 'time',  'Target Hypo Input', 
            'target_loose_pulp_viscosity', 'eop_prev1', 'eop_prev2', 
            'hypo_visc_prev2', 'hypo_visc_prev1', 'hypo_add_prev1', 'hypo2'
        ])
        dosage_fields = dosage.values_list(
            'date', 'time', 'Target_hypo_Input', 'target_loose_pulp_viscosity',
            'eop_prev1', 'eop_prev2', 'hypo_visc_prev2', 'hypo_visc_prev1',
            'hypo_add_prev1', 'hypo2'
        )
        for dosage in dosage_fields:
            writer.writerow(dosage)
        return response


class LoginView(APIView):
    def get(self, request):
        email = request.query_params['email']
        print(email)
        otp = int(request.query_params['otp'])
        print(otp)
        user = authenticate(email=email, password=otp)
        if user is not None:
            user_object = NewUser.objects.get(email=email)
            print(user_object)
            user_id = user_object.id
            user_email = user_object.email
            data = {
                'id': user_id,
                'email': user_email,
            }
            return JsonResponse({"message": "verified", "user": data}, status=200)
        else:
            return JsonResponse({"message": "incorrect otp"}, status=200)

    def post(self, request):
        email = request.data['email']
        # def sendotpfinal(email):
        #     otp = int((random.uniform(0, 1))*100000)
        #     # print(otp)
        #     if otp <= 100000 and otp >10000:
        #         otp = f"{otp}"
        #     elif otp <= 10000 and otp >1000:
        #         otp = f"0{otp}"
        #     elif otp <= 1000 and otp >100:
        #         otp = f"00{otp}"
        #     elif otp <= 100 and otp >10:
        #         otp = f"000{otp}"
        #     elif otp <= 10 and otp >1:
        #         otp = f"0000{otp}"
        #     otp = str(otp)
        #     # print(otp)
        #     sendotp(email,otp)
        #     changepassword(email, otp)
        #     return "OTP Sent"
        # foo = sendotpfinal(email)
        try:
            user = NewUser.objects.get(email=email)
            data = {
                "id": user.id,
                "email": user.email,
            }
            return JsonResponse(data, status=200)
        except Exception as e:
            user_object = NewUser(email=email)
            user_object.save()
            print(user_object)
            user_email = user_object.email
            data = {
                "id": user_object.id,
                "email": user_email,
            }
            return JsonResponse(data, status=200)


def sendotp(email, otp):
    message = Mail(
        from_email="noreply@ripik.in",
        to_emails=email,
        subject='OTP for logging In',
        html_content=f'Your OTP for logging in is {otp}. Thank you for using our services.',
    )
    sendgrid_client = SendGridAPIClient(api_key=settings.EMAIL_HOST_PASSWORD)
    response = sendgrid_client.send(message=message)
    print(response.status_code)
    # subject = 'OTP for logging In'
    # message = f'Your OTP for logging in is {otp}. Thank you for using our services.'
    # email_from = 'noreply@ripik.in'
    # recipient_list = [email]
    # # print("email sent")
    # send_mail( subject, message, email_from, recipient_list, fail_silently=False, )


def changepassword(email, otp):
    user = NewUser.objects.all().filter(email=email).first()
    if user:
        user.set_password(otp)
        user.save()
        # print(otp)
    else:
        user = NewUser.objects.create_user(email=email, password=otp)
        print(otp)
        user.save()
    # print("passwordchanged")
    # print(user)


class UserDosageView(APIView):
    def get(self, request):
        user_id = request.query_params['id']
        dosages = Dosage.objects.all()
        serializer = DosageSerializer(dosages, many=True)
        return JsonResponse({"dosages": serializer.data}, status=200)


class MonthExportView(APIView):
    def get(self, request):
        user_id = request.query_params['id']
        today_date = date.today()
        days = today_date.day
        response = HttpResponse('')
        response['Content-Disposition'] = 'attachment; filename = dosage_all.csv'
        writer = csv.writer(response)
        writer.writerow(
            ['date', 'Target Hypo Input', 
            'target_loose_pulp_viscosity', 
            'eop_prev1', 'eop_prev2', 'hypo_visc_prev2',
            'hypo_visc_prev1', 'hypo_add_prev1', 'hypo2']
        )
        for day in range(days):
            dosage = Dosage.objects.filter(user=user_id, date=today_date)
            today_date = today_date - timedelta(days=1)
            dosage_fields = dosage.values_list(
                'date', 'Target_hypo_Input', 
                'target_loose_pulp_viscosity', 'eop_prev1',
                'eop_prev2', 'hypo_visc_prev2', 'hypo_visc_prev1', 
                'hypo_add_prev1', 'hypo2'
            )
            for dosage in dosage_fields:
                writer.writerow(dosage)
        return response


class BetweenDateView(APIView):
    def get(self, request):
        response = HttpResponse('')
        response['Content-Disposition'] = 'attachment; filename = dosage_all.csv'
        writer = csv.writer(response)
        writer.writerow([
            'date', 'time', 'Target Hypo Input', 
            'target_loose_pulp_viscosity', 'eop_prev1', 'eop_prev2',
            'hypo_visc_prev2', 'hypo_visc_prev1', 'hypo_add_prev1', 
            'hypo2', 'target_hypo_addition'
        ])
        start_date = request.query_params['start_date']
        end_date = request.query_params['end_date']
        user_id = request.query_params['id']
        end_date = date(int(end_date[6:]), int(end_date[3:5]), int(end_date[0:2]))
        start_date = date(int(start_date[6:]), int(start_date[3:5]), int(start_date[0:2]))
        days = (end_date - start_date).days + 1
        initial_date = start_date

        def foo(input_date):
            input_date = str(input_date)
            print(input_date)
            dosage = Dosage.objects.all()
            dosage_fields = dosage.values_list(
                'date', 'time', 'Target_hypo_Input', 
                'target_loose_pulp_viscosity', 'eop_prev1', 'eop_prev2', 
                'hypo_visc_prev2', 'hypo_visc_prev1', 'hypo_add_prev1', 
                'hypo2', 'target_hypo_addition'
            )
            for dosage in dosage_fields:
                writer.writerow(dosage)
                # print(input_date)

        for i in range(days):
            current_date = initial_date
            foo(current_date)
            initial_date = initial_date + timedelta(days=1)
        return response


class ClientHypoPush(APIView):
    def post(self, request):
        data = request.data
        eop_prev2 = data['EOP_viscosity_n-2']
        eop_prev1 = data['EOP_viscosity_n-1']
        hypo_visc_prev2 = data['Hypo_viscosity_n-2']
        hypo_visc_prev1 = data['Hypo_viscosity_n-1']
        hypo_add_prev1 = data['Prev_Hypo_Addition']
        Target_hypo_Input = data['Target_Hypo_viscosity(previous)']
        target_loose_pulp_viscosity = data['Target_Loose_pulp_viscosity']
        vf6_flow = data['VF6_Flow']

        pi_data = get_data_from_pi()
        recommended_hypo = pi_data['recommended_hypo']
        hypo_addition_actual = pi_data['hypo_addition_actual']
        actual_loos_pulp = pi_data['actual_loos_pulp']

        # hypo1, hypo2 = calc_hypo(eop_prev1, Target_hypo_Input, hypo_visc_prev1, eop_prev2, vf6_flow)
        hypo1, hypo2 = calc_hypo(
            eop_prev1, Target_hypo_Input, hypo_visc_prev1, eop_prev2, 
            vf6_flow, target_loose_pulp_viscosity, actual_loos_pulp, 
            hypo_addition_actual, recommended_hypo)
            
        dosage_model = Dosage(target_hypo_addition=hypo1,
                              hypo2=hypo2,
                              Target_hypo_Input=Target_hypo_Input,
                              hypo_visc_prev1=hypo_visc_prev1,
                              eop_prev2=eop_prev2,
                              eop_prev1=eop_prev1,
                              target_loose_pulp_viscosity=target_loose_pulp_viscosity,
                              hypo_add_prev1=hypo_add_prev1,
                              hypo_visc_prev2=hypo_visc_prev2, 
                              vf6_flow=vf6_flow)
        dosage_model.save()
        return JsonResponse({"Recommended_Hypo_Addition": hypo1, "Recommended_Hypo_Secondary": hypo2})


class ClientHypoPushAuto(generics.ListAPIView):
    """
    API for fatch data form pi connector and predict 
    data from model and return Recommended_Hypo
    """

    def list(self, request, *args, **kwargs):
        user = self.request.user
        newUser = NewUser.objects.filter(pk=user.pk)
        req_user = None
        if newUser.exists():
            req_user = newUser.first()   
        updated_at = datetime.now().strftime("%Y-%d-%m, %I:%M:%S %p")
        
        target_value = SetTargetValue.objects.last()
        Target_hypo_Input = target_value.target_hypo_viscosity
        target_loose_pulp_viscosity = target_value.target_loose_puls_viscosity

        pi_data = get_data_from_pi()
        pi_data_copy = copy.deepcopy(pi_data)
        pi_data_copy.update({
            'Target_Hypo_viscosity(previous)': Target_hypo_Input,
            'Target_Loose_pulp_viscosity': target_loose_pulp_viscosity,
            'Recommended_Hypo_Addition': 0,
            'Recommended_Hypo_Secondary': 0,
            'updated_at': updated_at,
            'error sensors': []
        })
        validate_results = validate_input_data(pi_data)

        if len(validate_results) != 0:
            pi_data_copy['error sensors'] = validate_results
            return Response(pi_data_copy)

        eop_prev2 = pi_data['EOP_viscosity_n-2']
        eop_prev1 = pi_data['EOP_viscosity_n-1']
        hypo_visc_prev2 = pi_data['Hypo_viscosity_n-2']
        hypo_visc_prev1 = pi_data['Hypo_viscosity_n-1']
        hypo_add_prev1 = pi_data['Prev_Hypo_Addition']
        vf6_flow = pi_data['VF6_Flow']
        recommended_hypo = pi_data['recommended_hypo']
        hypo_addition_actual = pi_data['hypo_addition_actual']
        actual_loos_pulp = pi_data['actual_loos_pulp']
        # Target_hypo_Input = pi_data['Target_Hypo_viscosity(previous)']
        # target_loose_pulp_viscosity = pi_data['Target_Loose_pulp_viscosity']

        hypo1, hypo2 = calc_hypo(
            eop_prev1, Target_hypo_Input, hypo_visc_prev1, eop_prev2, 
            vf6_flow, target_loose_pulp_viscosity, actual_loos_pulp, 
            hypo_addition_actual, recommended_hypo)

        try:
            write_single_value(data_value=hypo1, hypo_type='hypo1')
            write_single_value(data_value=hypo2, hypo_type='hypo2')
        except:
            pass
        dosage_model = Dosage(target_hypo_addition=hypo1,
                              hypo2=hypo2,
                              Target_hypo_Input=Target_hypo_Input,
                              hypo_visc_prev1=hypo_visc_prev1,
                              eop_prev2=eop_prev2,
                              eop_prev1=eop_prev1,
                              target_loose_pulp_viscosity=target_loose_pulp_viscosity,
                              hypo_add_prev1=hypo_add_prev1,
                              hypo_visc_prev2=hypo_visc_prev2,
                              user=req_user,
                              vf6_flow=vf6_flow)
        dosage_model.save()
        updated_at = datetime.now().strftime("%Y-%d-%m, %I:%M:%S %p")
        pi_data_copy.update({
            'Target_Hypo_viscosity(previous)': Target_hypo_Input,
            'Target_Loose_pulp_viscosity': target_loose_pulp_viscosity,
            'Recommended_Hypo_Addition': hypo1,
            'Recommended_Hypo_Secondary': hypo2,
            'updated_at': updated_at
        })
        return Response(pi_data_copy)


class SaveTargetValueView(APIView):
    def post(self, request):
        data = request.data
        newUser = NewUser.objects.filter(pk=request.user.pk)
        req_user = None
        if newUser.exists():
            req_user = newUser.first()  

        Target_hypo_Input = data['Target_Hypo_viscosity(previous)']
        target_loose_pulp_viscosity = data['Target_Loose_pulp_viscosity']
        SetTargetValue.objects.create(
            target_hypo_viscosity=Target_hypo_Input,
            target_loose_puls_viscosity=target_loose_pulp_viscosity,
            user=req_user
        )
        return Response({"sucess: true"})
