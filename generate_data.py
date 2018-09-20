#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
# @Time    : 2018/9/18 下午7:32
# @Author  : Charles
# @Contact : drwxyh@gmail.com
# @File    : generate_data.py
# @Software: PyCharm

import random
import csv
import math
from machine import *


def gen_data(num_vms, num_slots):
    vm_list = list()
    with open('vm.csv') as fp:
        # The format of each line is that: id,start_time,end_time,demand
        f_csv = csv.reader(fp)
        headers = next(f_csv)
        for i in range(0, num_vms):
            row = next(f_csv)
            id, start_time, end_time, demand = row
            start_time = (int(start_time) + math.ceil(random.uniform(0, 500))) % num_slots
            end_time = min(start_time + math.ceil(random.normalvariate(300, 0.1)), 1000)

            down_demand = min(1.0, float(demand) * 10)
            up_demand = min(1.0, float(demand) * 20)
            demands = list()
            length = end_time - start_time + 1
            for j in range(length):
                demands.append(random.uniform(down_demand, up_demand))
            vm = VirtualMachine(int(id), start_time, end_time, demands)
            vm_list.append(vm)

    return vm_list
