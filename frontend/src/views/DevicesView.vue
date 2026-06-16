<template>
  <div class="space-y-6">
    <!-- Top Action Bar -->
    <div class="flex items-center justify-between bg-slate-900/20 p-4 border border-slate-900 rounded-xl">
      <div>
        <h3 class="text-sm font-bold text-white uppercase tracking-wider">ZKTeco Biometric Terminals</h3>
        <p class="text-xxs text-slate-400 mt-0.5">Manage terminal IP connections, health states, and log downloads</p>
      </div>
      <button 
        @click="openAddModal"
        class="bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-4 py-2 rounded-lg text-xs transition-colors flex items-center space-x-2 cursor-pointer shadow-lg shadow-indigo-600/20"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4.5 w-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        <span>Add Device</span>
      </button>
    </div>

    <!-- Devices Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div 
        v-for="d in devices" 
        :key="d.id"
        class="bg-slate-900/40 backdrop-blur-md border border-slate-900 rounded-xl p-6 shadow-lg flex flex-col justify-between"
      >
        <div>
          <!-- Header -->
          <div class="flex items-start justify-between">
            <div class="flex items-center space-x-3">
              <div :class="[
                d.connection_status === 'ONLINE' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border-rose-500/20',
                'w-10 h-10 rounded-lg border flex items-center justify-center'
              ]">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 5h10a2 2 0 012 2v10a2 2 0 01-2 2H7a2 2 0 01-2 2V7a2 2 0 012-2z" />
                </svg>
              </div>
              <div>
                <h4 class="text-sm font-bold text-white leading-tight">{{ d.name }}</h4>
                <p class="text-xxs text-slate-500 mt-0.5">{{ d.location || 'No Location' }}</p>
              </div>
            </div>
            <span :class="[
              d.connection_status === 'ONLINE' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border-rose-500/20',
              'px-2 py-0.5 rounded border text-xxs font-semibold tracking-wider'
            ]">{{ d.connection_status }}</span>
          </div>

          <!-- Connection Info -->
          <div class="mt-6 grid grid-cols-2 gap-4 text-xxs border-t border-b border-slate-900 py-4 my-4">
            <div>
              <p class="text-slate-500 uppercase font-semibold">IP Address</p>
              <p class="text-slate-300 font-mono mt-0.5">{{ d.ip_address }}:{{ d.port }}</p>
            </div>
            <div>
              <p class="text-slate-500 uppercase font-semibold">Mode Type</p>
              <p class="text-slate-300 font-medium mt-0.5">
                <span v-if="d.is_simulated" class="text-amber-500 font-semibold">[Simulated ZK]</span>
                <span v-else class="text-indigo-400">Physical UDP</span>
              </p>
            </div>
            <div>
              <p class="text-slate-500 uppercase font-semibold">Serial Number</p>
              <p class="text-slate-300 font-mono mt-0.5">{{ d.serial_number || 'Not tested' }}</p>
            </div>
            <div>
              <p class="text-slate-500 uppercase font-semibold">Firmware</p>
              <p class="text-slate-300 truncate mt-0.5" :title="d.firmware_version">{{ d.firmware_version || 'Not tested' }}</p>
            </div>
          </div>

          <!-- Last Sync -->
          <div class="flex items-center justify-between text-xxs text-slate-400">
            <span>Last Sync:</span>
            <span class="font-semibold font-mono text-slate-300">{{ formatTimestamp(d.last_sync_time) }}</span>
          </div>
        </div>

        <!-- Actions -->
        <div class="mt-6 pt-4 border-t border-slate-900 flex items-center gap-3">
          <button 
            @click="testConnection(d)"
            :disabled="actionLoading === d.id"
            class="flex-1 border border-slate-800 hover:bg-slate-800 text-slate-300 hover:text-white py-2 rounded-lg text-xxs transition-colors cursor-pointer disabled:opacity-50"
          >
            {{ actionLoading === d.id ? 'Testing...' : 'Test Connection' }}
          </button>
          <button 
            @click="syncDeviceLogs(d)"
            :disabled="actionLoading === d.id"
            class="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-2 rounded-lg text-xxs transition-colors cursor-pointer disabled:opacity-50"
          >
            {{ actionLoading === d.id ? 'Syncing...' : 'Sync Logs' }}
          </button>
          <button 
            @click="deleteDevice(d.id)"
            class="text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 p-2 border border-slate-900 rounded-lg cursor-pointer"
            title="Delete Terminal"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4.5 w-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Communication Event logs at bottom -->
    <div class="bg-slate-900/40 backdrop-blur-md border border-slate-900 rounded-xl overflow-hidden shadow-lg">
      <div class="p-4 border-b border-slate-900">
        <h3 class="text-sm font-bold text-white uppercase tracking-wider">Device Synchronization Logs</h3>
        <p class="text-xxs text-slate-500 mt-0.5">Connection events, query metrics, and error stack details</p>
      </div>

      <div class="p-4 max-h-80 overflow-y-auto space-y-2">
        <div v-if="deviceLogs.length === 0" class="text-center py-6 text-slate-500 text-xs">No device transaction logs found. Try syncing a device.</div>
        <div 
          v-for="log in deviceLogs" 
          :key="log.id"
          :class="[
            log.event_type.includes('SUCCESS') ? 'bg-emerald-500/5 border-emerald-500/10 text-emerald-400' : '',
            log.event_type.includes('FAILED') || log.event_type === 'ERROR' ? 'bg-rose-500/5 border-rose-500/10 text-rose-400' : '',
            log.event_type === 'INFO' ? 'bg-slate-900 border-slate-800 text-slate-300' : '',
            'p-3 border rounded-lg text-xxs flex items-start justify-between font-mono'
          ]"
        >
          <div class="space-y-1">
            <span class="font-bold uppercase tracking-wider text-slate-500 mr-2">[{{ log.event_type }}]</span>
            <span>{{ log.message }}</span>
          </div>
          <span class="text-slate-500 shrink-0 ml-4">{{ formatTimestamp(log.timestamp) }}</span>
        </div>
      </div>
    </div>

    <!-- Add Device Modal -->
    <div v-if="showModal" class="fixed inset-0 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm z-50">
      <div class="bg-slate-900 border border-slate-800 w-full max-w-md rounded-xl p-6 shadow-2xl space-y-4">
        <div class="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 class="text-sm font-bold text-white uppercase tracking-wider">Register Biometric Device</h3>
          <button @click="showModal = false" class="text-slate-400 hover:text-white cursor-pointer">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form @submit.prevent="saveDevice" class="space-y-4">
          <div>
            <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1">Device Name *</label>
            <input v-model="form.name" type="text" required class="form-input" placeholder="e.g. Front Door Gate" />
          </div>
          <div>
            <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1">IP Address *</label>
            <input v-model="form.ip_address" type="text" required class="form-input" placeholder="e.g. 192.168.1.201" />
          </div>
          <div>
            <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1">Port *</label>
            <input v-model="form.port" type="number" required class="form-input" />
          </div>
          <div>
            <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1">Branch / Location</label>
            <input v-model="form.location" type="text" class="form-input" placeholder="e.g. Reception" />
          </div>
          <!-- Toggle Simulation Mode -->
          <div class="flex items-center space-x-3 bg-slate-950 p-3 border border-slate-900 rounded-lg">
            <input v-model="form.is_simulated" type="checkbox" id="simulated" class="w-4 h-4 text-indigo-600 bg-slate-900 border-slate-800 rounded focus:ring-indigo-500" />
            <label for="simulated" class="text-xxs text-slate-300 font-semibold uppercase tracking-wider select-none cursor-pointer">
              Simulated ZKTeco Mode
            </label>
          </div>

          <p v-if="modalError" class="text-rose-400 text-xs font-semibold">{{ modalError }}</p>

          <div class="flex items-center justify-end space-x-3 border-t border-slate-800 pt-3">
            <button type="button" @click="showModal = false" class="px-4 py-2 border border-slate-800 text-slate-400 hover:text-white rounded-lg text-xs cursor-pointer">Cancel</button>
            <button type="submit" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium cursor-pointer">Register Terminal</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

