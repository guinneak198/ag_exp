import SpinCore_pp
from SpinCore_pp.power_helper import Ep_spacing_from_phalf
from SpinCore_pp.ppg import run_spin_echo, run_IR
from Instruments import power_control
from datetime import datetime


config_dict = SpinCore_pp.configuration("active.ini")

T1_powers_dB =(
        est_phalf = config_dict['guessed_phalf']/4,
        max_power = config_dict["max_power"],
        p_steps =  config_dict["num_T1s"],
        min_dBm_step = config_dict['min_dBm_step'], 
        three_down=False
) 
print(T1_powers_dB)
