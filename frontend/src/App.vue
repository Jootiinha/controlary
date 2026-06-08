<template>
  <div v-if="!isAuthenticated" class="h-screen">
    <router-view />
  </div>

  <div v-else class="h-screen flex bg-gray-50">
    <!-- Sidebar -->
    <aside class="w-64 bg-gradient-to-b from-gray-900 to-gray-800 text-white shadow-2xl flex flex-col fixed left-0 top-0 bottom-0 overflow-y-auto">
      <!-- Logo Section -->
      <div class="p-6 border-b border-gray-700">
        <h1 class="text-3xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">Controle</h1>
        <p class="text-gray-400 text-sm mt-1">Financeiro</p>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 px-4 py-6 space-y-2">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="flex items-center px-4 py-3 rounded-lg transition-all duration-200 text-gray-300 hover:text-white hover:bg-gray-700"
          :class="{ 'bg-blue-600 text-white': isActive(item.path) }"
        >
          <span class="text-lg mr-3">{{ item.icon }}</span>
          <span class="font-medium">{{ item.label }}</span>
        </router-link>
      </nav>

      <!-- Logout Button -->
      <div class="p-6 border-t border-gray-700">
        <button
          @click="logout"
          class="w-full flex items-center justify-center py-3 px-4 bg-red-600 hover:bg-red-700 rounded-lg font-semibold transition-colors duration-200"
        >
          <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          Sair
        </button>
      </div>
    </aside>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col ml-64">
      <!-- Header -->
      <header class="bg-white shadow-sm border-b border-gray-200 px-8 py-4 flex justify-between items-center sticky top-0 z-10">
        <div>
          <h2 class="text-2xl font-bold text-gray-900">{{ pageTitle }}</h2>
          <p class="text-xs text-gray-500 mt-1">{{ currentPageDescription }}</p>
        </div>
        <div class="flex items-center gap-6">
          <div class="text-right">
            <p class="text-sm font-semibold text-gray-900">{{ username }}</p>
            <p class="text-xs text-gray-500">{{ currentTime }}</p>
          </div>
          <div class="w-12 h-12 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-full flex items-center justify-center text-white font-bold text-lg shadow-md">
            {{ userInitial }}
          </div>
        </div>
      </header>

      <!-- Page Content -->
      <main class="flex-1 overflow-auto p-8">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from './store/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const currentTime = ref('')

const isAuthenticated = computed(() => authStore.isAuthenticated)
const username = computed(() => authStore.user?.username || 'User')
const userInitial = computed(() => username.value.charAt(0).toUpperCase())

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: '📊' },
  { path: '/accounts', label: 'Contas', icon: '🏦' },
  { path: '/payments', label: 'Pagamentos', icon: '💳' },
  { path: '/cards', label: 'Cartões', icon: '🎫' },
  { path: '/subscriptions', label: 'Assinaturas', icon: '🔄' },
  { path: '/categories', label: 'Categorias', icon: '📁' },
  { path: '/calendar', label: 'Calendário', icon: '📅' },
  { path: '/investments', label: 'Investimentos', icon: '📈' },
  { path: '/analytics', label: 'Análises', icon: '📉' },
]

const pageDescriptions = {
  '/dashboard': 'Visão geral de suas finanças',
  '/accounts': 'Gerencie suas contas bancárias',
  '/payments': 'Registre e acompanhe pagamentos',
  '/cards': 'Controle seus cartões de crédito',
  '/subscriptions': 'Monitore assinaturas recorrentes',
  '/categories': 'Organize categorias de gastos',
  '/calendar': 'Visualize pagamentos no calendário',
  '/investments': 'Acompanhe seus investimentos',
  '/analytics': 'Análise detalhada de dados financeiros',
}

const pageTitle = computed(() => {
  const item = navItems.find(i => i.path === route.path)
  return item ? item.label : 'Dashboard'
})

const currentPageDescription = computed(() => {
  return pageDescriptions[route.path] || 'Bem-vindo'
})

const isActive = (path) => {
  return route.path === path
}

const updateTime = () => {
  const now = new Date()
  currentTime.value = new Intl.DateTimeFormat('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(now)
}

const logout = async () => {
  await authStore.logout()
  router.push('/login')
}

onMounted(() => {
  updateTime()
  const interval = setInterval(updateTime, 1000)
  onUnmounted(() => clearInterval(interval))
})
</script>

<style scoped>
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a0aec0;
}
</style>
