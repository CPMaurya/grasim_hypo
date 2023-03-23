import datetime as dt
import pandas as pd
from requests_ntlm import HttpNtlmAuth
import tagreader
import numpy as np
from django.conf import settings
from main.models import Dosage


def get_data_from_pi():
    userID='digitization.pfic'
    userPW='Birla$2023'
    tagreader.list_sources(
        imstype="piwebapi", 
        url='https://10.193.0.16/piwebapi', 
        verifySSL=False, 
        auth = HttpNtlmAuth(userID, userPW)
    )
    
    pi_conn = tagreader.IMSClient(
        datasource = 'GILVSFHRH-PI1', 
        imstype = 'piwebapi', 
        url = 'https://10.193.0.16/piwebapi',
        tz ='Asia/Kolkata', verifySSL=False,
        auth = HttpNtlmAuth(userID, userPW)
    )
    pi_conn.connect()

    end_time_m_n1 = dt.datetime.now()
    start_time_n1 = end_time_m_n1 - dt.timedelta(hours=2)

    df_n1=pi_conn.read(["F1DPsfxbRv6mI0Whd6AYjuinrQpgwAAAR0lMVlNGSFJILVBJMVxIUEYtUEktU0FQLUlDRU9QVklT",
                  "F1DPsfxbRv6mI0Whd6AYjuinrQBRkAAAR0lMVlNGSFJILVBJMVxIUEYtUEktQkwtRlgtLTIwOEQuQVY",
                  "F1DPsfxbRv6mI0Whd6AYjuinrQPREAAAR0lMVlNGSFJILVBJMVxIUEYtUEktQkwtVkYwNi1NRVRTTy1TVEstRkxXLk1F"],
                  start_time_n1, end_time_m_n1, 180)

    df_n1.rename(columns={"F1DPsfxbRv6mI0Whd6AYjuinrQpgwAAAR0lMVlNGSFJILVBJMVxIUEYtUEktU0FQLUlDRU9QVklT":'EOP viscosity',
                          "F1DPsfxbRv6mI0Whd6AYjuinrQBRkAAAR0lMVlNGSFJILVBJMVxIUEYtUEktQkwtRlgtLTIwOEQuQVY":"Previous Hypo addition",
                          "F1DPsfxbRv6mI0Whd6AYjuinrQPREAAAR0lMVlNGSFJILVBJMVxIUEYtUEktQkwtVkYwNi1NRVRTTy1TVEstRkxXLk1F": "vf6_flow"},
                      inplace=True)

    df_hypo=pi_conn.read([
                  "F1DPsfxbRv6mI0Whd6AYjuinrQqAwAAAR0lMVlNGSFJILVBJMVxIUEYtUEktU0FQLUlDSFlDRVZJ"],
                  start_time_n1, end_time_m_n1, 180)

    df_hypo.rename(columns={
                          "F1DPsfxbRv6mI0Whd6AYjuinrQqAwAAAR0lMVlNGSFJILVBJMVxIUEYtUEktU0FQLUlDSFlDRVZJ":"Hypo viscosity"},
                      inplace=True)

    df_for_fix=pi_conn.read([
                  "F1DPsfxbRv6mI0Whd6AYjuinrQBRkAAAR0lMVlNGSFJILVBJMVxIUEYtUEktQkwtRlgtLTIwOEQuQVY",
                  "F1DPsfxbRv6mI0Whd6AYjuinrQrAwAAAR0lMVlNGSFJILVBJMVxIUEYtUEktU0FQLUlFTFBDRVZJ",
                  "F1DPsfxbRv6mI0Whd6AYjuinrQdBcAAAR0lMVlNGSFJILVBJMVxIUEYtUEktQ0gtVVBUTy0xLzg"
                  ],
                  start_time_n1, end_time_m_n1, 180)


    df_for_fix.rename(columns={
                    "F1DPsfxbRv6mI0Whd6AYjuinrQBRkAAAR0lMVlNGSFJILVBJMVxIUEYtUEktQkwtRlgtLTIwOEQuQVY":"actual_hypo_addition",
                    "F1DPsfxbRv6mI0Whd6AYjuinrQrAwAAAR0lMVlNGSFJILVBJMVxIUEYtUEktU0FQLUlFTFBDRVZJ": "actual_loos_pulp_visco",
                    "F1DPsfxbRv6mI0Whd6AYjuinrQdBcAAAR0lMVlNGSFJILVBJMVxIUEYtUEktQ0gtVVBUTy0xLzg": "recommended_hypo"
                    },
                    inplace=True)
    
    # df_n2.index = pd.to_datetime( df_n2.index, errors='coerce', utc=False)
    df_n1.index = pd.to_datetime(df_n1.index, errors='coerce', utc=False)
    df_hypo.index = pd.to_datetime(df_hypo.index, errors='coerce', utc=False)
    df_for_fix.index = pd.to_datetime(df_for_fix.index, errors='coerce', utc=False)

    df_n1['DateTime'] = df_n1.index
    df_n1 = df_n1.sort_values("DateTime", ascending=False)
    df_n1 = df_n1.drop_duplicates(subset=['EOP viscosity'])
    if len(df_n1) == 1 :
        df_n1 = pd.concat([df_n1, df_n1], axis= 0)
    df_n1 = df_n1.reset_index()
    
    df_hypo['DateTime'] = df_hypo.index
    df_hypo = df_hypo.sort_values("DateTime", ascending=False)
    df_hypo = df_hypo.drop_duplicates(subset=['Hypo viscosity'])
    if len(df_hypo) == 1 :
        df_hypo = pd.concat([df_hypo, df_hypo], axis= 0)
    df_hypo = df_hypo.reset_index()

    df_for_fix['DateTime'] = df_for_fix.index
    df_for_fix = df_for_fix.sort_values("DateTime", ascending=False)
    df_for_fix = df_for_fix.drop_duplicates(subset=['recommended_hypo'])
    df_for_fix = df_for_fix.reset_index()

    response = {
        'EOP_viscosity_n-2': df_n1['EOP viscosity'][1],
        'EOP_viscosity_n-1': df_n1['EOP viscosity'][0],
        'Hypo_viscosity_n-2': df_hypo['Hypo viscosity'][1],
        'Hypo_viscosity_n-1': df_hypo['Hypo viscosity'][0],
        'Prev_Hypo_Addition': df_n1['Previous Hypo addition'][0],
        'VF6_Flow': df_n1['vf6_flow'][0],
        'recommended_hypo': df_for_fix['recommended_hypo'][0],
        'hypo_addition_actual': df_for_fix['actual_hypo_addition'][0],
        'actual_loos_pulp': df_for_fix['actual_loos_pulp_visco'][0]
    }
 
    # response = {
    #     'EOP_viscosity_n-2': 460,
    #     'EOP_viscosity_n-1': 480,
    #     'Hypo_viscosity_n-2': 410,
    #     'Hypo_viscosity_n-1': 500,
    #     'Prev_Hypo_Addition': 6,
    #     'VF6_Flow': 50,
    #     'recommended_hypo': 0,
    #     'hypo_addition_actual': 0,
    #     'actual_loos_pulp': 0
    #     # 'Target_Hypo_viscosity(previous)': 490,
    #     # 'Target_Loose_pulp_viscosity': 450,
    # }
    return response

