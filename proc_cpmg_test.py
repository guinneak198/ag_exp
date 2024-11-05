from pylab import *
from pyspecdata import *
from pyspecProcScripts import *
from sympy import exp as s_exp
fl = figlist_var()
# {{{ load the files that we're interested in as different nddata objects
all_data = {}
pathways = {}
# {{{ 240625 - 0 dB
#all_data["Hahn 0 dB"] = find_file(
#    "240625_200uM_TEMPOL_0dB_echo.h5",
#    exp_type="ODNP_NMR_comp/Echoes",
#    expno="echo_2",
#    lookup = lookup_table
#)
#all_data["SE 0dB - 1"] = find_file(
#    "240625_200uM_TEMPOL_0dB_generic_echo.h5",
#    exp_type="ODNP_NMR_comp/Echoes",
#    expno="echo_2",
#    lookup = lookup_table
#)
#all_data["SE 0dB - 2"] = find_file(
#    "240625_200uM_TEMPOL_0dB_generic_echo.h5",
#    exp_type="ODNP_NMR_comp/Echoes",
#    expno="echo_4",
#    lookup = lookup_table
#)
#all_data["CPMG 0 dB - 1"] = find_file(
#    "240625_200uM_TEMPOL_0dB_generic_CPMG.h5",
#    exp_type="ODNP_NMR_comp/Echoes",
#    expno="CPMG_3",
#    lookup = lookup_table
#)
#all_data["CPMG 0 dB - 2"] = find_file(
#    "240625_200uM_TEMPOL_0dB_generic_CPMG.h5",
#    exp_type="ODNP_NMR_comp/Echoes",
#    expno="CPMG_5",
#    lookup = lookup_table
#)
# }}}
# {{{ 240624 - 30 dB
#all_data["CPMG 30 dB - 1"] = find_file(
#    "240625_200uM_TEMPOL_30dB_generic_CPMG.h5",
#    exp_type="ODNP_NMR_comp/Echoes",
#    expno="CPMG_1",
#    lookup = lookup_table
#)
#all_data["CPMG 30 dB - 2"] = find_file(
#    "240625_200uM_TEMPOL_30dB_generic_CPMG.h5",
#    exp_type="ODNP_NMR_comp/Echoes",
#    expno="CPMG_3",
#    lookup = lookup_table
#)
#all_data["SE 30 dB - 1"] = find_file(
#    "240625_200uM_TEMPOL_30dB_generic_echo.h5",
#    exp_type="ODNP_NMR_comp/Echoes",
#    expno="echo_2",
#    lookup = lookup_table
#)
#all_data["SE 30 dB - 2"] = find_file(
#    "240625_200uM_TEMPOL_30dB_generic_echo.h5",
#    exp_type="ODNP_NMR_comp/Echoes",
#    expno="echo_4",
#    lookup = lookup_table
#)
# {{{ 240625 34 dBm
all_data["SE 34 dB - 1"] = find_file(
    "240625_200uM_TEMPOL_34dB_generic_echo.h5",
    exp_type="ODNP_NMR_comp/Echoes",
    expno="echo_2",
    lookup = lookup_table
)
all_data["SE 34 dB - 2"] = find_file(
    "240625_200uM_TEMPOL_34dB_generic_echo.h5",
    exp_type="ODNP_NMR_comp/Echoes",
    expno="echo_4",
    lookup = lookup_table
)
all_data["CPMG 34 dB - 1"] = find_file(
    "240625_200uM_TEMPOL_34dB_generic_CPMG.h5",
    exp_type="ODNP_NMR_comp/Echoes",
    expno="CPMG_1",
    lookup = lookup_table
)
all_data["CPMG 34 dB - 2"] = find_file(
    "240625_200uM_TEMPOL_34dB_generic_CPMG.h5",
    exp_type="ODNP_NMR_comp/Echoes",
    expno="CPMG_3",
    lookup = lookup_table
)
# }}}
with figlist_var() as fl:
    for thislabel, thisd in all_data.items():
        obs(
                f"for {thislabel} spectral width {thisd.get_prop('acq_params')['SW_kHz']}~kHz"
                )
        if 'nScans' in thisd.dimlabels:
            thisd *= thisd.shape['nScans']
            thisd.mean('nScans')
        d = thisd
        d.ift('t2')
        fl.next('raw data for %s'%thislabel)
        #if 'indirect' in d.dimlabels:
        #    d.rename('indirect','nEcho')
        #    d.reorder(['ph_overall','ph_diff','nEcho','t2'])
        fl.image(d)
        d.ft('t2')
        fl.next('SE vs CPMG[nEcho,0] - 30 dBm')
        d.ift('t2')
        if 'CPMG' in thislabel:
            d = d['nEcho',:3]
            d.smoosh(['nEcho','t2'],'t2')
            acq = d.get_prop('acq_params')
            echo_time = 1e-6*2*(acq['tau_us']+acq['p90_us'])
            d['t2'] = (d['t2']['nEcho']) * echo_time + d['t2']['t2']
            d = select_pathway(d,d.get_prop('coherence_pathway'))
            fl.plot(abs(d),'.',label = thislabel)
        else:
            fl.plot(abs(select_pathway(d['t2':(0,15e-3)],d.get_prop('coherence_pathway'))),'.',label = thislabel)

