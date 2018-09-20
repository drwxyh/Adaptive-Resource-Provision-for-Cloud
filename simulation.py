#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
# @Time    : 2018/9/18 下午7:32
# @Author  : Charles
# @Contact : drwxyh@gmail.com
# @File    : simulation.py
# @Software: PyCharm

from queue import PriorityQueue
from generate_data import gen_data
from scheduler import VMScheduler

if __name__ == "__main__":
    # Generate the input
    num_vms = 1000
    num_slots = 1000
    num_pms = num_vms
    vm_list = gen_data(num_vms, num_slots)

    pq = PriorityQueue()
    for vm in vm_list:
        pq.put(vm)

    vmm = VMScheduler(num_pms, num_slots)

    for t in range(num_slots + 1):
        print('The {}th slot.'.format(t))
        cur_vm_list = list()
        while not pq.empty():
            vm = pq.get()
            if vm.start_time == t:
                cur_vm_list.append(vm)
            else:
                pq.put(vm)
                break

        vmm.vm_new = cur_vm_list
        # Arrange the new coming VMs on suitable PMs.
        vmm.insert()
        # Update the demand of running VMs.
        vmm.vm_re_categorize(t)
        # Update the category of active PMs.
        vmm.pm_re_categorize()
        # According to the change of VM's category, make a corresponding adjustment.
        vmm.change()
        # Integrate the set of new VMs and old VMs.
        vmm.integrate_vm_set()
        # Update the category of PMs.
        vmm.pm_re_categorize()
        vmm.pm_group_renew()
