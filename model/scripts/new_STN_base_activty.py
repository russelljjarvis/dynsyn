import numpy
import pylab
import os
import sys
import time as ttime

# Get directory where model and code resides 
model_dir=   '/'.join(os.getcwd().split('/')[0:-1])    
code_dir=  '/'.join(os.getcwd().split('/')[0:-2])  

# Add model, code and current directories to python path
sys.path.append(os.getcwd())  
sys.path.append(model_dir)
sys.path.append(code_dir+'/nest_toolbox') 
from src import my_nest, misc, my_topology, plot_settings
from src.my_axes import MyAxes 

from simulation_utils import simulate_basa_line_STN
from src import misc
import scipy.optimize as opt

HOME_DATA='/home/mikael/results/papers/dynsyn/network/supermicro/'
OUTPUT_PATH  = HOME_DATA + sys.argv[0].split('/')[-1].split('.')[0]

# Assume: n_gpe_stn=30, stn_current=0 and weight ctx_stn
# Find: weight GPe-STN and rate ctx
#
# Requirements
# alt 1. 1. 20 Hz without GPe input Farries 2010
# alt 2  1. 466 % upp  Feger 1991
# 2. 10 Hz with gaba


neuron_model=['STN_75_aeif']
syn_models=['CTX_STN_ampa_s','GPE_STN_gaba_s' ]
gpe_rate=30.0        
n_ctx, n_gpe =1, 30
THREADS=1 
def plot_example(ax, STN_target, sim_time, x, type):
    meanRate=round(STN_target.signals['spikes'].mean_rate(1000,sim_time),1)
    spk=STN_target.signals['spikes'].time_slice(1000,sim_time).raw_data()
    CV=numpy.std(numpy.diff(spk[:,0],axis=0))/numpy.mean(numpy.diff(spk[:,0],axis=0))

    
    STN_target.signals['V_m'].my_set_spike_peak( 15, spkSignal= STN_target.signals['spikes'] )          
    pylab.rcParams.update( {'path.simplify':False}    )
    
    STN_target.signals['V_m'].plot(display=ax)
    ax.set_title( type+'\n'+str(meanRate)+ 'Hz, CV='+str(round(CV,4))+
                  ', rate CTX='+str(round(x[0],4))+', w_GPE_STN='+str(round(x[1],4)) )


def restriction_1(gpe_rate, n_ctx, n_gpe, x,  neuron_model, syn_models):
# 1. 20 Hz without GPe input
    r,w=x
    target_rate1=20.

#     target_rate1=10.*4.6

#     target_rate1=10.*2.5    
#     target_rate1=10.*3.

#     target_rate1=10.*3.5
#     target_rate1=10.*4.
#     target_rate1=10.*4.5
#     target_rate1=10.*5.
#     target_rate1=10.*5.5   
    target_rate1=10.*8        
    n_gpe_ch=0
    STN_target=simulate_basa_line_STN(r, gpe_rate, n_ctx, n_gpe_ch,  
                               neuron_model, syn_models, 0, # This is the current to add to I_e base
                               sim_time, THREADS, w_GPE_STN=w) 
 
    e=round(STN_target.signals['spikes'].mean_rate(1000,sim_time),1)-target_rate1
#     e=e/target_rate1
    return STN_target, e

def restriction_2(gpe_rate, n_ctx, n_gpe,x,   neuron_model, syn_models):
        # 2. 10 Hz with gaba
        r,w=x
        target_rate2=10.0
        STN_target=simulate_basa_line_STN(r, gpe_rate, n_ctx, n_gpe,  
                               neuron_model, syn_models, 0, # This is the current to add to I_e base
                               sim_time, THREADS, w_GPE_STN=w )
 
        e=round(STN_target.signals['spikes'].mean_rate(1000,sim_time),1)-target_rate2
#         e=e/target_rate2
        
        return STN_target, e

def GPE_46_hz(gpe_rate, n_ctx, n_gpe, x, neuron_model, syn_models):
        # When GPe firers ar 30*1.55
        r,w=x
        gpe_rate_ch=30*1.55
        STN_target=simulate_basa_line_STN(r, gpe_rate_ch, n_ctx, n_gpe,  
                               neuron_model, syn_models, 0, # This is the current to add to I_e base
                               sim_time, THREADS, w_GPE_STN=w)
  
        STN_target.signals['spikes'].mean_rate(1000,sim_time)
        return STN_target

def error_fun(x, sim_time):
        
        
        STN_target, e1=restriction_1(gpe_rate, n_ctx, n_gpe, x, neuron_model, syn_models)
        STN_target, e2=restriction_2(gpe_rate, n_ctx, n_gpe, x, neuron_model, syn_models)
     
        print e1**2+e2**2
        return e1**2+e2**2
        
def fmin(load, save_at):
    
  
    x0=[188, 0.08]  #[current, w_GPE_STN] 20 Hz
  
  
  #29.720625
  #0.011041875

#     x0=[290, 0.119] #25
#     x0=[430,0.18] #30 Hz
#     x=[540, 0.215] #35 Hz
#     x0=[702, 0.28] #40 Hz
#     x0=[830., 0.336] #45 Hz
#     x0=[876.7, 0.349]  #[current, w_GPE_STN] 46 Hz
#     x0=[1000.8, 0.3957] # 50 Hz]
#     x0=[1159., 0.458] # 55 Hz]    
#     x0=[1159.+2.5*5*29.7, 0.458+2.5*5*0.01104] # 80 Hz] 
    x0=[2102, 0.794] # 80 Hz] 
#     z=[1161, 454] #
    if not load:
        [xopt,fopt, iter, funcalls , warnflag, allvecs] = opt.fmin(error_fun, 
                                                                   x0, 
                                                                   args=([sim_time]), 
                                                                   maxiter=20, 
                                                                   maxfun=20, 
                                                                   full_output=1, retall=1)

        misc.pickle_save([xopt,fopt, iter, funcalls , warnflag, allvecs], save_at)
    else:
        [xopt,fopt, iter, funcalls , warnflag, allvecs]=misc.pickle_load(save_at)        
    return xopt  



sim_time=20000
  

save_at=OUTPUT_PATH+'/simulate_network_fmin.plk' 
x=fmin(0,save_at)
#x=[215, 0.08]

STN_target1, e1=restriction_1(gpe_rate, n_ctx, n_gpe, x, neuron_model, syn_models)
STN_target2, e2=restriction_2(gpe_rate, n_ctx, n_gpe, x, neuron_model, syn_models)
STN_target3 = GPE_46_hz(gpe_rate, n_ctx, n_gpe, x, neuron_model, syn_models)

plot_settings.set_mode(pylab, mode='by_fontsize', w = 500.0, h = 500.0, fontsize=8)
font_size_text = 8
fig = pylab.figure( facecolor = 'w')

ax_list=[]
ax_list.append( MyAxes(fig, [ .1, .7, .8, .2 ] ) )    # text box
ax_list.append( MyAxes(fig, [ .1, .4, .8, .2 ] ) )    # 
ax_list.append( MyAxes(fig, [ .1, .1, .8, .2 ] ) )    # 
 
ax=ax_list[0]
plot_example(ax, STN_target1,sim_time, x, type='No GPE')  

ax=ax_list[1]
plot_example(ax, STN_target2, sim_time, x, type='Normal')  

ax=ax_list[2]
plot_example(ax, STN_target3, sim_time, x, type='GPE rate at '+str(30*1.55))  
        
pylab.show()