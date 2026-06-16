<template>
  <div class="min-h-screen bg-slate-950 text-slate-100 antialiased font-sans">
    <!-- Unauthenticated Layout (Login) -->
    <div v-if="!authStore.isAuthenticated" class="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 p-4">
      <router-view />
    </div>

    <!-- Authenticated Layout -->
    <div v-else class="min-h-screen flex flex-col md:flex-row">
      <!-- Mobile Top Bar -->
      <header class="md:hidden bg-slate-900/90 backdrop-blur-md border-b border-slate-800 px-4 py-3 flex items-center justify-between sticky top-0 z-40">
        <div class="flex items-center space-x-2">
          <div class="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
            <span class="font-bold text-white text-lg">A</span>
          </div>
          <span class="font-bold text-lg tracking-wider text-white">Antigravity HRMS</span>
        </div>
        <button @click="mobileMenuOpen = !mobileMenuOpen" class="text-slate-300 hover:text-white focus:outline-none p-1 rounded-md hover:bg-slate-800">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path v-if="!mobileMenuOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </header>

      <!-- Sidebar Navigation -->
      <aside :class="[
        mobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0',
        'fixed md:sticky top-0 left-0 h-screen w-64 bg-slate-900/70 backdrop-blur-lg border-r border-slate-800/80 p-5 flex flex-col justify-between z-50 transition-transform duration-300 ease-in-out md:flex'
      ]">
        <div>
          <!-- Logo & Brand -->
          <div class="hidden md:flex items-center space-x-3 mb-8 px-2">
            <div class="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center shadow-xl shadow-indigo-500/20">
              <span class="font-bold text-white text-xl">A</span>
            </div>
            <div>
              <h1 class="font-bold text-white tracking-wider leading-none text-base">Antigravity</h1>
              <span class="text-xs text-slate-400 font-semibold uppercase tracking-widest">HR Portal</span>
            </div>
          </div>

          <!-- Navigation Links -->
          <nav class="space-y-1">
            <router-link 
              v-for="item in navItems" 
              :key="item.name" 
              :to="item.path"
              @click="mobileMenuOpen = false"
              v-show="item.show"
              class="flex items-center space-x-3 px-3 py-2.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 transition-all group duration-150"
              active-class="bg-indigo-600/90! text-white! font-medium shadow-md shadow-indigo-600/20"
            >
              <component :is="item.icon" class="h-5 w-5 text-slate-400 group-hover:text-white transition-colors" />
              <span>{{ item.name }}</span>
            </router-link>
          </nav>
        </div>

        <!-- User profile panel -->
        <div class="border-t border-slate-800/80 pt-4 mt-6">
          <div class="flex items-center space-x-3 px-2 mb-3">
            <div class="w-10 h-10 rounded-full bg-slate-800 border-2 border-slate-700 flex items-center justify-center font-bold text-indigo-400 overflow-hidden shadow-inner">
              <span v-if="!authStore.user?.profile_picture">{{ authStore.fullName.charAt(0) }}</span>
              <img v-else :src="authStore.user.profile_picture" alt="Avatar" class="w-full h-full object-cover" />
            </div>
            <div class="min-w-0 flex-1">
              <p class="text-sm font-semibold text-white truncate leading-tight">{{ authStore.fullName }}</p>
              <p class="text-xs text-slate-400 truncate mt-0.5">{{ displayRole(authStore.userRole) }}</p>
            </div>
          </div>
          <button 
            @click="handleLogout" 
            class="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 transition-colors w-full text-left"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            <span class="text-sm font-medium">Log Out</span>
          </button>
        </div>
      </aside>

      <!-- Overlay for Mobile Menu -->
      <div 
        v-if="mobileMenuOpen" 
        @click="mobileMenuOpen = false" 
        class="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden"
      ></div>

      <!-- Main Content Container -->
      <main class="flex-1 min-w-0 flex flex-col min-h-screen">
        <!-- Top Bar Header (Desktop Only) -->
        <header class="hidden md:flex items-center justify-between px-8 py-4 bg-slate-950 border-b border-slate-900 sticky top-0 z-30">
          <div>
            <h2 class="text-lg font-bold text-white tracking-wide">{{ currentPageTitle }}</h2>
            <p class="text-xs text-slate-400 font-medium">HRMS Biometric Attendance System</p>
          </div>
          
          <div class="flex items-center space-x-6">
            <!-- Clock -->
            <div class="text-right">
              <p class="text-sm font-semibold text-slate-200">{{ formattedTime }}</p>
              <p class="text-xs text-slate-500 font-medium">{{ formattedDate }}</p>
            </div>
            <div class="h-8 w-px bg-slate-900"></div>
            <!-- Notification Badge -->
            <div class="relative cursor-pointer text-slate-400 hover:text-white transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              <span class="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-indigo-500 ring-2 ring-slate-950"></span>
            </div>
          </div>
        </header>

        <!-- View Viewport -->
        <div class="flex-1 p-4 md:p-8 bg-slate-950 overflow-y-auto">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, h } from 'vue';
