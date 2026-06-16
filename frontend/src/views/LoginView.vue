<template>
  <div class="w-full max-w-md">
    <!-- Card Panel -->
    <div class="bg-slate-900/40 backdrop-blur-xl border border-slate-800/80 rounded-2xl p-8 shadow-2xl shadow-slate-950/50">
      <!-- Header -->
      <div class="text-center mb-8">
        <div class="inline-flex w-12 h-12 rounded-xl bg-indigo-600 items-center justify-center shadow-lg shadow-indigo-500/20 mb-4">
          <span class="font-bold text-white text-2xl">A</span>
        </div>
        <h2 class="text-2xl font-bold text-white tracking-wide">Welcome Back</h2>
        <p class="text-sm text-slate-400 mt-1">Sign in to your HRMS portal account</p>
      </div>

      <!-- Error Alert -->
      <div v-if="authStore.error" class="bg-rose-500/10 border border-rose-500/30 text-rose-200 px-4 py-3 rounded-lg text-sm mb-6 flex items-start space-x-2">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-rose-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <span>{{ authStore.error }}</span>
      </div>

      <!-- Form -->
      <form @submit.prevent="handleLogin" class="space-y-5">
        <div>
          <label for="username" class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Username / Employee ID</label>
          <div class="relative">
            <span class="absolute inset-y-0 left-0 pl-3.5 flex items-center text-slate-500">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </span>
            <input 
              v-model="username" 
              type="text" 
              id="username" 
              required
              class="w-full bg-slate-950/60 border border-slate-800 rounded-lg pl-11 pr-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/30 transition-all text-sm"
              placeholder="e.g. admin or EMP-001"
            />
          </div>
        </div>

        <div>
          <div class="flex items-center justify-between mb-2">
            <label for="password" class="block text-xs font-semibold uppercase tracking-wider text-slate-400">Password</label>
            <a href="#" class="text-xs text-indigo-400 hover:text-indigo-300 font-medium">Forgot Password?</a>
          </div>
          <div class="relative">
            <span class="absolute inset-y-0 left-0 pl-3.5 flex items-center text-slate-500">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </span>
            <input 
              v-model="password" 
              type="password" 
              id="password" 
              required
              class="w-full bg-slate-950/60 border border-slate-800 rounded-lg pl-11 pr-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/30 transition-all text-sm"
              placeholder="••••••••"
            />
          </div>
        </div>

        <!-- Submit Button -->
        <button 
          type="submit" 
          :disabled="authStore.loading"
          class="w-full bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white font-medium py-2.5 rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500/50 flex items-center justify-center space-x-2 disabled:opacity-50 cursor-pointer shadow-lg shadow-indigo-600/30 text-sm mt-8"
        >
          <span v-if="authStore.loading" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
          <span v-else>Sign In</span>
        </button>
      </form>
    </div>

    <!-- Default seeded info box -->
    <div class="mt-6 bg-slate-900/30 border border-slate-900 rounded-xl p-4 text-center">
      <p class="text-xs text-slate-400">
        Demo Accounts: <br>
        <span class="font-mono text-slate-300">admin</span> / <span class="font-mono text-slate-300">admin123</span> (Super Admin)<br>
        <span class="font-mono text-slate-300">hr_manager</span> / <span class="font-mono text-slate-300">admin123</span> (HR Manager)
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useAuthStore } from '../stores/auth';
import { useRouter } from 'vue-router';

const authStore = useAuthStore();
const router = useRouter();

const username = ref('');
const password = ref('');

const handleLogin = async () => {
  const success = await authStore.login(username.value, password.value);
  if (success) {
    router.push('/');
  }
};
</script>
