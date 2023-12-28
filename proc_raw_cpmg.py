from pylab import *
from pyspecdata import *
# {{{ load the files that we're interested in as different nddata objects
all_data = {}
#all_data["AB echo"] = find_file(
#    "231030_CPMG_AB_control_fin.h5",
#    exp_type="ODNP_NMR_comp/CPMG",
#    expno="CPMG_64echoes",
#)
#all_data["AB echo"] = all_data["AB echo"].chunk(
#        "t", ["ph2","ph1","Nechoes","t2"], [4,4,64,-1]).labels(
#                {
#                    "ph1":r_[0:4],
#                    "ph2":r_[0:4],
#                    "Nechoes":r_[0:64]
#                })
#all_data["AB echo"] = find_file(#our original delays and everything except using AB phase cycling
#    "231030_CPMG_16step_CPMG.h5",
#    exp_type="ODNP_NMR_comp/CPMG",
#    expno="CPMG_2",
#)
#all_data['AB echo'].squeeze()
#all_data["AB echo"] = find_file(#AB pad start and 16 phase step
#    "231030_CPMG_16step_CPMG.h5",
#    exp_type="ODNP_NMR_comp/CPMG",
#    expno="CPMG_3",
#)
#all_data["AB echo"] = all_data["AB echo"].chunk(
#        "t", ["ph2","ph1","Nechoes","t2"], [4,4,3,-1]).labels(
#                {
#                    "ph1":r_[0:4],
#                    "ph2":r_[0:4],
#                    "Nechoes":r_[0:3]
#                })
#all_data["AB echo"] = find_file(#16 phase step 2 ms deadtime
#    "231030_CPMG_16step_CPMG.h5",
#    exp_type="ODNP_NMR_comp/CPMG",
#    expno="CPMG_4",
#)
#all_data["AB echo"] = all_data["AB echo"].chunk(
#        "t", ["ph2","ph1","Nechoes","t2"], [4,4,3,-1]).labels(
#                {
#                    "ph1":r_[0:4],
#                    "ph2":r_[0:4],
#                    "Nechoes":r_[0:3]
#                })
#all_data["AB echo"] = find_file(#16 phase step 2 ms deadtime, calculate ta BEST SO FARu
#    "231031_CPMG_AB_control_1.h5",
#    exp_type="ODNP_NMR_comp/CPMG",
#    expno="CPMG_64echoes",
#)
#all_data["AB echo"] = all_data["AB echo"].chunk(
#        "t", ["ph2","ph1","Nechoes","t2"], [4,4,64,-1]).labels(
#                {
#                    "ph1":r_[0:4],
#                    "ph2":r_[0:4],
#                    "Nechoes":r_[0:64]
#                })
#all_data["AB echo"].ft(['ph1','ph2'],unitary=True)
all_data["AB echo"] = find_file(#8 phase step 2 ms deadtime, calculate tau
    "231031_CPMG_prep_CPMG.h5",
    exp_type="ODNP_NMR_comp/CPMG",
    expno="CPMG_16",
)
all_data["AB echo"] = all_data["AB echo"].chunk(
        "t", ["ph2","ph1","Nechoes","t2"], [4,4,64,-1]).labels(
                {
                    "ph1":r_[0:4],
                    "ph2":r_[0:4],
                    "Nechoes":r_[0:64]
                })               
#all_data["AB echo"].ft(['ph_diff','ph_overall'],unitary=True)
all_data["AB echo"].ft(['ph1','ph2'],unitary=True)# }}}
with figlist_var() as fl:
    for thislabel, thisd in all_data.items():
        obs(
                f"for {thislabel} spectral width {thisd.get_prop('acq_params')['SW_kHz']}~kHz"
                )
        fl.next("deadtime = 245 us")
        fl.image(thisd, interpolation='bilinear')
        
        #fl.next('1D')
        #fl.plot(abs(thisd['ph_overall',-1]['ph_diff',1]),label = 'ph_diff=+1, phoverall = -1')
