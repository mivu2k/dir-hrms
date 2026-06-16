<template>
  <div class="space-y-6">
    <!-- Top Action Bar -->
    <div class="flex flex-col sm:flex-row items-center justify-between gap-4 bg-slate-900/20 p-4 border border-slate-900 rounded-xl">
      <!-- Search Input -->
      <div class="relative w-full sm:max-w-xs">
        <span class="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </span>
        <input 
          v-model="searchQuery"
          type="text" 
          class="w-full bg-slate-950 border border-slate-800 rounded-lg pl-10 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          placeholder="Search employees..."
        />
      </div>

      <!-- Add Button -->
      <button 
        @click="openAddModal"
        class="w-full sm:w-auto bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-4 py-2.5 rounded-lg text-xs transition-colors flex items-center justify-center space-x-2 cursor-pointer shadow-lg shadow-indigo-600/20"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4.5 w-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        <span>Add Employee</span>
      </button>
    </div>

    <!-- Employee Table Card -->
    <div class="bg-slate-900/40 backdrop-blur-md border border-slate-900 rounded-xl overflow-hidden shadow-lg">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="bg-slate-900/50 border-b border-slate-800 text-slate-400 font-semibold uppercase">
              <th class="px-6 py-4">ID</th>
              <th class="px-6 py-4">Name</th>
              <th class="px-6 py-4">Contact</th>
              <th class="px-6 py-4">Department & Designation</th>
              <th class="px-6 py-4">Role</th>
              <th class="px-6 py-4">Status</th>
              <th class="px-6 py-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="filteredEmployees.length === 0" class="border-b border-slate-900">
              <td colspan="7" class="px-6 py-10 text-center text-slate-500">No employees found.</td>
            </tr>
            <tr 
              v-for="emp in filteredEmployees" 
              :key="emp.id" 
              class="border-b border-slate-900 hover:bg-slate-800/20 transition-colors"
            >
              <td class="px-6 py-4 font-mono font-medium text-slate-400">{{ emp.employee_id }}</td>
              <td class="px-6 py-4 font-semibold text-white">
                {{ emp.first_name }} {{ emp.last_name }}
                <span v-if="emp.bio_device_user_id" class="block text-xxs font-normal text-slate-500 mt-0.5">Bio ID: {{ emp.bio_device_user_id }}</span>
              </td>
              <td class="px-6 py-4">
                <p class="text-slate-300">{{ emp.email }}</p>
                <p class="text-xxs text-slate-500 mt-0.5">{{ emp.phone || 'No Phone' }}</p>
              </td>
              <td class="px-6 py-4">
                <p class="text-slate-300 font-medium">{{ getDeptName(emp.department_id) }}</p>
                <p class="text-xxs text-slate-500 mt-0.5">{{ getDesgName(emp.designation_id) }}</p>
              </td>
              <td class="px-6 py-4 font-mono text-indigo-400">{{ formatRole(emp.role) }}</td>
              <td class="px-6 py-4">
                <span :class="[
                  emp.status === 'ACTIVE' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-slate-800 text-slate-400 border-slate-700',
                  'px-2 py-0.5 rounded border text-xxs font-medium'
                ]">{{ emp.status }}</span>
              </td>
              <td class="px-6 py-4 text-right">
                <button 
                  @click="deleteEmployee(emp.id)" 
                  class="text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 p-1.5 rounded-lg transition-colors cursor-pointer"
                  title="Delete Employee"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4.5 w-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Add Employee Modal Dialog -->
    <div v-if="showModal" class="fixed inset-0 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm z-50 overflow-y-auto">
      <div class="bg-slate-900 border border-slate-800 w-full max-w-2xl rounded-xl p-6 shadow-2xl space-y-6">
        <div class="flex items-center justify-between border-b border-slate-800 pb-4">
          <h3 class="text-sm font-bold text-white uppercase tracking-wider">Register New Employee</h3>
          <button @click="showModal = false" class="text-slate-400 hover:text-white cursor-pointer">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form @submit.prevent="saveEmployee" class="space-y-4">
          <!-- Two Column Inputs -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Employee ID *</label>
              <input v-model="form.employee_id" type="text" required class="form-input" placeholder="e.g. EMP-006" />
            </div>
            <div>
              <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Biometric Device ID (ZK User ID)</label>
              <input v-model="form.bio_device_user_id" type="text" class="form-input" placeholder="e.g. 6" />
            </div>
            <div>
              <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">First Name *</label>
              <input v-model="form.first_name" type="text" required class="form-input" />
            </div>
            <div>
              <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Last Name *</label>
              <input v-model="form.last_name" type="text" required class="form-input" />
            </div>
            <div>
              <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Email *</label>
              <input v-model="form.email" type="email" required class="form-input" />
            </div>
            <div>
              <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Phone</label>
              <input v-model="form.phone" type="text" class="form-input" />
            </div>
            <div>
              <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">National ID / CNIC</label>
              <input v-model="form.cnic" type="text" class="form-input" placeholder="e.g. 42101-xxxxxxx-x" />
            </div>
            <div>
              <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Passport</label>
              <input v-model="form.passport" type="text" class="form-input" />
            </div>
            <div>
              <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Department *</label>
              <select v-model="form.department_id" required class="form-select">
                <option v-for="d in departments" :key="d.id" :value="d.id">{{ d.name }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Designation *</label>
              <select v-model="form.designation_id" required class="form-select">
                <option v-for="d in designations" :key="d.id" :value="d.id">{{ d.name }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Shift *</label>
              <select v-model="form.shift_id" required class="form-select">
                <option v-for="s in shifts" :key="s.id" :value="s.id">{{ s.name }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Joining Date *</label>
              <input v-model="form.joining_date" type="date" required class="form-input" />
            </div>
            <div>
              <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">System Portal Access Password</label>
              <input v-model="form.password" type="password" class="form-input" placeholder="Optional. If omitted, no portal login." />
            </div>
            <div>
              <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Portal Role</label>
              <select v-model="form.role" class="form-select">
                <option value="EMPLOYEE">Employee</option>
                <option value="TEAM_LEAD">Team Lead</option>
                <option value="DEPT_MANAGER">Department Manager</option>
                <option value="ACCOUNTANT">Accountant</option>
                <option value="HR_OFFICER">HR Officer</option>
                <option value="HR_MANAGER">HR Manager</option>
              </select>
            </div>
          </div>

          <!-- Base Salary / Allowances for SalaryStructure -->
          <div class="border-t border-slate-800 pt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Base Salary (PKR) *</label>
              <input v-model="form.basic_salary" type="number" required class="form-input" />
            </div>
            <div>
              <label class="block text-xxs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Allowances (PKR)</label>
              <input v-model="form.allowances" type="number" class="form-input" />
            </div>
          </div>

          <p v-if="modalError" class="text-rose-400 text-xs font-semibold">{{ modalError }}</p>

          <div class="flex items-center justify-end space-x-3 border-t border-slate-800 pt-4">
            <button type="button" @click="showModal = false" class="px-4 py-2 border border-slate-800 text-slate-400 hover:text-white rounded-lg text-xs cursor-pointer">Cancel</button>
            <button type="submit" :disabled="modalSaving" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium cursor-pointer disabled:opacity-50">
              <span v-if="modalSaving">Saving...</span>
              <span v-else>Register Employee</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';

const searchQuery = ref('');
const showModal = ref(false);
const modalSaving = ref(false);
const modalError = ref(null);

const employees = ref([]);
const departments = ref([]);
const designations = ref([]);
const shifts = ref([]);

const form = ref({
  employee_id: '',
  bio_device_user_id: '',
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  cnic: '',
  passport: '',
  department_id: '',
  designation_id: '',
  shift_id: '',
  joining_date: new Date().toISOString().substr(0, 10),
  role: 'EMPLOYEE',
  password: '',
  basic_salary: 50000,
  allowances: 7500
});

const fetchEmployees = async () => {
  try {
    const res = await axios.get('/employees/');
    employees.value = res.data;
  } catch (err) {
    console.error('Error fetching employees:', err);
  }
};

const fetchStructures = async () => {
  try {
    const [d, ds, s] = await Promise.all([
      axios.get('/employees/departments'),
      axios.get('/employees/designations'),
      axios.get('/attendance/shifts')
    ]);
    departments.value = d.data;
    designations.value = ds.data;
    shifts.value = s.data;
  } catch (err) {
    console.error('Error loading dropdown lists:', err);
  }
};

const openAddModal = () => {
  form.value = {
    employee_id: `EMP-${String(employees.value.length + 1).padStart(3, '0')}`,
    bio_device_user_id: String(employees.value.length + 1),
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    cnic: '',
    passport: '',
    department_id: departments.value[0]?.id || '',
    designation_id: designations.value[0]?.id || '',
    shift_id: shifts.value[0]?.id || '',
    joining_date: new Date().toISOString().substr(0, 10),
    role: 'EMPLOYEE',
    password: '',
    basic_salary: 50000,
    allowances: 7500
  };
  modalError.value = null;
  showModal.value = true;
};

const saveEmployee = async () => {
  modalSaving.value = true;
  modalError.value = null;
  try {
    // 1. Create the employee record
    const empRes = await axios.post('/employees/', {
      employee_id: form.value.employee_id,
      bio_device_user_id: form.value.bio_device_user_id || null,
      first_name: form.value.first_name,
      last_name: form.value.last_name,
      email: form.value.email,
      phone: form.value.phone || null,
      cnic: form.value.cnic || null,
      passport: form.value.passport || null,
      department_id: Number(form.value.department_id),
      designation_id: Number(form.value.designation_id),
      shift_id: Number(form.value.shift_id),
      joining_date: form.value.joining_date,
      role: form.value.role,
      password: form.value.password || null
    });

    // 2. Configure salary structure for employee
    await axios.post(`/payroll/salary-structures/${empRes.data.id}`, {
      basic_salary: Number(form.value.basic_salary),
      allowances: Number(form.value.allowances || 0),
      eobi_contribution: 1000.00,
      provident_fund: Number(form.value.basic_salary) * 0.05,
      tax_percentage: 5.0
    });

    showModal.value = false;
    await fetchEmployees();
  } catch (err) {
    console.error('Error saving employee:', err);
    modalError.value = err.response?.data?.detail || 'Failed to create employee profile.';
  } finally {
    modalSaving.value = false;
  }
};

const deleteEmployee = async (id) => {
  if (!confirm('Are you sure you want to delete this employee? This will delete all attendance history and user profiles.')) return;
  try {
    await axios.delete(`/employees/${id}`);
    await fetchEmployees();
  } catch (err) {
    console.error('Delete error:', err);
    alert('Failed to delete employee: ' + (err.response?.data?.detail || 'API error'));
  }
};

// Search Filter
const filteredEmployees = computed(() => {
  if (!searchQuery.value) return employees.value;
  const q = searchQuery.value.toLowerCase();
  return employees.value.filter(emp => 
    emp.first_name.toLowerCase().includes(q) ||
    emp.last_name.toLowerCase().includes(q) ||
    emp.employee_id.toLowerCase().includes(q) ||
    emp.email.toLowerCase().includes(q)
  );
});

// Helper names mappings
const getDeptName = (id) => {
  const d = departments.value.find(x => x.id === id);
  return d ? d.name : 'Unassigned';
};
const getDesgName = (id) => {
  const d = designations.value.find(x => x.id === id);
  return d ? d.name : 'Unassigned';
};
const formatRole = (role) => {
  return role ? role.replace('_', ' ') : 'Employee';
};

onMounted(() => {
  fetchEmployees();
  fetchStructures();
});
</script>

<style scoped>
/* Standard Form Styling Utilities */
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
