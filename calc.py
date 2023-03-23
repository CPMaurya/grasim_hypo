import math


def calc_hypo(eop_prev1, Target_hypo_Input, hypo_visc_prev1, eop_prev2, vf6_flow, target_loose_pulp_viscosity, actual_loos_pulp, hypo_addition_actual, recommended_hypo):
    hypo_addition = 0
    Target_hypo = 450
    Target_hypo_Input = Target_hypo_Input + (target_loose_pulp_viscosity - actual_loos_pulp)
    delta = eop_prev1 - Target_hypo_Input
    hypo1 = 0
    hypo2_val = 0
    if delta > 150:
        del_cal = delta - 150
        hypo2_val = 7.73395 * math.log(3.405994550408719 * del_cal)
    if eop_prev1 < 510 and hypo_visc_prev1 < 470:
        hypo1 = (0.06515909090909099 * eop_prev1) + -15.781136363636403
    elif eop_prev1 < 510 and hypo_visc_prev1 > 470:
        hypo1 = (0.06472727272727279 * eop_prev1) + -14.190909090909116
    elif 510 < eop_prev1 < 620 and hypo_visc_prev1 < 470:
        hypo1 = (0.0936363636363637 * eop_prev1) + -31.704545454545492
    elif 510 < eop_prev1 < 620 and 470 < hypo_visc_prev1 < 540:
        hypo1 = (0.13709090909090924 * eop_prev1) + -45.79636363636371
    elif 510 < eop_prev1 < 620 and hypo_visc_prev1 > 540:
        hypo1 = (0.13727272727272735 * eop_prev1) + -34.80909090909094
    elif eop_prev2 > 620 and hypo_visc_prev1 < 470:
        hypo1 = (0.16718749999999966 * eop_prev1) + -57.68124999999976
    elif eop_prev2 > 620 and 470 < hypo_visc_prev1 < 540:
        hypo1 = (0.16718749999999966 * eop_prev1) + -57.68124999999976
    elif eop_prev2 > 620 and hypo_visc_prev1 > 540:
        hypo1 = (0.11143749999999988 * eop_prev1) + -15.2562499999999

    diff = abs(hypo_addition_actual - recommended_hypo)
    diff = diff * 0.5
    
    hypo1 = hypo1*(vf6_flow/300)
    hypo2_val = hypo2_val*(vf6_flow/300)
    hypo1 = hypo1 + diff + 20

    return hypo1, hypo2_val
