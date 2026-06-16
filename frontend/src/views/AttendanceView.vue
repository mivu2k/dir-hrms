<template>
  <div class="space-y-6">
    <!-- Top Filter Bar -->
    <div class="flex flex-col xl:flex-row items-center justify-between gap-4 bg-slate-900/20 p-4 border border-slate-900 rounded-xl">
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 w-full xl:max-w-4xl">
        <!-- Start Date -->
        <div>
          <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1">Start Date</label>
          <input v-model="filters.start_date" type="date" class="form-input" />
        </div>
        <!-- End Date -->
        <div>
          <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1">End Date</label>
          <input v-model="filters.end_date" type="date" class="form-input" />
        </div>
        <!-- Status Filter -->
        <div>
          <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1">Status</label>
          <select v-model="filters.status" class="form-select">
            <option value="">All Statuses</option>
            <option value="PRESENT">Present</option>
            <option value="LATE">Late Only</option>
            <option value="HALF_DAY">Half Day</option>
            <option value="ABSENT">Absent</option>
            <option value="ON_LEAVE">On Leave</option>
            <option value="HOLIDAY">Holiday</option>
          </select>
        </div>
        <!-- Search Trigger -->
        <div class="flex items-end">
          <button 
            @click="fetchSummaries"
            class="w-full bg-slate-950 hover:bg-slate-800 text-slate-200 border border-slate-800 text-xs font-semibold py-2 rounded-lg transition-colors cursor-pointer"
          >Apply Filters</button>
        </div>
      </div>

      <!-- Action Button: Request Regularization -->
      <button 
        @click="showCorrectionModal = true"
        class="w-full xl:w-auto bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-4 py-2.5 rounded-lg text-xs transition-colors flex items-center justify-center space-x-2 cursor-pointer shadow-lg shadow-indigo-600/20"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4.5 w-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <span>Request Correction</span>
      </button>
    </div>

    <!-- Daily Summaries Table -->
    <div class="bg-slate-900/40 backdrop-blur-md border border-slate-900 rounded-xl overflow-hidden shadow-lg">
      <div class="p-4 border-b border-slate-900 flex items-center justify-between">
        <h3 class="text-sm font-bold text-white uppercase tracking-wider">Attendance Register</h3>
        <p class="text-xxs text-slate-500">Filtered daily metrics sheet</p>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="bg-slate-900/50 border-b border-slate-800 text-slate-400 font-semibold uppercase">
              <th class="px-6 py-4">Employee</th>
              <th class="px-6 py-4">Date</th>
              <th class="px-6 py-4">Check In</th>
              <th class="px-6 py-4">Check Out</th>
              <th class="px-6 py-4">Work Hours</th>
              <th class="px-6 py-4">Late / OT</th>
              <th class="px-6 py-4">Status</th>
              <th class="px-6 py-4">Remarks</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="summaries.length === 0" class="border-b border-slate-900">
              <td colspan="8" class="px-6 py-10 text-center text-slate-500">No attendance sheets generated for selection.</td>
            </tr>
            <tr 
              v-for="s in summaries" 
              :key="s.id" 
              class="border-b border-slate-900 hover:bg-slate-800/20 transition-colors"
            >
              <td class="px-6 py-4 font-semibold text-white">
                {{ s.employee.first_name }} {{ s.employee.last_name }}
                <span class="block text-xxs font-mono font-normal text-slate-500 mt-0.5">{{ s.employee.employee_id }}</span>
              </td>
              <td class="px-6 py-4 text-slate-300 font-medium">{{ s.date }}</td>
              <td class="px-6 py-4 font-mono text-slate-300">{{ formatTime(s.check_in) }}</td>
              <td class="px-6 py-4 font-mono text-slate-300">{{ formatTime(s.check_out) }}</td>
              <td class="px-6 py-4 font-bold text-slate-200">{{ s.working_hours }} hrs</td>
              <td class="px-6 py-4">
                <span v-if="s.late_minutes > 0" class="text-rose-400 font-medium">Late: {{ s.late_minutes }}m</span>
                <span v-else-if="s.overtime_minutes > 0" class="text-emerald-400 font-medium">OT: {{ s.overtime_minutes }}m</span>
                <span v-else class="text-slate-500">—</span>
              </td>
              <td class="px-6 py-4">
                <span :class="[
                  s.status === 'PRESENT' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : '',
                  s.status === 'LATE' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : '',
                  s.status === 'HALF_DAY' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : '',
                  s.status === 'ABSENT' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' : '',
                  s.status === 'ON_LEAVE' ? 'bg-sky-500/10 text-sky-400 border-sky-500/20' : '',
                  s.status === 'HOLIDAY' ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' : '',
                  'px-2 py-0.5 rounded border text-xxs font-semibold'
                ]">{{ s.status }}</span>
              </td>
              <td class="px-6 py-4 text-slate-400 text-xxs max-w-xs truncate" :title="s.remarks">{{ s.remarks || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Regularization Requests Console -->
    <div class="bg-slate-900/40 backdrop-blur-md border border-slate-900 rounded-xl overflow-hidden shadow-lg">
      <div class="p-4 border-b border-slate-900">
        <h3 class="text-sm font-bold text-white uppercase tracking-wider">Regularization Correction Requests</h3>
        <p class="text-xxs text-slate-500 mt-0.5">Approve missing punches corrections</p>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="bg-slate-900/50 border-b border-slate-800 text-slate-400 font-semibold uppercase">
              <th class="px-6 py-4">Employee</th>
              <th class="px-6 py-4">Date</th>
              <th class="px-6 py-4">Requested Punch Times</th>
              <th class="px-6 py-4">Reason</th>
              <th class="px-6 py-4">Status</th>
              <th class="px-6 py-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="corrections.length === 0" class="border-b border-slate-900">
              <td colspan="6" class="px-6 py-10 text-center text-slate-500">No correction requests recorded.</td>
            </tr>
            <tr 
              v-for="c in corrections" 
              :key="c.id" 
              class="border-b border-slate-900 hover:bg-slate-800/20 transition-colors"
            >
              <td class="px-6 py-4 font-semibold text-white">
                {{ c.employee.first_name }} {{ c.employee.last_name }}
              </td>
              <td class="px-6 py-4 text-slate-300 font-medium">{{ c.date }}</td>
              <td class="px-6 py-4 font-mono text-slate-300">
                In: {{ c.requested_check_in || '—' }} | Out: {{ c.requested_check_out || '—' }}
              </td>
              <td class="px-6 py-4 text-slate-400 text-xxs">{{ c.reason }}</td>
              <td class="px-6 py-4">
                <span :class="[
                  c.status === 'APPROVED' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : '',
                  c.status === 'PENDING' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : '',
                  c.status === 'REJECTED' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' : '',
                  'px-2 py-0.5 rounded border text-xxs font-medium'
                ]">{{ c.status }}</span>
              </td>
              <td class="px-6 py-4 text-right space-x-2">
                <div v-if="c.status === 'PENDING' && isApprover" class="inline-flex space-x-2">
                  <button 
                    @click="approveCorrection(c.id)" 
                    class="bg-emerald-600 hover:bg-emerald-500 text-white font-medium px-2.5 py-1 rounded text-xxs cursor-pointer"
                  >Approve</button>
                  <button 
                    @click="rejectCorrection(c.id)" 
                    class="bg-rose-600 hover:bg-rose-500 text-white font-medium px-2.5 py-1 rounded text-xxs cursor-pointer"
                  >Reject</button>
                </div>
                <div v-else-if="c.comments" class="text-xxs text-slate-500 italic max-w-xxs truncate" :title="c.comments">
                  {{ c.comments }}
                </div>
                <span v-else class="text-slate-500">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Correction Dialog Modal -->
    <div v-if="showCorrectionModal" class="fixed inset-0 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm z-50">
      <div class="bg-slate-900 border border-slate-800 w-full max-w-md rounded-xl p-6 shadow-2xl space-y-4">
        <div class="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 class="text-sm font-bold text-white uppercase tracking-wider">Submit Correction Request</h3>
          <button @click="showCorrectionModal = false" class="text-slate-400 hover:text-white cursor-pointer">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form @submit.prevent="submitCorrection" class="space-y-4">
          <div>
            <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1">Date *</label>
            <input v-model="corrForm.date" type="date" required class="form-input" />
          </div>
          <div>
            <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1">Requested Check In</label>
            <input v-model="corrForm.requested_check_in" type="time" class="form-input" />
          </div>
          <div>
            <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1">Requested Check Out</label>
            <input v-model="corrForm.requested_check_out" type="time" class="form-input" />
          </div>
          <div>
            <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1">Reason *</label>
            <textarea v-model="corrForm.reason" required rows="3" class="form-input" placeholder="e.g. Forgot to punch check-in at terminal."></textarea>
          </div>

          <p v-if="corrError" class="text-rose-400 text-xs font-semibold">{{ corrError }}</p>

          <div class="flex items-center justify-end space-x-3 border-t border-slate-800 pt-3">
            <button type="button" @click="showCorrectionModal = false" class="px-4 py-2 border border-slate-800 text-slate-400 hover:text-white rounded-lg text-xs cursor-pointer">Cancel</button>
            <button type="submit" :disabled="corrSaving" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium cursor-pointer disabled:opacity-50">
              <span v-if="corrSaving">Submitting...</span>
              <span v-else>Submit Request</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useAuthStore } from '../stores/auth';