import { useAuthStore } from './stores/auth';
import { useRouter, useRoute } from 'vue-router';

const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();

const mobileMenuOpen = ref(false);
const timeNow = ref(new Date());

let timeInterval = null;

// Clock updates
onMounted(() => {
  timeInterval = setInterval(() => {
    timeNow.value = new Date();
  }, 1000);
});

onUnmounted(() => {
  if (timeInterval) clearInterval(timeInterval);
});

// Format clock
const formattedTime = computed(() => {
  return timeNow.value.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });
});

const formattedDate = computed(() => {
  return timeNow.value.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: '2-digit', year: 'numeric' });
});

// Display role nicely
const displayRole = (role) => {
  if (!role) return '';
  return role.split('_').map(word => word.charAt(0) + word.slice(1).toLowerCase()).join(' ');
};

// Icons (custom render functions using inline SVG definitions)
const DashboardIcon = {
  render: () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor', strokeWidth: 2 }, [
    h('path', { strokeLinecap: 'round', strokeLinejoin: 'round', d: 'M4 6a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 01-2-2v-4z' })
  ])
};

const EmployeesIcon = {
  render: () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor', strokeWidth: 2 }, [
    h('path', { strokeLinecap: 'round', strokeLinejoin: 'round', d: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z' })
  ])
};

const AttendanceIcon = {
  render: () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor', strokeWidth: 2 }, [
    h('path', { strokeLinecap: 'round', strokeLinejoin: 'round', d: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' })
  ])
};

const DevicesIcon = {
  render: () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor', strokeWidth: 2 }, [
    h('path', { strokeLinecap: 'round', strokeLinejoin: 'round', d: 'M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 5h10a2 2 0 012 2v10a2 2 0 01-2 2H7a2 2 0 01-2-2V7a2 2 0 012-2z' })
  ])
};

const LeavesIcon = {
  render: () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor', strokeWidth: 2 }, [
    h('path', { strokeLinecap: 'round', strokeLinejoin: 'round', d: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z' })
  ])
};

const PayrollIcon = {
  render: () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor', strokeWidth: 2 }, [
    h('path', { strokeLinecap: 'round', strokeLinejoin: 'round', d: 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z' })
  ])
};

// Define menu list based on permissions
const navItems = computed(() => [
  { name: 'Dashboard', path: '/', icon: DashboardIcon, show: true },
  { name: 'Employees', path: '/employees', icon: EmployeesIcon, show: authStore.isHR },
  { name: 'Attendance', path: '/attendance', icon: AttendanceIcon, show: true },
  { name: 'Devices', path: '/devices', icon: DevicesIcon, show: authStore.isHR },
  { name: 'Leaves', path: '/leaves', icon: LeavesIcon, show: true },
  { name: 'Payroll', path: '/payroll', icon: PayrollIcon, show: true }
]);

// Determine active page title
const currentPageTitle = computed(() => {
  const currentRouteName = route.name;
  if (!currentRouteName) return 'HRMS Portal';
  return currentRouteName.toString();
});

const handleLogout = () => {
  authStore.logout();
  router.push('/login');
};
</script>

<style>
/* Active link styling override */
.router-link-active {
  background-color: var(--color-brand-600) !important;
  color: #ffffff !important;
}
</style>
