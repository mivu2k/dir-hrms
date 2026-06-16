<template>
  <div class="space-y-6 animate-fade-in">
    <!-- Generate Payroll Header Widget (Accountant/HR Only) -->
    <div v-if="isAccountant" class="bg-slate-900/40 backdrop-blur-md border border-slate-900 rounded-xl p-6 shadow-lg">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div class="space-y-1">
          <h3 class="text-sm font-bold text-white uppercase tracking-wider">Generate Monthly Payroll Run</h3>
          <p class="text-xs text-slate-400">Processes basic wages, late arrival penalties, absent deductions, overtime, and taxes.</p>
        </div>

        <div class="flex flex-wrap items-center gap-3">
          <!-- Month -->
          <select v-model="runForm.month" class="form-select w-28">
            <option v-for="m in 12" :key="m" :value="m">{{ getMonthName(m) }}</option>
          </select>
          <!-- Year -->
          <select v-model="runForm.year" class="form-select w-24">
            <option :value="2026">2026</option>
            <option :value="2027">2027</option>
          </select>
          <!-- Generate Button -->
          <button 
            @click="generatePayroll"
            :disabled="runSaving"
            class="bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-4 py-2 rounded-lg text-xs transition-colors flex items-center space-x-2 cursor-pointer disabled:opacity-50"
          >
            <span v-if="runSaving">Generating...</span>
            <span v-else>Calculate Run</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Active Payroll Processing Cycles (Accountant/HR Only) -->
    <div v-if="isAccountant && payrolls.length > 0" class="bg-slate-900/40 backdrop-blur-md border border-slate-900 rounded-xl p-6 shadow-lg">
      <h3 class="text-sm font-bold text-white uppercase tracking-wider mb-4">Active Payroll Cycles</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div 
          v-for="p in payrolls" 
          :key="p.id"
          class="bg-slate-950/60 border border-slate-900 rounded-lg p-4 flex items-center justify-between"
        >
          <div>
            <p class="text-xs font-semibold text-white">Payroll Period: {{ p.year }} - {{ getMonthName(p.month) }}</p>
            <p class="text-xxs text-slate-500 mt-1">Generated: {{ formatTimestamp(p.generated_at) }}</p>
          </div>
          <div class="flex items-center space-x-3">
            <span :class="[
              p.status === 'PAID' || p.status === 'APPROVED' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border-amber-500/20',
              'px-2 py-0.5 rounded border text-xxs font-medium'
            ]">{{ p.status }}</span>
            <button 
              v-if="p.status === 'DRAFT' && isHR"
              @click="approvePayrollCycle(p.id)"
              class="bg-emerald-600 hover:bg-emerald-500 text-white font-medium px-3 py-1 rounded text-xxs cursor-pointer"
            >Finalize Run</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Payslips Grid -->
    <div class="bg-slate-900/40 backdrop-blur-md border border-slate-900 rounded-xl p-6 shadow-lg">
      <h3 class="text-sm font-bold text-white uppercase tracking-wider mb-4">Payslips Records</h3>
      
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="border-b border-slate-800 text-slate-400 font-semibold uppercase">
              <th class="py-2.5">Period</th>
              <th class="py-2.5" v-if="isAccountant">Employee</th>
              <th class="py-2.5">Basic Salary</th>
              <th class="py-2.5">Allowances / OT</th>
              <th class="py-2.5">Deductions</th>
              <th class="py-2.5">Net Payout</th>
              <th class="py-2.5">Status</th>
              <th class="py-2.5 text-right">Receipt</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="payslips.length === 0" class="border-b border-slate-900">
              <td colspan="8" class="py-6 text-center text-slate-500">No payslips calculated yet.</td>
            </tr>
            <tr 
              v-for="p in payslips" 
              :key="p.id" 
              class="border-b border-slate-900/60 hover:bg-slate-800/20 transition-colors"
            >
              <td class="py-2.5 font-medium text-slate-200">
                {{ p.payroll.year }} - {{ getMonthName(p.payroll.month) }}
              </td>
              <td class="py-2.5 font-semibold text-white" v-if="isAccountant">
                {{ p.employee.first_name }} {{ p.employee.last_name }}
                <span class="block text-xxs font-mono font-normal text-slate-500 mt-0.5">{{ p.employee.employee_id }}</span>
              </td>
              <td class="py-2.5 font-mono text-slate-300">Rs. {{ formatCurrency(p.basic_salary) }}</td>
              <td class="py-2.5">
                <span class="text-slate-300">Rs. {{ formatCurrency(p.allowances) }}</span>
                <span v-if="p.overtime_amount > 0" class="block text-xxs text-emerald-400 mt-0.5">OT: +{{ formatCurrency(p.overtime_amount) }}</span>
              </td>
              <td class="py-2.5 text-rose-400">
                Rs. {{ formatCurrency(calculateTotalDeductions(p)) }}
              </td>
              <td class="py-2.5 font-bold text-white">Rs. {{ formatCurrency(p.net_salary) }}</td>
              <td class="py-2.5">
                <span :class="[
                  p.status === 'PAID' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border-amber-500/20',
                  'px-2 py-0.5 rounded border text-xxs font-semibold'
                ]">{{ p.status }}</span>
              </td>
              <td class="py-2.5 text-right">
                <button 
                  @click="openPayslipDetails(p)"
                  class="bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-400 border border-indigo-500/10 font-semibold px-3 py-1 rounded text-xxs transition-colors cursor-pointer"
                >View Payslip</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Payslip itemized details card overlay -->
    <div v-if="selectedPayslip" class="fixed inset-0 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm z-50">
      <div class="bg-slate-900 border border-slate-800 w-full max-w-lg rounded-xl p-6 shadow-2xl space-y-6 max-h-screen overflow-y-auto" id="payslip-modal">
        <!-- Brand Header -->
        <div class="flex items-start justify-between border-b border-slate-800 pb-4">
          <div class="flex items-center space-x-2">
            <div class="w-8 h-8 rounded bg-indigo-600 flex items-center justify-center font-bold text-white text-base">A</div>
            <div>
              <h4 class="font-bold text-white text-sm">Antigravity Corp</h4>
              <p class="text-xxs text-slate-500">Employee Payslip Statement</p>
            </div>
          </div>
          <button @click="selectedPayslip = null" class="text-slate-400 hover:text-white cursor-pointer no-print">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Meta info grid -->
        <div class="grid grid-cols-2 gap-4 text-xxs border-b border-slate-800 pb-4">
          <div>
            <p class="text-slate-500 font-semibold uppercase">Employee Details</p>
            <p class="text-white font-bold mt-1 text-xs">{{ selectedPayslip.employee.first_name }} {{ selectedPayslip.employee.last_name }}</p>
            <p class="text-slate-300 font-mono mt-0.5">ID: {{ selectedPayslip.employee.employee_id }}</p>
          </div>
          <div>
            <p class="text-slate-500 font-semibold uppercase">Salary Period</p>
            <p class="text-white font-bold mt-1 text-xs">{{ getMonthName(selectedPayslip.payroll.month) }} {{ selectedPayslip.payroll.year }}</p>
            <p class="text-slate-300 mt-0.5">Payout Status: {{ selectedPayslip.status }}</p>
          </div>
        </div>

        <!-- Allowances vs Deductions Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
          <!-- Allowances Column -->
          <div class="space-y-3">
            <p class="font-bold text-emerald-400 uppercase tracking-wider text-xxs">Earnings & Allowances</p>
            <div class="space-y-2 bg-slate-950/40 p-3 rounded-lg border border-slate-900">
              <div class="flex justify-between">
                <span class="text-slate-400">Basic Pay</span>
                <span class="font-mono text-slate-200">Rs. {{ formatCurrency(selectedPayslip.basic_salary) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-400">Allowances</span>
                <span class="font-mono text-slate-200">Rs. {{ formatCurrency(selectedPayslip.allowances) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-400">Overtime Pay</span>
                <span class="font-mono text-emerald-400">+ Rs. {{ formatCurrency(selectedPayslip.overtime_amount) }}</span>
              </div>
              <div class="flex justify-between font-bold border-t border-slate-800 pt-2 text-white">
                <span>Total Earnings</span>
                <span class="font-mono">Rs. {{ formatCurrency(Number(selectedPayslip.basic_salary) + Number(selectedPayslip.allowances) + Number(selectedPayslip.overtime_amount)) }}</span>
              </div>
            </div>
          </div>

          <!-- Deductions Column -->
          <div class="space-y-3">
            <p class="font-bold text-rose-400 uppercase tracking-wider text-xxs">Deductions & Taxes</p>
            <div class="space-y-2 bg-slate-950/40 p-3 rounded-lg border border-slate-900">
              <div class="flex justify-between">
                <span class="text-slate-400">Late Penalties</span>
                <span class="font-mono text-rose-400">- Rs. {{ formatCurrency(selectedPayslip.late_deduction) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-400">Absent Days</span>
                <span class="font-mono text-rose-400">- Rs. {{ formatCurrency(selectedPayslip.leave_deduction) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-400">Income Tax</span>
                <span class="font-mono text-rose-400">- Rs. {{ formatCurrency(selectedPayslip.tax_deduction) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-400">EOBI Contribution</span>
                <span class="font-mono text-rose-400">- Rs. {{ formatCurrency(selectedPayslip.eobi_deduction) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-400">Provident Fund</span>
                <span class="font-mono text-rose-400">- Rs. {{ formatCurrency(selectedPayslip.provident_fund_deduction) }}</span>
              </div>
              <div class="flex justify-between font-bold border-t border-slate-800 pt-2 text-rose-400">
                <span>Total Deductions</span>
                <span class="font-mono">Rs. {{ formatCurrency(calculateTotalDeductions(selectedPayslip)) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Net Salary Statement -->
        <div class="bg-indigo-950/20 border border-indigo-950/50 rounded-xl p-4 flex items-center justify-between text-xs font-bold text-white">
          <span class="uppercase tracking-wider">Net Salary Payout</span>
          <span class="text-lg font-mono text-indigo-400">Rs. {{ formatCurrency(selectedPayslip.net_salary) }}</span>
        </div>

        <!-- Actions -->
        <div class="flex items-center justify-end space-x-3 border-t border-slate-800 pt-4 no-print">
          <button @click="selectedPayslip = null" class="px-4 py-2 border border-slate-800 text-slate-400 hover:text-white rounded-lg text-xs cursor-pointer">Close</button>
          <button @click="printPayslip" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium cursor-pointer shadow-lg shadow-indigo-600/20">Print statement</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useAuthStore } from '../stores/auth';
import axios from 'axios';

const authStore = useAuthStore();

const payslips = ref([]);
const payrolls = ref([]);

const selectedPayslip = ref(null);

const runSaving = ref(false);
const runForm = ref({
  month: new Date().getMonth() + 1, // Current month
  year: 2026
});

const isHR = computed(() => {
  return ['SUPER_ADMIN', 'HR_MANAGER'].includes(authStore.userRole);
});

const isAccountant = computed(() => {
  return ['SUPER_ADMIN', 'ACCOUNTANT', 'HR_MANAGER'].includes(authStore.userRole);
});

const fetchPayslips = async () => {
  try {
    const res = await axios.get('/payroll/payslips');
    payslips.value = res.data;
  } catch (err) {
    console.error('Error fetching payslips:', err);
  }
};

const fetchPayrolls = async () => {
  if (!isAccountant.value) return;
  try {
    const res = await axios.get('/payroll/payrolls');
    payrolls.value = res.data;
  } catch (err) {
    console.error('Error fetching payroll runs:', err);
  }
};

const generatePayroll = async () => {
  runSaving.value = true;
  try {
    const res = await axios.post('/payroll/payrolls/generate', {
      month: Number(runForm.value.month),
      year: Number(runForm.value.year)
    });
    alert(res.data.message);
    await Promise.all([fetchPayslips(), fetchPayrolls()]);
  } catch (err) {
    console.error(err);
    alert('Failed to generate payroll: ' + (err.response?.data?.detail || 'API Error'));
  } finally {
    runSaving.value = false;
  }
};

const approvePayrollCycle = async (id) => {
  if (!confirm('Are you sure you want to approve this payroll cycle? This will lock calculations and release all payslips.')) return;
  try {
    await axios.post(`/payroll/payrolls/${id}/approve`);
    await Promise.all([fetchPayslips(), fetchPayrolls()]);
  } catch (err) {
    console.error(err);
    alert('Failed to approve run: ' + (err.response?.data?.detail || 'API Error'));
  }
};

const openPayslipDetails = (payslip) => {
  selectedPayslip.value = payslip;
};

const printPayslip = () => {
  window.print();
};

const calculateTotalDeductions = (p) => {
  return Number(p.late_deduction) + Number(p.leave_deduction) + Number(p.tax_deduction) + Number(p.eobi_deduction) + Number(p.provident_fund_deduction);
};

const formatCurrency = (val) => {
  if (!val) return '0.00';
  return Number(val).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

const formatTimestamp = (iso) => {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' });
};

const getMonthName = (m) => {
  const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  return months[m - 1];
};

onMounted(() => {
  fetchPayslips();
  fetchPayrolls();
});
</script>

<style scoped>
.form-select {
  background-color: var(--color-slate-950);
  border: 1px solid var(--color-slate-800);
  border-radius: 0.5rem;
  padding: 0.5rem 0.75rem;
  color: #ffffff;
  font-size: 0.75rem;
}
.form-select:focus {
  outline: none;
  border-color: var(--color-brand-500);
}

/* Print CSS Styles mapping */
@media print {
  body * {
    visibility: hidden;
  }
  #payslip-modal, #payslip-modal * {
    visibility: visible;
  }
  #payslip-modal {
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    background: white !important;
    color: black !important;
    border: none !important;
  }
  #payslip-modal * {
    color: black !important;
  }
  .no-print {
    display: none !important;
  }
}
</style>
