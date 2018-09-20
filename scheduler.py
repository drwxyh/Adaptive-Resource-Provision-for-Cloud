#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
# @Time    : 2018/9/18 下午7:32
# @Author  : Charles
# @Contact : drwxyh@gmail.com
# @File    : scheduler.py
# @Software: PyCharm

from machine import PhysicalMachine, VirtualMachine


class VMScheduler:
    """
    This class is the abstraction of VM manager which is responsible for scheduling VMs to run on the
    appropriate PMs at each time slot.
    """

    def __init__(self, num_pms, num_slots):
        """
        :param num_pms:
        :param num_slots:
        """
        self.num_pms = num_pms
        self.num_slots = num_slots
        self.vm_set = list()
        self.vm_new = list()
        self.pm_set = dict()  # dict[id:pm]
        self.idle_pm_id = set()  # store idle pms
        self.active_pm_id = set()  # store running pms

        # Create PMs
        for i in range(self.num_pms):
            pm_id = i + 1
            pm = PhysicalMachine(pm_id, num_slots=1000)
            self.idle_pm_id.add(pm_id)
            self.pm_set[pm_id] = pm

        # Create PM Category
        pm_category = ['B', 'L', 'LT', 'S', 'SS', 'LS', 'T', 'UT', 'ULLT']
        self.pm_groups = dict()
        for x in pm_category:
            self.pm_groups[x] = set()

    def pm_group_renew(self):
        # According to the category of each PM, divide active PMs into different groups.
        self.pm_re_categorize()
        for x in self.pm_groups.keys():
            self.pm_groups[x].clear()

        empty_pm_id = set()
        for pm_id in self.active_pm_id:
            pm = self.pm_set[pm_id]
            pm.update()
            if not pm.category:
                empty_pm_id.add(pm.id)
                self.pm_set[pm.id] = PhysicalMachine(pm.id, num_slots=1000)

        for pm_id in empty_pm_id:
            self.active_pm_id.discard(pm_id)
            self.idle_pm_id.add(pm_id)

        for pm_id in self.active_pm_id:
            pm = self.pm_set[pm_id]
            self.pm_groups[pm.category].add(pm)

    def pm_re_categorize(self):
        # Re-categorize the PM, if the number of VMs running on it is none
        # then remove it from active_pm_id set, add it to idle_pm_id and re-initialize the PM.
        empty_pm_id = set()
        for pm_id in self.active_pm_id:
            if not self.pm_set[pm_id].running_vms:
                empty_pm_id.add(pm_id)

        for pm_id in empty_pm_id:
            self.active_pm_id.discard(pm_id)
            self.idle_pm_id.discard(pm_id)
            self.pm_set[pm_id] = PhysicalMachine(pm_id, num_slots=1000)
        for pm_id in self.active_pm_id:
            self.pm_set[pm_id].update()

    def vm_re_categorize(self, system_time):
        # Re-categorize the VM, if it's time to finish, then remove it from it's current running PM's running_vms,
        # and discard it from vm_set. Notice that if we remove a VM from an PM， the number of VMs running on it
        # maybe decrease to zero, so we must check the state of PM in the following step.
        finished_vms = set()
        for vm in self.vm_set:
            if system_time == vm.end_time:
                pm_id = vm.current_pm_id
                self.pm_set[pm_id].running_vms.discard(vm)
                finished_vms.add(vm)
        for vm in finished_vms:
            print('VM-{} finishes its work.'.format(vm.id))
            self.vm_set.remove(vm)
        for vm in self.vm_set:
            vm.update(system_time)

    def integrate_vm_set(self):
        # After the insert operation of new coming VMs and the change operation of old VMs, we should put them together.
        print('{} PMs is in active state.'.format(len(self.active_pm_id)))
        for vm in self.vm_new:
            self.vm_set.append(vm)
        self.vm_new = list()

    def divide(self, pm):
        # All T-items in a bin form several non-overlapping groups such that:
        # 1) the size of any group is no more than 1/3;
        # 2) the size of any two groups is larger than 1/3;
        res = list()
        vm_t_set = list()
        for vm in pm.running_vms:
            if vm.category == 'T':
                vm_t_set.append((vm.current_demand, vm))
        vm_t_set = sorted(vm_t_set, key=lambda x: x[0])
        temp = list()
        while len(vm_t_set):
            temp.append(vm_t_set.pop())
            total_demand = 0.0
            for x in temp:
                total_demand += x[0]
            if total_demand > 1 / 3:
                vm_t_set.insert(0, temp.pop())
                res.append(temp)
                temp = list()
        res.append(temp)

        result = list()
        for x in res:
            temp = list()
            for y in x:
                temp.append(y[1])
            result.append(temp)
        return result

    def new(self, vms):
        # Put VMs into a new PM. This operation means that we should get a PM from idle PM set and put it into active PM
        # set firstly. Then, VMs are put into the same PM, the new PM's category and PM group state should be updated.
        pm_id = self.idle_pm_id.pop()
        # print('{} is used.'.format(pm_id))
        self.active_pm_id.add(pm_id)
        pm = self.pm_set[pm_id]
        if isinstance(vms, VirtualMachine):
            vms.current_pm_id = pm_id
            pm.running_vms.add(vms)
        else:
            for vm in vms:
                vm.current_pm_id = pm_id
                pm.running_vms.add(vm)
        pm.update()
        self.pm_group_renew()
        return pm_id

    def hot(self, pm):
        # If the total demand of VMs running on the PM is larger than its capacity, we call this PM hot.
        total_demand = 0.0
        for vm in pm.running_vms:
            total_demand += vm.current_demand
        if total_demand > pm.capacity:
            return True
        else:
            return False

    def __exist(self, category, pm=None):
        num = len(self.pm_groups[category])
        if num == 0:
            return False
        if pm is not None:
            if num == 1 and pm in self.pm_groups[category]:
                return False
        else:
            return True

    def __get(self, category, pm=None):
        num = len(self.pm_groups[category])
        if num > 0:
            if pm is not None:
                if pm.category == category:
                    self.pm_groups[category].discard(pm)
            res = self.pm_groups[category].pop()
            self.pm_groups[category].add(res)
            if pm is not None:
                if pm.category == category:
                    self.pm_groups[category].add(pm)
            return res
        else:
            return None

    def move(self, vms, pm):
        # When we move VMs from its original PMs to the new PM, we should remove it from original PM's running set and
        # and add it to the new PM's running set.
        if isinstance(vms, VirtualMachine):
            pre_pm_id = vms.current_pm_id
            if pre_pm_id is not None:
                self.pm_set[pre_pm_id].running_vms.discard(vms)
                if len(self.pm_set[pre_pm_id].running_vms) == 0:
                    self.active_pm_id.discard(pre_pm_id)
                    self.idle_pm_id.add(pre_pm_id)
                    self.pm_set[pre_pm_id] = PhysicalMachine(pre_pm_id, num_slots=1000)
            vms.current_pm_id = pm.id
            pm.running_vms.add(vms)
        else:
            for vm in vms:
                pre_pm_id = vm.current_pm_id
                if pre_pm_id is not None:
                    self.pm_set[pre_pm_id].running_vms.discard(vm)
                    if len(self.pm_set[pre_pm_id].running_vms) == 0:
                        self.active_pm_id.discard(pre_pm_id)
                        self.idle_pm_id.add(pre_pm_id)
                        self.pm_set[pre_pm_id] = PhysicalMachine(pre_pm_id, num_slots=1000)
                vm.current_pm_id = pm.id
                pm.running_vms.add(vm)
        pm.update()
        self.pm_group_renew()

    def fillwith(self, vm_x):
        if self.__exist('ULLT'):
            pm_b = self.__get('ULLT')
            self.move(vm_x, pm_b)
        elif self.__exist('UT'):
            pm_b = self.__get('UT')
            self.move(vm_x, pm_b)
        else:
            self.new(vm_x)

    def fill(self, pm_b):
        if pm_b.category == 'L' or pm_b.category == 'LT':
            while pm_b.gap >= 1 / 3 and self.__exist('T'):
                if self.__exist('UT'):
                    ut = self.__get('UT')
                    group_choice = self.divide(ut)
                    g = group_choice.pop()
                    self.move(g, pm_b)
                else:
                    t = self.__get('T')
                    group_choice = self.divide(t)
                    g = group_choice.pop()
                    self.move(g, pm_b)

    def insert_s_item(self, vm_x):
        if self.__exist('S'):
            pm_b = self.__get('S')
            self.move(vm_x, pm_b)
        else:
            self.new(vm_x)

    def release(self, pm):
        pm_id = pm.id
        while len(pm.running_vms) != 0:
            vm = pm.running_vms.pop()
            self.fillwith(vm)
        self.active_pm_id.discard(pm_id)
        self.idle_pm_id.add(pm_id)
        # print('{} is released.'.format(pm_id))
        self.pm_set[pm_id] = PhysicalMachine(pm_id, num_slots=1000)
        self.pm_group_renew()

    def adjust(self, pm_b):
        if pm_b.category == 'LT' or pm_b.category == 'T':
            while self.hot(pm_b):
                g = pm_b.running_vms.pop()
                self.fillwith(g)
            if pm_b.gap >= 1 / 3:
                self.fill(pm_b)

    def insert(self):
        for vm in self.vm_new:
            print('VM-{} starts running now.'.format(vm.id))
            if vm.category == 'B':
                self.new(vm)
            elif vm.category == 'L':
                pm_id = self.new(vm)
                pm = self.pm_set[pm_id]
                self.fill(pm)
            elif vm.category == 'S':
                self.insert_s_item(vm)
            else:
                self.fillwith(vm)

    def __exist_s_item(self, pm, vm_x=None):
        num = 0
        for vm in pm.running_vms:
            if vm.category == 'S':
                num += 1
        if vm_x is not None:
            if vm_x.category == 'S':
                num -= 1
        if num <= 0:
            return False
        else:
            return True

    def __get_s_item(self, pm, vm_x=None):
        s_set = set()
        for vm in pm.running_vms:
            if vm.category == 'S':
                s_set.add(vm)
        if vm_x is not None:
            if vm_x.category == 'S':
                s_set.discard(vm_x)
        if len(s_set) != 0:
            return s_set.pop()

    def __exist_l_item(self, pm, vm_x=None):
        num = 0
        for vm in pm.running_vms:
            if vm.category == 'L':
                num += 1
        if vm_x is not None:
            if vm_x.category == 'L':
                num -= 1
        if num <= 0:
            return False
        else:
            return True

    def __get_l_item(self, pm, vm_x=None):
        l_set = set()
        for vm in pm.running_vms:
            if vm.category == 'L':
                l_set.add(vm)
        if vm_x is not None:
            if vm_x.category == 'L':
                l_set.discard(vm_x)
        if len(l_set) != 0:
            return l_set.pop()

    def change(self):
        for vm in self.vm_set:
            pm = self.pm_set[vm.current_pm_id]
            pre = vm.pre_category
            cur = vm.category
            if pre == 'B' and cur == 'L':
                self.fill(pm)

            elif pre == 'B' and cur == 'S':
                if self.__exist('S', pm):
                    pm_b = self.__get('S', pm)
                    self.move(vm, pm_b)

            elif pre == 'B' and cur == 'T':
                if self.__exist('ULLT', pm):
                    pm_b = self.__get('ULLT', pm)
                    self.move(vm, pm_b)
                else:
                    if self.__exist('UT', pm):
                        pm_b = self.__get('UT', pm)
                        self.move(vm, pm_b)

            elif pre == 'L' and cur == 'B':
                self.release(pm)

            elif pre == 'L' and cur == 'L':
                self.adjust(pm)

            elif pre == 'L' and cur == 'S':
                if self.__exist('S', pm):
                    pm_b = self.__get('S', pm)
                    self.move(vm, pm_b)

            elif pre == 'L' and cur == 'T':
                if self.__exist('T', pm):
                    while self.__exist('UT', pm):
                        pm_b = self.__get('UT')
                        group_choice = self.divide(pm)
                        g = group_choice.pop()
                        self.move(g, pm_b)
                else:
                    while self.__exist('ULLT', pm):
                        pm_b = self.__get('ULLT', pm)
                        group_choice = self.divide(pm)
                        g = group_choice.pop()
                        self.move(g, pm_b)

            elif pre == 'S' and cur == 'B':
                if self.__exist_s_item(pm):
                    s_item = self.__get_s_item(pm)
                    self.insert_s_item(s_item)

            elif pre == 'S' and cur == 'L':
                if self.__exist_s_item(pm):
                    s_item = self.__get_s_item(pm)
                    self.insert_s_item(s_item)
                    self.fill(pm)

            elif pre == 'S' and cur == 'T':
                if self.__exist_s_item(pm) and self.__exist('S', pm):
                    s_item = self.__get_s_item(pm)
                    pm_b = self.__get('S', pm)
                    self.move(s_item, pm_b)
                if self.__exist('ULLT', pm):
                    pm_b = self.__get('ULLT', pm)
                    self.move(vm, pm_b)
                elif self.__exist('UT', pm):
                    pm_b = self.__get('UT', pm)
                    self.move(vm, pm_b)
                else:
                    if self.__exist_s_item(pm):
                        pm.running_vms.discard(vm)
                        self.new(vm)

            elif pre == 'T' and cur == 'B':
                if self.__exist_l_item(pm):
                    vm_x = self.__get_l_item(pm)
                    pm.running_vms.discard(vm_x)
                    self.new(vm_x)
                    self.release(pm)

            elif pre == 'T' and cur == 'L':
                if self.__exist_l_item(pm, vm):
                    vm_x = self.__get_l_item(pm, vm)
                    new_pm_id = self.new(vm_x)
                    self.fill(self.pm_set[new_pm_id])
                    self.adjust(pm)

            elif pre == 'T' and cur == 'S':
                if self.__exist_l_item(pm):
                    vm_x = self.__get_l_item(pm)
                    self.insert_s_item(vm)
                    self.fill(self.pm_set[vm_x.current_pm_id])
                elif self.__exist('S', pm):
                    pm_b = self.__get('S')
                    t_group = self.divide(pm)
                    while self.__exist('UT', pm) and t_group:
                        pm_c = self.__get('UT', pm)
                        g = t_group.pop()
                        self.move(g, pm_c)
                    self.move(vm, pm_b)
                else:
                    self.release(pm)

            elif pre == 'T' and cur == 'T':
                if self.__exist_l_item(pm, vm):
                    self.adjust(pm)
                else:
                    if self.hot(pm):
                        self.fillwith(vm)
                    else:
                        while pm.gap >= 1 / 3 and self.__exist('UT', pm):
                            pm_b = self.__get('UT', pm)
                            t_group = self.divide(pm_b)
                            g = t_group.pop()
                            self.move(g, pm)

            else:
                pass
