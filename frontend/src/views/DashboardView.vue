<template>
  <div class="space-y-6">
    <!-- Quick Stats Cards Grid -->
    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <div v-for="i in 4" :key="i" class="h-28 bg-slate-900/40 border border-slate-900 rounded-xl animate-pulse"></div>
    </div>
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <!-- Total Employees -->
      <div class="bg-slate-900/40 backdrop-blur-md border border-slate-900 rounded-xl p-6 flex items-center justify-between shadow-lg">
        <div class="space-y-1">
          <p class="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Active Staff</p>
          <p class="text-3xl font-bold text-white">{{ stats.metrics.total_employees }}</p>
        </div>
        <div class="w-12 h-12 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </div>
      </div>

      <!-- Present Today -->
      <div class="bg-slate-900/40 backdrop-blur-md border border-slate-900 rounded-xl p-6 flex items-center justify-between shadow-lg">
        <div class="space-y-1">
          <p class="text-xs font-semibold uppercase tracking-wider text-slate-400">Present Today</p>
          <p class="text-3xl font-bold text-emerald-400">{{ stats.metrics.present_today }}</p>
        </div>
        <div class="w-12 h-12 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
      </div>

      <!-- Late Today -->
      <div class="bg-slate-900/40 backdrop-blur-md border border-slate-900 rounded-xl p-6 flex items-center justify-between shadow-lg">
        <div class="space-y-1">
          <p class="text-xs font-semibold uppercase tracking-wider text-slate-400">Late Arrivals</p>
          <p class="text-3xl font-bold text-amber-500">{{ stats.metrics.late_today }}</p>
        </div>
        <div class="w-12 h-12 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-500">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
      </div>

      <!-- On Leave Today -->
      <div class="bg-slate-900/40 backdrop-blur-md border border-slate-900 rounded-xl p-6 flex items-center justify-between shadow-lg">
        <div class="space-y-1">
          <p class="text-xs font-semibold uppercase tracking-wider text-slate-400">On Leave / Absent</p>
          <p class="text-3xl font-bold text-rose-400">{{ stats.metrics.on_leave_today }} / {{ stats.metrics.absent_today }}</p>
        </div>
        <div class="w-12 h-12 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </div>
      </div>
    </div>

    <!-- Main Content Row -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Interactive Attendance Graph -->
      <div class="bg-slate-900/40 backdrop-blur-md border border-slate-900 rounded-xl p-6 shadow-lg lg:col-span-2">
        <h3 class="text-sm font-bold text-white uppercase tracking-wider mb-4">Attendance Analysis</h3>
        <div v-if="!loading" class="h-72">
          <apexchart 
            type="bar" 
            height="100%" 
            :options="chartOptions" 
            :series="chartSeries"
          ></apexchart>
        </div>
      </div>

      <!-- Quick Web Punch Widget -->
      <div class="bg-slate-900/40 backdrop-blur-md border border-slate-900 rounded-xl p-6 shadow-lg flex flex-col justify-between">
        <div>
          <h3 class="text-sm font-bold text-white uppercase tracking-wider mb-2">Web Attendance</h3>
          <p class="text-xs text-slate-400 mb-6">Punch your check-in or check-out directly from the dashboard.</p>
          
          <div class="space-y-4">
            <!-- Select Punch Type -->
            <div>
              <label class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Punch State</label>
              <div class="grid grid-cols-2 gap-2">
                <button 
                  @click="punchType = 'CHECK_IN'"
                  :class="[
                    punchType === 'CHECK_IN' ? 'bg-indigo-600 border-indigo-500 text-white' : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200',
                    'border py-2 rounded-lg font-medium text-xs transition-colors cursor-pointer'
                  ]"
                >Check In</button>
                <button 
                  @click="punchType = 'CHECK_OUT'"
                  :class="[
                    punchType === 'CHECK_OUT' ? 'bg-indigo-600 border-indigo-500 text-white' : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200',
                    'border py-2 rounded-lg font-medium text-xs transition-colors cursor-pointer'
                  ]"
                >Check Out</button>
              </div>
            </div>

            <!-- GPS Simulation Note -->
            <div class="bg-indigo-950/20 border border-indigo-950/50 rounded-lg p-3 text-xs text-indigo-300 flex items-start space-x-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span>GPS Coordinates will automatically bind based on simulated office perimeter check.</span>
            </div>
          </div>
        </div>

        <div class="mt-6">
          <button 
            @click="submitPunch"
            :disabled="punchLoading"
            class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-3 rounded-lg shadow-lg shadow-indigo-600/30 transition-all flex items-center justify-center space-x-2 cursor-pointer disabled:opacity-50 text-sm"
          >
            <span v-if="punchLoading" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            <span v-else>Register Web Punch</span>
          </button>
          <p v-if="punchResult" :class="[punchResult.success ? 'text-emerald-400' : 'text-rose-400', 'text-xs text-center mt-3 font-medium']">
            {{ punchResult.message }}
          </p>
        </div>
      </div>
    </div>

    <!-- Bottom Row (Live Punches stream & devices) -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Biometric Logs Stream -->
      <div class="bg-slate-900/40 backdrop-blur-md border border-slate-900 rounded-xl p-6 shadow-lg lg:col-span-2 flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-bold text-white uppercase tracking-wider">Live Punch Stream</h3>
            <span class="inline-flex items-center px-2 py-0.5 rounded text-xxs font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <span class="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-ping mr-1.5"></span>
              Live Synced
            </span>
          </div>
          
          <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse text-xs">
              <thead>
                <tr class="border-b border-slate-800 text-slate-400 font-semibold uppercase">
                  <th class="py-2.5">ID</th>
                  <th class="py-2.5">Name</th>
                  <th class="py-2.5">Timestamp</th>
                  <th class="py-2.5">State</th>
                  <th class="py-2.5">Mode</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="stats.recent_punches.length === 0" class="border-b border-slate-900">
                  <td colspan="5" class="py-4 text-center text-slate-500">No logs generated for today.</td>
                </tr>
                <tr 
                  v-for="(log, idx) in stats.recent_punches" 
                  :key="idx" 
                  class="border-b border-slate-900/60 hover:bg-slate-800/20 transition-colors"
                >
                  <td class="py-2.5 font-mono text-slate-400">{{ log.employee_id }}</td>
                  <td class="py-2.5 font-medium text-white">{{ log.employee_name }}</td>
                  <td class="py-2.5 text-slate-300">{{ log.timestamp }}</td>
                  <td class="py-2.5">
                    <span :class="[
                      log.punch_type === 'CHECK_IN' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border-rose-500/20',
                      'px-1.5 py-0.5 rounded border text-xxs font-semibold'
                    ]">{{ log.punch_type }}</span>
                  </td>
                  <td class="py-2.5 text-slate-400 font-mono">{{ log.verification_mode }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Devices Health Monitor Card -->
      <div class="bg-slate-900/40 backdrop-blur-md border border-slate-900 rounded-xl p-6 shadow-lg flex flex-col justify-between">
        <div>
          <h3 class="text-sm font-bold text-white uppercase tracking-wider mb-4">Biometric Terminals</h3>
          
          <div class="space-y-4">
            <div class="flex items-center justify-between p-3 bg-slate-950/60 border border-slate-900 rounded-lg">
              <div class="flex items-center space-x-3">
                <div class="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 5h10a2 2 0 012 2v10a2 2 0 01-2 2H7a2 2 0 01-2-2V7a2 2 0 012-2z" />
                  </svg>
                </div>
                <div>
                  <p class="text-xs font-semibold text-white">Terminals Online</p>
                  <p class="text-xxs text-slate-400 mt-0.5">Ready to download records</p>
                </div>
              </div>
              <span class="text-sm font-bold text-emerald-400">{{ stats.devices.online }}</span>
            </div>

            <div class="flex items-center justify-between p-3 bg-slate-950/60 border border-slate-900 rounded-lg">
              <div class="flex items-center space-x-3">
                <div class="w-8 h-8 rounded-lg bg-rose-500/10 flex items-center justify-center text-rose-400">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                  </svg>
                </div>
                <div>
                  <p class="text-xs font-semibold text-white">Terminals Offline</p>
                  <p class="text-xxs text-slate-400 mt-0.5">Connection timeout error</p>
                </div>
              </div>
              <span class="text-sm font-bold text-rose-400">{{ stats.devices.offline }}</span>
            </div>

            <!-- Pending approvals notice -->
            <div class="p-3 bg-indigo-950/10 border border-indigo-950/30 rounded-lg space-y-2">
              <p class="text-xs font-semibold text-indigo-300 uppercase tracking-wider">Approval Queue</p>
              <div class="flex items-center justify-between text-xxs text-slate-300">
                <span>Pending Leave Requests</span>
                <span class="font-bold text-indigo-400">{{ stats.alerts.pending_leaves }}</span>
              </div>
              <div class="flex items-center justify-between text-xxs text-slate-300">
                <span>Pending Attendance Corrections</span>
                <span class="font-bold text-indigo-400">{{ stats.alerts.pending_corrections }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="mt-6 border-t border-slate-900/60 pt-4">
          <router-link to="/devices" class="w-full inline-flex items-center justify-center space-x-2 py-2 border border-slate-800 text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors cursor-pointer">
            <span>Configure Devices</span>
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

const loading = ref(true);
const punchType = ref('CHECK_IN');
const punchLoading = ref(false);
const punchResult = ref(null);

const stats = ref({
  metrics: { total_employees: 0, present_today: 0, absent_today: 0, late_today: 0, on_leave_today: 0 },
  devices: { total: 0, online: 0, offline: 0 },
  alerts: { pending_leaves: 0, pending_corrections: 0 },
  recent_punches: [],
  payroll_summary: null
});

// Chart setup for daily trends
const chartSeries = ref([
  { name: 'Present', data: [4, 5, 4, 5, 5] },
  { name: 'Late', data: [1, 0, 1, 0, 1] },
  { name: 'Absent', data: [0, 0, 0, 0, 0] }
]);

const chartOptions = ref({
  chart: {
    type: 'bar',
    stacked: true,
    background: 'transparent',
    foreColor: '#94a3b8',
    toolbar: { show: false }
  },
  theme: { mode: 'dark' },
  colors: ['#6366f1', '#f59e0b', '#ef4444'], // Indigo, Amber, Rose
  plotOptions: {
    bar: {
      horizontal: false,
      columnWidth: '40%',
      borderRadius: 4
    }
  },
  dataLabels: { enabled: false },
  xaxis: {
    categories: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
    axisBorder: { show: false },
    axisTicks: { show: false }
  },
  yaxis: {
    title: { text: 'Employees Count' }
  },
  grid: {
    borderColor: '#1e293b',
    strokeDashArray: 4
  },
  tooltip: {
    theme: 'dark'
  },
  legend: {
    position: 'top',
    horizontalAlign: 'right'
  }
});

const fetchDashboardData = async () => {
  try {
    const res = await axios.get('/dashboard/summary');
    stats.value = res.data;
    
    // Adjust mock chart numbers dynamically based on actual employee count if available
    const total = stats.value.metrics.total_employees || 5;
    const present = stats.value.metrics.present_today || 4;
    const late = stats.value.metrics.late_today || 1;
    const absent = stats.value.metrics.absent_today || 0;
    
    chartSeries.value = [
      { name: 'Present', data: [total - 1, total, total - 2, total - 1, present] },
      { name: 'Late', data: [1, 0, 1, 0, late] },
      { name: 'Absent', data: [0, 0, 1, 1, absent] }
    ];
  } catch (err) {
    console.error('Error fetching dashboard summary:', err);
  } finally {
    loading.value = false;
  }
};

const submitPunch = async () => {
  punchLoading.value = true;
  punchResult.value = null;
  try {
    const res = await axios.post('/attendance/punch', {
      punch_type: punchType.value,
      verification_mode: 'WEB',
      // Simulating a GPS location coordinate inside perimeter
      latitude: 33.6844,
      longitude: 73.0479
    });
    
    punchResult.value = {
      success: true,
      message: res.data.message
    };
    
    // Refresh dashboard stats
    await fetchDashboardData();
  } catch (err) {
    console.error('Web punch error:', err);
    punchResult.value = {
      success: false,
      message: err.response?.data?.detail || 'Failed to register web punch.'
    };
  } finally {
    punchLoading.value = false;
  }
};

onMounted(() => {
  fetchDashboardData();
});
</script>
