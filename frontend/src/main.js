import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'
import VueApexCharts from "vue3-apexcharts"
import './style.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)

// Initialize JWT token in Axios header from localStorage immediately
const authStore = useAuthStore()
authStore.initializeAuth()

app.use(router)
app.use(VueApexCharts)

app.mount('#app')
