<template>
  <div class="space-y-6">
    <!-- Leave Balances Row -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div 
        v-for="b in balances" 
        :key="b.id"
        class="bg-slate-900/40 backdrop-blur-md border border-slate-900 rounded-xl p-6 shadow-lg flex items-center justify-between"
      >
        <div class="space-y-1">
          <p class="text-xs font-semibold uppercase tracking-wider text-slate-400">{{ b.leave_type.name }} Balance</p>
          <p class="text-3xl font-bold text-white">
            {{ Number(b.allocated_days) - Number(b.used_days) }} 
            <span class="text-xs text-slate-400 font-normal">/ {{ b.allocated_days }} days left</span>
          </p>
        </div>
        <div class="w-12 h-12 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
          <span class="font-mono font-bold text-base">{{ b.leave_type.code }}</span>
        </div>
      </div>
      <div v-if="balances.length === 0" class="md:col-span-3 text-center py-6 bg-slate-900/20 border border-slate-900 rounded-xl text-slate-400 text-xs">
        No leave balances allocated for the current year.
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Leave Submission Form -->
      <div class="bg-slate-900/40 backdrop-blur-md border border-slate-900 rounded-xl p-6 shadow-lg h-fit">
        <h3 class="text-sm font-bold text-white uppercase tracking-wider mb-2">Request Leave</h3>
        <p class="text-xs text-slate-400 mb-6">Submit a request to your manager for time off approval.</p>

        <form @submit.prevent="submitLeave" class="space-y-4">
          <div>
            <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1">Leave Type *</label>
            <select v-model="form.leave_type_id" required class="form-select">
              <option v-for="b in balances" :key="b.leave_type.id" :value="b.leave_type.id">{{ b.leave_type.name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1">Start Date *</label>
            <input v-model="form.start_date" type="date" required class="form-input" />
          </div>
          <div>
            <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1">End Date *</label>
            <input v-model="form.end_date" type="date" required class="form-input" />
          </div>
          <div>
            <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1">Reason *</label>
            <textarea v-model="form.reason" required rows="3" class="form-input" placeholder="Explain the reason for leave..."></textarea>
          </div>

          <p v-if="formError" class="text-rose-400 text-xs font-semibold">{{ formError }}</p>

          <button 
            type="submit" 
            :disabled="formSaving"
            class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-2.5 rounded-lg shadow-lg shadow-indigo-600/30 transition-colors flex items-center justify-center space-x-2 cursor-pointer disabled:opacity-50 text-xs"
          >
            <span v-if="formSaving">Submitting...</span>
            <span v-else>Submit Leave Request</span>
          </button>
        </form>
      </div>

      <!-- Leave Requests Archive List -->
      <div class="bg-slate-900/40 backdrop-blur-md border border-slate-900 rounded-xl p-6 shadow-lg lg:col-span-2">
        <h3 class="text-sm font-bold text-white uppercase tracking-wider mb-4">Leave Requests Log</h3>
        
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse text-xs">
            <thead>
              <tr class="border-b border-slate-800 text-slate-400 font-semibold uppercase">
                <th class="py-2.5">Date Range</th>
                <th class="py-2.5">Type</th>
                <th class="py-2.5">Days</th>
                <th class="py-2.5">Reason</th>
                <th class="py-2.5">Status</th>
                <th class="py-2.5 text-right">Approvals / Comments</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="requests.length === 0" class="border-b border-slate-900">
                <td colspan="6" class="py-4 text-center text-slate-500">No leave requests submitted yet.</td>
              </tr>
              <tr 
                v-for="r in requests" 
                :key="r.id" 
                class="border-b border-slate-900/60 hover:bg-slate-800/20 transition-colors"
              >
                <td class="py-2.5 font-medium text-slate-200">
                  {{ r.start_date }} <span class="text-slate-500 text-xxs font-normal">to</span> {{ r.end_date }}
                </td>
                <td class="py-2.5 font-semibold text-white">{{ r.leave_type.code }}</td>
                <td class="py-2.5 font-bold text-slate-300">{{ r.total_days }}</td>
                <td class="py-2.5 text-slate-400 text-xxs max-w-xxs truncate" :title="r.reason">{{ r.reason }}</td>
                <td class="py-2.5">
                  <span :class="[
                    r.status === 'APPROVED' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : '',
                    r.status === 'MANAGER_APPROVED' ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' : '',
                    r.status === 'PENDING' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : '',
                    r.status === 'REJECTED' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' : '',
                    'px-2 py-0.5 rounded border text-xxs font-medium'
                  ]">{{ formatStatus(r.status) }}</span>
                </td>
                <td class="py-2.5 text-right text-xxs text-slate-400">
                  <span v-if="r.comments" class="italic" :title="r.comments">{{ r.comments }}</span>
                  <span v-else class="text-slate-500">—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Manager Leave Approvals Section (Show only if Direct Manager or HR/Super Admin) -->
    <div v-if="isApprover" class="bg-slate-900/40 backdrop-blur-md border border-slate-900 rounded-xl p-6 shadow-lg">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-sm font-bold text-white uppercase tracking-wider">Leaves Pending Approvals</h3>
        <p class="text-xxs text-slate-500">Multi-tier manager & HR sign-off dashboard</p>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="border-b border-slate-800 text-slate-400 font-semibold uppercase">
              <th class="py-3">Employee</th>
              <th class="py-3">Leave Range</th>
              <th class="py-3">Type</th>
              <th class="py-3">Days</th>
              <th class="py-3">Reason</th>
              <th class="py-3">Workflow State</th>
              <th class="py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="pendingApprovals.length === 0" class="border-b border-slate-900">
              <td colspan="7" class="py-6 text-center text-slate-500">No leave requests currently pending your approval.</td>
            </tr>
            <tr 
              v-for="r in pendingApprovals" 
              :key="r.id" 
              class="border-b border-slate-900 hover:bg-slate-800/20 transition-colors"
            >
              <td class="py-3 font-semibold text-white">
                {{ r.employee.first_name }} {{ r.employee.last_name }}
                <span class="block text-xxs font-mono font-normal text-slate-500 mt-0.5">{{ r.employee.employee_id }}</span>
              </td>
              <td class="py-3 font-medium text-slate-200">{{ r.start_date }} to {{ r.end_date }}</td>
              <td class="py-3 font-semibold text-indigo-400">{{ r.leave_type.name }}</td>
              <td class="py-3 font-bold text-slate-300">{{ r.total_days }} days</td>
              <td class="py-3 text-slate-400 text-xxs max-w-xs truncate" :title="r.reason">{{ r.reason }}</td>
              <td class="py-3">
                <span :class="[
                  r.status === 'PENDING' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
                  'px-2 py-0.5 rounded border text-xxs font-medium'
                ]">
                  {{ r.status === 'PENDING' ? 'Pending Mgr' : 'Pending HR' }}
                </span>
              </td>
              <td class="py-3 text-right space-x-2">
                <button 
                  @click="approveLeave(r)" 
                  class="bg-emerald-600 hover:bg-emerald-500 text-white font-medium px-3 py-1 rounded text-xxs cursor-pointer"
                >
                  {{ r.status === 'PENDING' ? 'Mgr Approve' : 'HR Confirm' }}
                </button>
                <button 
                  @click="rejectLeave(r)" 
                  class="bg-rose-600 hover:bg-rose-500 text-white font-medium px-3 py-1 rounded text-xxs cursor-pointer"
                >Reject</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useAuthStore } from '../stores/auth';