import axios from 'axios';

const authStore = useAuthStore();

const summaries = ref([]);
const corrections = ref([]);
const showCorrectionModal = ref(false);
const corrSaving = ref(false);
const corrError = ref(null);

const filters = ref({
  start_date: new Date(Date.now() - 6 * 24 * 60 * 60 * 1000).toISOString().substr(0, 10), // Last 7 days
  end_date: new Date().toISOString().substr(0, 10),
  status: ''
});

const corrForm = ref({
  date: new Date().toISOString().substr(0, 10),
  requested_check_in: '09:00',
  requested_check_out: '17:00',
  reason: ''
});

// Check if current user has approval role
const isApprover = computed(() => {
  return ['SUPER_ADMIN', 'HR_MANAGER', 'HR_OFFICER', 'DEPT_MANAGER'].includes(authStore.userRole);
});

const fetchSummaries = async () => {
  try {
    const res = await axios.get('/attendance/summaries', {
      params: {
        start_date: filters.value.start_date,
        end_date: filters.value.end_date,
        status: filters.value.status || undefined
      }
    });
    summaries.value = res.data;
  } catch (err) {
    console.error('Error fetching summaries:', err);
  }
};

const fetchCorrections = async () => {
  try {
    const res = await axios.get('/attendance/corrections');
    corrections.value = res.data;
  } catch (err) {
    console.error('Error fetching corrections:', err);
  }
};

