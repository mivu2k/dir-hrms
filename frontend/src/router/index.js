import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../stores/auth';

// Lazy load views for faster startup
const DashboardView = () => import('../views/DashboardView.vue');
const LoginView = () => import('../views/LoginView.vue');
const EmployeesView = () => import('../views/EmployeesView.vue');
const AttendanceView = () => import('../views/AttendanceView.vue');
const DevicesView = () => import('../views/DevicesView.vue');
const LeavesView = () => import('../views/LeavesView.vue');
const PayrollView = () => import('../views/PayrollView.vue');

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: { requiresGuest: true }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: DashboardView,
    meta: { requiresAuth: true }
  },
  {
    path: '/employees',
    name: 'Employees',
    component: EmployeesView,
    meta: { requiresAuth: true, requiresHR: true }
  },
  {
    path: '/attendance',
    name: 'Attendance',
    component: AttendanceView,
    meta: { requiresAuth: true }
  },
  {
    path: '/devices',
    name: 'Devices',
    component: DevicesView,
    meta: { requiresAuth: true, requiresHR: true }
  },
  {
    path: '/leaves',
    name: 'Leaves',
    component: LeavesView,
    meta: { requiresAuth: true }
  },
  {
    path: '/payroll',
    name: 'Payroll',
    component: PayrollView,
    meta: { requiresAuth: true }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// Navigation Guards
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();
  
  const isAuthenticated = authStore.isAuthenticated;
  const userRole = authStore.userRole;
  
  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login');
  } else if (to.meta.requiresGuest && isAuthenticated) {
    next('/');
  } else if (to.meta.requiresHR && !['SUPER_ADMIN', 'HR_MANAGER', 'HR_OFFICER'].includes(userRole)) {
    next('/'); // Redirect to dashboard if lacks permissions
  } else {
    next();
  }
});

export default router;