import axios from 'axios';

const authStore = useAuthStore();

const balances = ref([]);
const requests = ref([]);
const approvalsList = ref([]); // Holds raw requests for manager pending lists

const formSaving = ref(false);
const formError = ref(null);

const form = ref({
  leave_type_id: '',
  start_date: new Date().toISOString().substr(0, 10),
  end_date: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString().substr(0, 10),
  reason: ''
});

const isApprover = computed(() => {
  return ['SUPER_ADMIN', 'HR_MANAGER', 'HR_OFFICER', 'DEPT_MANAGER', 'TEAM_LEAD'].includes(authStore.userRole);
});

// Pending list filter: return requests that need action
const pendingApprovals = computed(() => {
  const role = authStore.userRole;
  return approvalsList.value.filter(r => {
    // If request is finalized, skip
    if (r.status === 'APPROVED' || r.status === 'REJECTED') return false;
    
    // If pending manager, display to department managers, super admins, HR
    if (r.status === 'PENDING') return true;
    
    // If manager_approved, display only to HR / Super Admin
    if (r.status === 'MANAGER_APPROVED') {
      return ['SUPER_ADMIN', 'HR_MANAGER'].includes(role);
    }
    return false;
  });
});

const fetchBalances = async () => {
  try {
    const res = await axios.get('/leave/balances');
    balances.value = res.data;
    if (balances.value.length > 0 && !form.value.leave_type_id) {
      form.value.leave_type_id = balances.value[0].leave_type.id;
    }
  } catch (err) {
    console.error('Error fetching leave balances:', err);
  }
};

