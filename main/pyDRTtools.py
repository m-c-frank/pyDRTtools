# -*- coding: utf-8 -*-
"""
Created on Fri Dec  4 17:22:26 2020

@author: thwan
"""
import sys
from os import environ
import csv
import numpy as np
from numpy import inf, log, log10, absolute, angle

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog
from layout import Ui_MainWindow
from DRT_main import *

# import matplotlib related packages
import matplotlib as mpl
mpl.use("Qt5Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
#plt.rc('text', usetex=True)

__author__ = 'Ting Hei Wan'
__date__ = '27 Jan 2021'


class pyDRTtools_GUI(QtWidgets.QMainWindow):
    def __init__(self):
        # Initalize parent
        QtWidgets.QMainWindow.__init__(self)
        
        # Initalize GUI layout
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
       
        # setting data to be None initally
        self.data = None
       
        # linking buttons with various functions
        # import button
        self.ui.import_button.clicked.connect(self.import_file)
        self.ui.induct_choice.currentIndexChanged.connect(self.inductance_callback) # activated when item change
        # show buttons
        self.ui.show_EIS.clicked.connect(lambda: self.plotting_callback('EIS_data'))
        self.ui.show_mag.clicked.connect(lambda: self.plotting_callback('Magnitude'))
        self.ui.show_phase.clicked.connect(lambda: self.plotting_callback('Phase'))
        self.ui.show_re.clicked.connect(lambda: self.plotting_callback('Re_data'))
        self.ui.show_im.clicked.connect(lambda: self.plotting_callback('Im_data'))
        self.ui.show_re_res.clicked.connect(lambda: self.plotting_callback('Re_residual'))
        self.ui.show_im_res.clicked.connect(lambda: self.plotting_callback('Im_residual'))
        self.ui.show_DRT.clicked.connect(lambda: self.plotting_callback('DRT_data'))
        self.ui.show_score.clicked.connect(lambda: self.plotting_callback('Score'))
        # run buttons
        self.ui.simple_run_button.clicked.connect(self.simple_run_callback)
        self.ui.bayesian_button.clicked.connect(self.bayesian_run_callback)
        self.ui.HT_button.clicked.connect(self.BHT_run_callback)
        # export result buttons
        self.ui.export_DRT_button.clicked.connect(self.export_DRT)
        self.ui.export_EIS_button.clicked.connect(self.export_EIS)
        self.ui.export_fig_button.clicked.connect(self.export_fig)
       
    def import_file(self):
        # file dialog pop up, user can choose a csv or a txt file
        path, ext = QFileDialog.getOpenFileName(None, "Please choose a file", "", "All Files (*);; CSV files (*.csv);; TXT files (*.txt)") 
        # return if there are no path or the file format is not correct
        if not (path.endswith('.csv') or path.endswith('.txt')):
            print('return')
            return
            
        self.data = EIS_object.from_file(path)
        # discard inductance data if necessary
        self.inductance_callback()
        self.statusBar().showMessage('Imported file: %s' % path, 1000)
    
    def inductance_callback(self):        
        if self.data is None:
            return
        
        elif self.ui.induct_choice.currentIndex() == 2:
            # discard inductive data
            self.data.freq = self.data.freq[-self.data.Z_double_prime>0]
            self.data.Z_prime = self.data.Z_prime[-self.data.Z_double_prime>0]
            self.data.Z_double_prime = self.data.Z_double_prime[-self.data.Z_double_prime>0]
            self.data.Z_exp = self.data.Z_prime + self.data.Z_double_prime*1j
            
        else: 
            # use original data otherwise
            self.data.freq = self.data.freq_0
            self.data.Z_prime = self.data.Z_prime_0
            self.data.Z_double_prime = self.data.Z_double_prime_0
            self.data.Z_exp = self.data.Z_exp_0
        
        self.data.tau = 1/self.data.freq # we assume that the collocation points equal to 1/freq as default
        self.data.tau_fine  = np.logspace(log10(self.data.tau.min())-0.5,log10(self.data.tau.max())+0.5,10*self.data.freq.shape[0])
        self.data.method = 'none'
        
        self.plotting_callback('EIS_data')
    
    def simple_run_callback(self):
        # callback for simple ridge regularization
        if self.data is None:
            return
        # we first read the parameters chosen by the users
        rbf_type = str(self.ui.discre_choice.currentText())
        data_used = str(self.ui.data_used_choice.currentText())
        induct_used = int(self.ui.induct_choice.currentIndex())# this needs to check.
        der_used = str(self.ui.der_choice.currentText())
        lambda_value = float(self.ui.reg_para_entry.text())
        shape_control = str(self.ui.shape_control_choice.currentText())
        coeff = float(self.ui.FWHM_entry.text())
        # perform computation
        self.data = Simple_run(self.data, rbf_type, data_used, induct_used, 
                               der_used, lambda_value, shape_control, coeff)
        self.plotting_callback('DRT_data')

    def bayesian_run_callback(self):
        # callback for bayesian regularization
        if self.data is None:
            return
        # we first read the parameters chosen by the users
        rbf_type = str(self.ui.discre_choice.currentText())
        data_used = str(self.ui.data_used_choice.currentText())
        induct_used = int(self.ui.induct_choice.currentIndex())# this needs to check.
        der_used = str(self.ui.der_choice.currentText())
        lambda_value = float(self.ui.reg_para_entry.text())
        sample_number = int(self.ui.sample_no_entry.text())
        shape_control = str(self.ui.shape_control_choice.currentText())
        coeff = float(self.ui.FWHM_entry.text())
        # perform computation
        self.data = Bayesian_run(self.data, rbf_type, data_used, induct_used, der_used, 
                                 lambda_value, sample_number,  shape_control, coeff)
        self.plotting_callback('DRT_data')
        
    def BHT_run_callback(self):
        # callback for Hilbert Transform run
        if self.data is None:
            return
        # we first read the parameters chosen by the users
        rbf_type = str(self.ui.discre_choice.currentText())
        der_used = str(self.ui.der_choice.currentText())
        shape_control = str(self.ui.shape_control_choice.currentText())# check this out
        coeff = float(self.ui.FWHM_entry.text())# check this out
        # perform computation
        self.data = BHT_run(self.data, rbf_type, der_used, shape_control, coeff)
        self.plotting_callback('DRT_data')
        
    def plotting_callback(self, plot_to_show):
        # not plotting anything if no data is imported
        if self.data == None:
            return
        # initalize the figure object
        fig = Figure_Canvas()
        # plot the kind of figure we want
        if plot_to_show == 'EIS_data':
            fig.EIS_data(self.data)
        elif plot_to_show == 'Magnitude':
            fig.Magnitude(self.data)
        elif plot_to_show == 'Phase':
            fig.Phase(self.data)
        elif plot_to_show == 'Re_data':
            fig.Re_data(self.data)
        elif plot_to_show == 'Im_data':
            fig.Im_data(self.data)
        elif plot_to_show == 'Re_residual':
            fig.Re_residual(self.data)
        elif plot_to_show == 'Im_residual':
            fig.Im_residual(self.data)    
        elif plot_to_show == 'DRT_data':
            fig.DRT_data(self.data)
        elif plot_to_show == 'Score':
            fig.Score(self.data)
        else:
            return
        # rendering the figure object on to the gui      
        graphicscene = QtWidgets.QGraphicsScene(20, 25, 650, 610)
        graphicscene.addWidget(fig)
        self.ui.plot_panel.setScene(graphicscene)
        self.ui.plot_panel.show()
    
    def export_DRT(self):
        # callback for exporting the DRT results
        # return if users have not conduct any computation
        if self.data == None:
            return
        # select path to save the result
        path, ext = QFileDialog.getSaveFileName(None, "Please directory to save the DRT result", 
                                                "", "CSV files (*.csv);; TXT files (*.txt)")
        
        if self.data.method == 'simple':
            with open(path, 'w', newline='') as save_file:
                writer = csv.writer(save_file)
                # first save L and R
                writer.writerow(['L', self.data.L])
                writer.writerow(['R', self.data.R])
                writer.writerow(['tau','gamma'])
                # after that save tau and gamma
                for n in range(self.data.out_tau_vec.shape[0]):
                    writer.writerow([self.data.out_tau_vec[n], self.data.gamma[n]])
            
        elif self.data.method == 'credit':
            with open(path, 'w', newline='') as save_file:
                writer = csv.writer(save_file)
                # first save L and R
                writer.writerow(['L', self.data.L])
                writer.writerow(['R', self.data.R])
                writer.writerow(['tau','MAP','Mean','Upperbound','Lowerbound'])
                # after that save tau, gamma, mean, upper bound and lower bound
                for n in range(self.data.out_tau_vec.shape[0]):
                    writer.writerow([self.data.out_tau_vec[n], self.data.gamma[n],
                                    self.data.mean[n], self.data.upper_bound[n], 
                                    self.data.lower_bound[n]] )
                        
        elif self.data.method == 'BHT':
            with open(path, 'w', newline='') as save_file:
                writer = csv.writer(save_file)
                # first save L and R
                writer.writerow(['L', self.data.mu_L_0])
                writer.writerow(['R', self.data.mu_R_inf])
                writer.writerow(['tau','gamma_Re','gamma_Im'])
                # after that save tau, gamma_re and gamma_im 
                for n in range(self.data.out_tau_vec.shape[0]):
                    writer.writerow([self.data.out_tau_vec[n], 
                                     self.data.mu_gamma_fine_re[n],
                                     self.data.mu_gamma_fine_im[n]])
    
    def export_EIS(self):
        # callback for exporting the EIS fitting results
        # return if users have not conduct any computation
        if self.data == None:
            return
        # select path to save the result
        path, ext = QFileDialog.getSaveFileName(None, "Please directory to save the EIS fitting result", 
                                                "", "CSV files (*.csv);; TXT files (*.txt)")
                        
        if self.data.method == 'BHT': # save result for BHT
            with open(path, 'w', newline='') as save_file:
                writer = csv.writer(save_file)
                writer.writerow(['s_res_re', self.data.out_scores['s_res_re'][0],
                                  self.data.out_scores['s_res_re'][1],
                                  self.data.out_scores['s_res_re'][2]])
                writer.writerow(['s_res_im', self.data.out_scores['s_res_im'][0],
                                  self.data.out_scores['s_res_im'][1],
                                  self.data.out_scores['s_res_im'][2]])
                writer.writerow(['s_mu_re', self.data.out_scores['s_mu_re']])
                writer.writerow(['s_mu_im', self.data.out_scores['s_mu_im']])
                writer.writerow(['s_HD_re', self.data.out_scores['s_HD_re']])
                writer.writerow(['s_HD_im', self.data.out_scores['s_HD_im']])
                writer.writerow(['s_JSD_re', self.data.out_scores['s_JSD_re']])
                writer.writerow(['s_JSD_im', self.data.out_scores['s_JSD_im']])
                writer.writerow(['freq', 'mu_Z_re','mu_Z_im','mu_H_re','mu_H_im',
                                 'Z_H_re_band','Z_H_im_band','Z_H_re_res','Z_H_im_res'])
                # save frequency, the fitted impedance and the residual
                for n in range(self.data.freq.shape[0]):
                    writer.writerow([self.data.freq[n], self.data.mu_Z_re[n],
                                     self.data.mu_Z_im[n], self.data.mu_Z_H_im_agm[n],
                                     self.data.band_re_agm[n], self.data.band_im_agm[n],
                                     self.data.res_H_re[n], self.data.res_H_im[n]])
                
        else: # save result for simple and bayesian run
            with open(path, 'w', newline='') as save_file:
                writer = csv.writer(save_file)
                writer.writerow(['freq','mu_Z_re','mu_Z_im','Z_re_res','Z_im_res'])
                # save frequency, the fitted impedance and the residual
                for n in range(self.data.freq.shape[0]):
                    writer.writerow([self.data.freq[n], self.data.mu_Z_re[n],
                                     self.data.mu_Z_im[n], self.data.res_re[n],
                                     self.data.res_im[n]])
    
    def export_fig(self):
        # export figure as png
        # return if users have not conduct any computation
        if self.data == None:
            return
        
        file_choices = "PNG (*.png)"        
        path, ext = QFileDialog.getSaveFileName(self,'Save file', '', file_choices)
        
        pixmap = QtGui.QPixmap(self.ui.plot_panel.viewport().size())
        self.ui.plot_panel.viewport().render(pixmap)
        pixmap.save(path)
        
        if path:
            self.statusBar().showMessage('Saved to %s' % path, 1000)
            

class Figure_Canvas(FigureCanvas):
    def __init__(self, parent=None, width=7.5, height=6.5, dpi=100):
        # create Figure under matplotlib.pyplot
        # deactivate the popping of another figure panel
        plt.ioff()
#        plt.rc('text', usetex=True)
        plt.rc('font', family='serif', size = 20)
        plt.rc('xtick', labelsize = 15)
        plt.rc('ytick', labelsize = 15)
        fig = plt.figure(figsize=(width, height), dpi=dpi) 
        # initalizing parent
        FigureCanvas.__init__(self, fig) 
        self.setParent(parent)
        self.axes = fig.add_subplot(111) # using add_subplot method
        fig.tight_layout()
        fig.subplots_adjust(left=0.14, bottom=0.13, right=0.9, top=0.9)
        
    def EIS_data(self, entry):
        # plot the data
        if entry.method == 'BHT':# for BHT run
            self.axes.plot(entry.mu_Z_re, -entry.mu_Z_im, 
                           'k', label = '$Z_\mu$(Regressed)', linewidth=3)
            self.axes.plot(entry.mu_Z_H_re_agm, -entry.mu_Z_H_im_agm, 
                           'b', label = '$Z_H$(Hilbert transform)', linewidth=3)
            self.axes.plot(entry.Z_prime, -entry.Z_double_prime, 'or')
            self.axes.legend(frameon = False, fontsize = 15, loc = 'upper left')
            
        elif entry.method != 'none':# for simple or bayesian run
            self.axes.plot(entry.mu_Z_re, -entry.mu_Z_im, 'k', linewidth=2)
            self.axes.plot(entry.Z_prime, -entry.Z_double_prime, 'or')
        
        else:# no computation for imported data yet
            self.axes.plot(entry.Z_prime, -entry.Z_double_prime, 'or')
        
        self.axes.set_xlabel('$Z^{\prime}$')
        self.axes.set_ylabel('-$Z^{\prime \prime}$')
        self.axes.ticklabel_format(axis="both", style="sci", scilimits=(0,0))
        self.axes.axis('equal')

    def Magnitude(self, entry):
        # plot magnitude
        if entry.method == 'BHT':# for BHT run
            self.axes.semilogx(entry.freq, absolute(entry.mu_Z_re+1j*entry.mu_Z_im), 
                               'k', label = '$Z_\mu$(Regressed)', linewidth=2)
            self.axes.semilogx(entry.freq, absolute(entry.mu_Z_H_re_agm+1j*entry.mu_Z_H_im_agm),
                               'b', label = '$Z_H$(Hilbert transform)', linewidth=2)
            self.axes.semilogx(entry.freq, absolute(entry.Z_exp), 'or')
            self.axes.legend(frameon = False, fontsize = 15, loc = 'upper left')
            
        elif entry.method != 'none':# for simple or bayesian run
            self.axes.semilogx(entry.freq, absolute(entry.mu_Z_re+1j*entry.mu_Z_im), 'k', linewidth=3)
            self.axes.semilogx(entry.freq, absolute(entry.Z_exp), 'or')
            
        else:# no computation for imported data yet
            self.axes.semilogx(entry.freq, absolute(entry.Z_exp), 'or')
        
        self.axes.set_xlim([min(entry.freq), max(entry.freq)])    
        self.axes.set_xlabel('$f$')
        self.axes.set_ylabel('$|Z|$')
        
    def Phase(self, entry):
        # plot phase angle
        if entry.method == 'BHT':# for BHT run
            self.axes.semilogx(entry.freq, angle(entry.mu_Z_re+1j*entry.mu_Z_im, deg = True),
                               'k', label = '$Z_\mu$(Regressed)', linewidth=2)
            self.axes.semilogx(entry.freq, angle(entry.mu_Z_H_re_agm+1j*entry.mu_Z_H_im_agm, deg = True),
                               'b', label = '$Z_H$(Hilbert transform)', linewidth=2)
            self.axes.semilogx(entry.freq, angle(entry.Z_exp, deg = True), 'or')
            self.axes.legend(frameon = False, fontsize = 15, loc = 'upper left')
        
        elif entry.method != 'none':# for simple or bayesian run
            self.axes.semilogx(entry.freq, angle(entry.mu_Z_re+1j*entry.mu_Z_im, deg = True), 'k', linewidth=3)
            self.axes.semilogx(entry.freq, angle(entry.Z_exp, deg = True), 'or')
            
        else:# no computation for imported data yet
            self.axes.semilogx(entry.freq, angle(entry.Z_exp, deg = True), 'or')
        
        self.axes.set_xlim([min(entry.freq), max(entry.freq)])    
        self.axes.set_xlabel('$f$')
        self.axes.set_ylabel('$angle/^\circ$')
        
    def Re_data(self, entry):
        # plot Re part
        if entry.method == 'BHT':# for BHT run
            self.axes.fill_between(entry.freq, entry.mu_Z_H_re_agm-3*entry.band_re_agm, entry.mu_Z_H_re_agm+3*entry.band_re_agm,  facecolor='lightgrey')
            self.axes.semilogx(entry.freq, entry.mu_Z_re, 'k', label = '$Z_\mu$(Regressed)', linewidth=3)
            self.axes.semilogx(entry.freq, entry.mu_Z_H_re_agm, 'b', label = '$Z_H$(Hilbert transform)', linewidth=3)
            self.axes.semilogx(entry.freq, entry.Z_prime, 'or')
            self.axes.legend(frameon = False, fontsize = 15, loc = 'upper left')
        
        elif entry.method != 'none':# for simple or bayesian run
            self.axes.semilogx(entry.freq, entry.mu_Z_re, 'k', linewidth=3)
            self.axes.semilogx(entry.freq, entry.Z_prime, 'or')
            
        else:
            self.axes.semilogx(entry.freq, entry.Z_prime, 'or')
        
        self.axes.set_xlim([min(entry.freq), max(entry.freq)])    
        self.axes.set_xlabel('$f$')
        self.axes.set_ylabel('$Z^{\prime}$')
        
    def Im_data(self, entry):
        # plot Re part
        if entry.method == 'BHT':# for BHT run
            self.axes.fill_between(entry.freq, -entry.mu_Z_H_im_agm-3*entry.band_im_agm, -entry.mu_Z_H_im_agm+3*entry.band_im_agm,  facecolor='lightgrey')
            self.axes.semilogx(entry.freq, -entry.mu_Z_im, 'k', label = '$Z_\mu$(Regressed)', linewidth=3)
            self.axes.semilogx(entry.freq, -entry.mu_Z_H_im_agm, 'b', label = '$Z_H$(Hilbert transform)', linewidth=3)
            self.axes.semilogx(entry.freq, -entry.Z_double_prime, 'or')
            self.axes.legend(frameon = False, fontsize = 15, loc = 'upper left')
            
        elif entry.method != 'none':# for simple or bayesian run
            self.axes.semilogx(entry.freq, -entry.mu_Z_im, 'k')
            self.axes.semilogx(entry.freq, -entry.Z_double_prime, 'or')
        
        else:   
            self.axes.semilogx(entry.freq, -entry.Z_double_prime, 'or')
        
        self.axes.set_xlim([min(entry.freq), max(entry.freq)])    
        self.axes.set_xlabel('$f$')
        self.axes.set_ylabel('-$Z^{\prime \prime}$')
        
    def Re_residual(self, entry):
        # plot the residual in the Re part
        if entry.method == 'none' :#or str(entry.ui.data_used_choice.currentText()) == 'Im Data':
            return
        
        elif entry.method == 'BHT':# for BHT run
            self.axes.fill_between(entry.freq, -3*entry.band_re_agm, 3*entry.band_re_agm,  facecolor='lightgrey')
            self.axes.semilogx(entry.freq, entry.res_H_re, 'or')
            self.axes.set_xlabel('$f$')
            self.axes.set_ylabel('$R_{\infty}+Z^{\prime}_{H}-Z^{\prime}_{exp}$')
            y_max = max(3*entry.band_re_agm)
        
        else:# for simple or bayesian run
            self.axes.semilogx(entry.freq, entry.res_re, 'or')
            self.axes.set_xlabel('$f$')
            self.axes.set_ylabel('$Z^{\prime}_{DRT}-Z^{\prime}_{exp}$')
            y_max = max(absolute(entry.res_re))
        
        self.axes.set_xlim([min(entry.freq), max(entry.freq)])    
        self.axes.set_ylim([-1.1*y_max, 1.1*y_max])
        self.axes.ticklabel_format(axis= 'y', style="sci", scilimits=(0,0))
          
    def Im_residual(self, entry):
        # plot the residual in the Im part
        if entry.method == 'none' :#or str(entry.ui.data_used_choice.currentText()) == 'Re Data':
            return
        
        elif entry.method == 'BHT':# for BHT run
            self.axes.fill_between(entry.freq, -3*entry.band_im_agm, 3*entry.band_im_agm,  facecolor='lightgrey')
            self.axes.semilogx(entry.freq, entry.res_H_im, 'or')
            self.axes.set_xlabel('$f$')
            self.axes.set_ylabel('$\omega L_0+Z^{\prime \prime}_{H}-Z^{\prime\prime}_{exp}$')
            y_max = max(3*entry.band_im_agm)
            
        else:# for simple or bayesian run
            self.axes.semilogx(entry.freq, entry.res_im, 'or')
            self.axes.set_xlabel('$f$')
            self.axes.set_ylabel('$Z^{\prime \prime}_{DRT}-Z^{\prime \prime}_{exp}$')
            y_max = max(absolute(entry.res_im))
            
        self.axes.set_xlim([min(entry.freq), max(entry.freq)])    
        self.axes.set_ylim([-1.1*y_max, 1.1*y_max])
        self.axes.ticklabel_format(axis = 'y', style="sci", scilimits=(0,0))
        
    def DRT_data(self, entry):
        # plot the DRT
        if entry.method == 'none':
            return
        
        elif entry.method == 'simple':
            self.axes.semilogx(entry.out_tau_vec, entry.gamma, 'k', linewidth=3)
            y_min = 0
            y_max = max(entry.gamma)
            
        elif entry.method == 'credit':
            self.axes.fill_between(entry.out_tau_vec, entry.lower_bound, entry.upper_bound,  facecolor='lightgrey')
            self.axes.semilogx(entry.out_tau_vec, entry.gamma, color='black', label='MAP', linewidth=3)
            self.axes.semilogx(entry.out_tau_vec, entry.mean, color='blue', label='mean', linewidth=3)
            self.axes.semilogx(entry.out_tau_vec, entry.lower_bound, color='black')
            self.axes.semilogx(entry.out_tau_vec, entry.upper_bound, color='black')
            self.axes.legend(frameon = False, fontsize = 15)
            y_min = 0
            y_max = max(entry.upper_bound)
            
        elif entry.method == 'BHT':
            self.axes.semilogx(entry.out_tau_vec, entry.mu_gamma_fine_re, 'b', linewidth = 3, label = '$Mean Re$')
            self.axes.semilogx(entry.out_tau_vec, entry.mu_gamma_fine_im, 'k', linewidth = 3, label = '$Mean Im$')
            y_min = min(np.concatenate((entry.mu_gamma_fine_re,entry.mu_gamma_fine_im)))
            y_max = max(np.concatenate((entry.mu_gamma_fine_re,entry.mu_gamma_fine_im)))
        
        self.axes.set_xlabel(r'$\tau/s$')
        self.axes.set_ylabel(r'$\gamma/\Omega$')
        self.axes.set_ylim([y_min, 1.1*y_max])
        self.axes.set_xlim([min(entry.out_tau_vec), max(entry.out_tau_vec)])
    
    def Score(self, entry):
        # plot EIS score
        if entry.method != 'BHT':
            return
        
        else: # for BHT method
            Re_part = np.array([entry.out_scores['s_res_re'][0], entry.out_scores['s_res_re'][1], entry.out_scores['s_res_re'][2],
                       entry.out_scores['s_mu_re'], entry.out_scores['s_HD_re'], entry.out_scores['s_JSD_re']])
            Im_part = np.array([entry.out_scores['s_res_im'][0], entry.out_scores['s_res_im'][1], entry.out_scores['s_res_im'][2],
                       entry.out_scores['s_mu_im'], entry.out_scores['s_HD_im'], entry.out_scores['s_JSD_im']])
            x = np.arange(6)  # the label locations
            width = 0.35  # the width of the bars
            
            self.axes.bar(x - width/2, Re_part*100, width, label='Re part', color = 'blue')
            self.axes.bar(x + width/2, Im_part*100, width, label='Im part', color = 'black')
            self.axes.plot([-0.5,5.5], [100,100], '--k')
            
            self.axes.legend(frameon = False, fontsize = 15)
            self.axes.set_ylim([0, 125])
            self.axes.set_xlim([-0.5, 5.5])
            self.axes.set_xticks(x) 
            self.axes.set_xticklabels((r'$s_{1\sigma}$', r'$s_{2\sigma}$', r'$s_{3\sigma}$', r'$s_{\mu}$', r'$s_{\rm HD}$', r'$s_{\rm JSD}$'))
            self.axes.set_yticks([0,50,100]) 
            self.axes.set_ylabel(r'$\rm Scores (\%)$')
            
if __name__ == "__main__":
    # starting the GUI when users run this file 
    environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
    app = QtWidgets.QApplication(sys.argv)
    app.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    MainWindow = pyDRTtools_GUI()
    MainWindow.show()
    sys.exit(app.exec_())
    

"""
check list:
1) pwl discretization
2) map array to gamma for BHT computation
3) computation consistency compare with MATLAB code
4) missing code in the position of "pass"
5) speed up code (e.g. loading plt.rc)
6) check the figure display
7) Update BHT run.
"""