def validate_input_data(data):
    results = []
    EOP_viscosity_min = 450
    EOP_viscosity_max = 650
    Hypo_viscosity_min = 400
    Hypo_viscosity_max = 600

    if EOP_viscosity_min > data['EOP_viscosity_n-2'] < EOP_viscosity_max:
        results.append('EOP_viscosity_n-2 = ' + str(data['EOP_viscosity_n-2']) + " Should be range between " + str(450) + " to " + str(650))
    if EOP_viscosity_min > data['EOP_viscosity_n-1'] < EOP_viscosity_max:
        results.append('EOP_viscosity_n-1 = ' + str(data['EOP_viscosity_n-1']) + " Should be range between " + str(450) + " to " + str(650))
    if Hypo_viscosity_min > data['Hypo_viscosity_n-2'] < Hypo_viscosity_max:
        results.append('Hypo_viscosity_n-2 = ' + str(data['Hypo_viscosity_n-2']) + " Should be range between " + str(400) + " to " + str(600))
    if Hypo_viscosity_min > data['Hypo_viscosity_n-1'] < Hypo_viscosity_max:
        results.append('Hypo_viscosity_n-1 = ' + str(data['Hypo_viscosity_n-1']) + " Should be range between " + str(400) + " to " + str(600))
    return results