const submitCorrection = async () => {
  corrSaving.value = true;
  corrError.value = null;
  try {
    await axios.post('/attendance/corrections', {
      date: corrForm.value.date,
      requested_check_in: corrForm.value.requested_check_in || null,
      requested_check_out: corrForm.value.requested_check_out || null,
      reason: corrForm.value.reason
    });
    showCorrectionModal.value = false;
    await fetchCorrections();
  } catch (err) {
    console.error('Error submitting correction:', err);
    corrError.value = err.response?.data?.detail || 'Failed to submit request.';
  } finally {
    corrSaving.value = false;
  }
};

const approveCorrection = async (id) => {
  const comment = prompt('Enter approval comments (optional):');
  if (comment === null) return;
  try {
    await axios.post(`/attendance/corrections/${id}/approve`, { comments: comment });
    await Promise.all([fetchSummaries(), fetchCorrections()]);
  } catch (err) {
    console.error('Approval error:', err);
    alert('Failed to approve request: ' + (err.response?.data?.detail || 'API error'));
  }
};

const rejectCorrection = async (id) => {
  const comment = prompt('Enter rejection reason:');
  if (!comment) return;
  try {
    await axios.post(`/attendance/corrections/${id}/reject`, { comments: comment });
    await fetchCorrections();
  } catch (err) {
    console.error('Rejection error:', err);
    alert('Failed to reject request: ' + (err.response?.data?.detail || 'API error'));
  }
};

const formatTime = (isoString) => {
  if (!isoString) return '—';
  try {
    const d = new Date(isoString);
    return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
  } catch (e) {
    return isoString;
  }
};

onMounted(() => {
  fetchSummaries();
  fetchCorrections();
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
