# Adaptive-Resource-Provison-for-Cloud
Online Bin Packing Algorithm Used for Cloud Resource Allocation  

> Cloud Resource Allocation

- Paper：Adaptive Resource Provisioning for the Cloud Using Online Bin Packing
- Conference：IEEE TRANSACTIONS ON COMPUTERS, VOL 63, NO. 11, NOVEMBER 2014

# This project is an realization of the algorithm VISBP which is provided in the aforemetioned paper. 

- generate_data.py
  This module is to generate VM data for simulation from real trace data set.
- machine.py
  This module contains two classes Physical Machine and Virual Machine which are the abstraction of Bin and Item respectively.
- scheduler.py
  This module is responsible for scheduling VMs according to thier different categories.
- simulation.py
  In this module, simulations with different parameters can be taken.