const fetchRequests = async () => {
  try {
    const res = await axios.get('/leave/requests');
    // If user is admin/manager, it contains everyone's requests.
    // For separation, we split employee own request and pending approvals.
    if (isApprover.value) {
      approvalsList.value = res.data;
      // Filter for own requests
      requests.value = res.data.filter(r => r.employee.employee_id === authStore.user?.employee_id);
    } else {
      requests.value = res.data;
    }
  } catch (err) {
    console.error('Error loading leave requests:', err);
  }
};

const submitLeave = async () => {
  formSaving.value = true;
  formError.value = null;
  try {
    await axios.post('/leave/requests', {
      leave_type_id: Number(form.value.leave_type_id),
      start_date: form.value.start_date,
      end_date: form.value.end_date,
      reason: form.value.reason
    });
    form.value.reason = '';
    await Promise.all([fetchBalances(), fetchRequests()]);
  } catch (err) {
    console.error('Error submitting leave:', err);
    formError.value = err.response?.data?.detail || 'Failed to submit leave request.';
  } finally {
    formSaving.value = false;
  }
};

const approveLeave = async (req) => {
  const comment = prompt('Enter approval notes (optional):');
  if (comment === null) return;
  try {
    const res = await axios.post(`/leave/requests/${req.id}/approve`, { comments: comment });
    alert(res.data.message);
    await Promise.all([fetchBalances(), fetchRequests()]);
  } catch (err) {
    alert('Failed to approve request: ' + (err.response?.data?.detail || 'API error'));
  }
};

const rejectLeave = async (req) => {
  const comment = prompt('Enter rejection reason:');
  if (!comment) return;
  try {
    await axios.post(`/leave/requests/${req.id}/reject`, { comments: comment });
    await Promise.all([fetchBalances(), fetchRequests()]);
  } catch (err) {
    alert('Failed to reject: ' + (err.response?.data?.detail || 'API error'));
  }
};

const formatStatus = (status) => {
  if (status === 'MANAGER_APPROVED') return 'Pending HR';
  if (status === 'APPROVED') return 'Approved';
  if (status === 'PENDING') return 'Pending Mgr';
  return status;
};

onMounted(() => {
  fetchBalances();
  fetchRequests();
});
</script>

<style scoped>
.form-input {
  width: 100%;
  background-color: var(--color-slate-950);
  border: 1px solid var(--color-slate-800);
  border-radius: 0.5rem;
  padding: 0.5rem 0.75rem;
  color: #ffffff;
  font-size: 0.75rem;
}
.form-input:focus {
  outline: none;
  border-color: var(--color-brand-500);
}
.form-select {
  width: 100%;
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
</style>
