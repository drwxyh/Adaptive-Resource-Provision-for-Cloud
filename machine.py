#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
# @Time    : 2018/9/18 下午7:32
# @Author  : Charles
# @Contact : drwxyh@gmail.com
# @File    : machine.py
# @Software: PyCharm


class VirtualMachine:
    """
    This class is the abstraction of Virtual Machine or Item in BinPacking.
    """

    def __init__(self, identifier, start_time, end_time, demands):
        """
        :param identifier: the id of this virtual machine
        :param start_time: time that vm needs to be served
        :param end_time: time that vm stops running
        :param demands: the number of vm's demand in each slot
        :param current_demand: the number of demand in current slot
        :param category: the category of this vm in current slot which if variable
        :param current_pm_id: the id of the pm this vm is running on in current slot which is variable
        :param length: the number of slots that the vm will run
        :type identifier: int
        :type start_time: int
        :type end_time: int
        :type demands: list(float)
        """
        self.id = identifier
        self.length = end_time - start_time + 1
        self.start_time = start_time
        self.end_time = end_time
        self.demands = demands
        self.current_demand = demands[0]
        self.category = self.get_category()
        self.pre_category = None
        self.current_pm_id = None
        self.pre_pm_id = self.current_pm_id

    def update(self, system_time):
        # Update the demand of vm according to the system time and its category.
        if system_time - self.start_time + 1 <= self.length:
            self.pre_category = self.category
            self.current_demand = self.demands[system_time - self.start_time]
            self.category = self.get_category()
        else:
            pass

    def get_category(self):
        # Determine this vm's category according to its current demand.
        if 0 < self.current_demand <= 1 / 3:
            return 'T'
        elif 1 / 3 < self.current_demand <= 1 / 2:
            return 'S'
        elif 1 / 2 < self.current_demand <= 2 / 3:
            return 'L'
        elif 2 / 3 < self.current_demand <= 1:
            return 'B'
        else:
            return None

    def __lt__(self, other):
        # In order to use queue.PriorityQueue, we must implement the less than operator for this class.
        if self.start_time < other.start_time:
            return True
        else:
            return False

    def __str__(self):
        res = 'VirtualMachine:\n - id:{} \n - start time:{} \n - end time:{} \n - demands:{}'
        return res.format(self.id, self.start_time, self.end_time, self.demands)


class PhysicalMachine:
    """
    This class is the abstraction of Physical Machine or Bin.
    """

    def __init__(self, identifier, capacity=1.0, gap=1.0, status=False, running_vms=None,
                 power_on_time=0,
                 power_off_time=0, num_slots=1000):
        """
        :param identifier: the identifier of Physical Machine
        :param capacity: calculation resource that pm can provide
        :param gap: calculation resource remained to be used
        :param status: the pm is either in idle state or active state
        :param running_vms: vms running by this pm
        :param power_on_time: time start to work
        :param power_off_time: time stop working
        :param num_slots: number of slots that system will run
        :type identifier: int
        :type capacity: float
        :type gap: float
        :type status: bool
        :type running_vms: set(vms)
        :type power_on_time: int
        :type power_off_time: int
        """
        self.id = identifier
        self.capacity = capacity
        self.status = status
        if running_vms is None:
            self.running_vms = set()
        else:
            self.running_vms = running_vms
        self.power_on_time = power_on_time
        self.power_off_time = power_off_time
        self.category = None
        self.gap = gap

    def update(self):
        # Update the pm category according to the change in its running vms.
        self.category = self.get_category()
        self.gap = self.get_gap()

    def get_gap(self):
        # Calculate the remained resource which can be used than.
        total_demand = 0.0
        for vm in self.running_vms:
            total_demand += vm.current_demand
        return self.capacity - total_demand

    def get_category(self):
        # Determine this pm's category according to the vms running on it.
        t_cnt, s_cnt, l_cnt, b_cnt = 0, 0, 0, 0
        item_num = len(self.running_vms)
        total_demand = 0.0
        for vm in self.running_vms:
            total_demand += vm.current_demand

        for vm in self.running_vms:
            vm_category = vm.get_category()
            if vm_category == 'T':
                t_cnt += 1
            elif vm_category == 'S':
                s_cnt += 1
            elif vm_category == 'L':
                l_cnt += 1
            elif vm_category == 'B':
                b_cnt += 1
            else:
                pass

        if item_num == 1 and b_cnt == 1:
            return 'B'

        if item_num == 1 and l_cnt == 1:
            if total_demand < 2 / 3:
                return 'ULLT'
            else:
                return 'L'

        if l_cnt == 1 and t_cnt == item_num - 1 and t_cnt >= 1:
            if total_demand < 2 / 3:
                return 'ULLT'
            else:
                return 'LT'

        if s_cnt == 1 and item_num == 1:
            return 'S'

        if s_cnt == 2 and item_num == 2:
            return 'SS'

        if l_cnt == 1 and s_cnt == 1 and item_num == 2:
            return 'LS'

        if t_cnt == item_num and t_cnt >= 1:
            if total_demand < 2 / 3:
                return 'UT'
            else:
                return 'T'

    def __str__(self):
        res = 'PhysicalMachine: \n - id:{} \n - capacity: {}\n - status:{}\n- utilization: {}'
        return res.format(self.id, self.capacity, self.status, self.utilization)