const devices = ref([]);
const deviceLogs = ref([]);
const showModal = ref(false);
const modalError = ref(null);

const actionLoading = ref(null);

const form = ref({
  name: '',
  ip_address: '',
  port: 4370,
  location: '',
  is_simulated: true
});

const fetchDevices = async () => {
  try {
    const res = await axios.get('/devices/');
    devices.value = res.data;
  } catch (err) {
    console.error('Error fetching ZK devices:', err);
  }
};

const fetchAllDeviceLogs = async () => {
  // Aggregate logs from all devices (assuming first device for log history feed, or we fetch for first device)
  if (devices.value.length === 0) return;
  try {
    const res = await axios.get(`/devices/${devices.value[0].id}/logs`);
    deviceLogs.value = res.data;
  } catch (err) {
    console.error('Error fetching logs:', err);
  }
};

const openAddModal = () => {
  form.value = {
    name: '',
    ip_address: '192.168.1.201',
    port: 4370,
    location: '',
    is_simulated: true
  };
  modalError.value = null;
  showModal.value = true;
};

const saveDevice = async () => {
  try {
    await axios.post('/devices/', form.value);
    showModal.value = false;
    await fetchDevices();
  } catch (err) {
    console.error('Error creating device:', err);
    modalError.value = err.response?.data?.detail || 'Failed to create terminal config.';
  }
};

const deleteDevice = async (id) => {
  if (!confirm('Are you sure you want to delete this device configuration?')) return;
  try {
    await axios.delete(`/devices/${id}`);
    await fetchDevices();
  } catch (err) {
    console.error(err);
  }
};

const testConnection = async (device) => {
  actionLoading.value = device.id;
  try {
    const res = await axios.post(`/devices/${device.id}/test`);
    alert(`Diagnostics Result: \n${res.data.message}\nSerial: ${res.data.details?.serial_number || '—'}\nFirmware: ${res.data.details?.firmware_version || '—'}`);
    await Promise.all([fetchDevices(), fetchAllDeviceLogs()]);
  } catch (err) {
    alert('Diagnostics Failed: ' + (err.response?.data?.detail || 'timeout'));
  } finally {
    actionLoading.value = null;
  }
};

const syncDeviceLogs = async (device) => {
  actionLoading.value = device.id;
  try {
    const res = await axios.post(`/devices/${device.id}/sync`);
    alert(`Biometric Sync completed successfully: \nDownloaded logs count: ${res.data.total_logs}\nInserted new logs: ${res.data.new_logs}\nRecalculated summaries: ${res.data.recalculated_days}`);
    await Promise.all([fetchDevices(), fetchAllDeviceLogs()]);
  } catch (err) {
    alert('Sync Failed: ' + (err.response?.data?.detail || 'sync error'));
  } finally {
    actionLoading.value = null;
  }
};

const formatTimestamp = (isoString) => {
  if (!isoString) return '—';
  const d = new Date(isoString);
  return d.toLocaleString('en-US', { hour12: true, month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' });
};

onMounted(async () => {
  await fetchDevices();
  await fetchAllDeviceLogs();
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
</style>
