<template>
  <div class="space-y-6">
    <!-- Header Section -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-4xl font-bold text-gray-900">Dashboard</h1>
        <p class="text-gray-500 mt-1">Bem-vindo ao seu painel financeiro</p>
      </div>
      <div class="text-right">
        <p class="text-sm text-gray-500">{{ currentDate }}</p>
      </div>
    </div>

    <!-- KPI Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <!-- Total Balance -->
      <div class="bg-gradient-to-br from-green-50 to-green-100 rounded-xl shadow-sm border border-green-200 p-6 hover:shadow-md transition">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-green-600 text-sm font-semibold uppercase tracking-wide">Saldo Total</p>
            <p class="text-3xl font-bold text-green-900 mt-3">
              {{ formatCurrency(accountsStore.totalBalance) }}
            </p>
            <p class="text-xs text-green-600 mt-2">Somatório de todas as contas</p>
          </div>
          <div class="bg-green-600 bg-opacity-10 rounded-lg p-4">
            <svg class="w-8 h-8 text-green-600" fill="currentColor" viewBox="0 0 20 20">
              <path d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" />
            </svg>
          </div>
        </div>
      </div>

      <!-- Monthly Income -->
      <div class="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl shadow-sm border border-blue-200 p-6 hover:shadow-md transition">
        <div class="flex items-center justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-2">
              <p class="text-blue-600 text-sm font-semibold uppercase tracking-wide">Renda Mês</p>
              <TrendBadge
                :current="analyticsStore.kpis.monthly_income"
                :previous="analyticsStore.kpis.previous_income"
                :is-positive-good="true"
                period="mês anterior"
              />
            </div>
            <p class="text-3xl font-bold text-blue-900 mt-3">
              {{ formatCurrency(monthlyIncome) }}
            </p>
            <p class="text-xs text-blue-600 mt-2">Este mês</p>
          </div>
          <div class="bg-blue-600 bg-opacity-10 rounded-lg p-4">
            <svg class="w-8 h-8 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 11-1.414-1.414L13.586 7H12z" clip-rule="evenodd" />
              <path fill-rule="evenodd" d="M3 3a1 1 0 011 1v10a1 1 0 01-1 1H1a1 1 0 110-2h1V4a1 1 0 011-1h2a1 1 0 110 2H3z" clip-rule="evenodd" />
            </svg>
          </div>
        </div>
      </div>

      <!-- Monthly Expense -->
      <div class="bg-gradient-to-br from-red-50 to-red-100 rounded-xl shadow-sm border border-red-200 p-6 hover:shadow-md transition">
        <div class="flex items-center justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-2">
              <p class="text-red-600 text-sm font-semibold uppercase tracking-wide">Despesa Mês</p>
              <TrendBadge
                :current="analyticsStore.kpis.monthly_expense"
                :previous="analyticsStore.kpis.previous_expense"
                :is-positive-good="false"
                period="mês anterior"
              />
            </div>
            <p class="text-3xl font-bold text-red-900 mt-3">
              {{ formatCurrency(monthlyExpense) }}
            </p>
            <p class="text-xs text-red-600 mt-2">Este mês</p>
          </div>
          <div class="bg-red-600 bg-opacity-10 rounded-lg p-4">
            <svg class="w-8 h-8 text-red-600" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M3 13a1 1 0 110-2h14a1 1 0 110 2H3z" clip-rule="evenodd" />
              <path fill-rule="evenodd" d="M3 9a1 1 0 110-2h14a1 1 0 110 2H3z" clip-rule="evenodd" />
            </svg>
          </div>
        </div>
      </div>

      <!-- Outstanding Balance -->
      <div class="bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl shadow-sm border border-orange-200 p-6 hover:shadow-md transition">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-orange-600 text-sm font-semibold uppercase tracking-wide">A Vencer</p>
            <p class="text-3xl font-bold text-orange-900 mt-3">
              {{ formatCurrency(outstandingBalance) }}
            </p>
            <p class="text-xs text-orange-600 mt-2">Pagamentos pendentes</p>
          </div>
          <div class="bg-orange-600 bg-opacity-10 rounded-lg p-4">
            <svg class="w-8 h-8 text-orange-600" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v2h16V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clip-rule="evenodd" />
              <path fill-rule="evenodd" d="M4 11a1 1 0 011-1h10a1 1 0 011 1v7a1 1 0 01-1 1H5a1 1 0 01-1-1v-7z" clip-rule="evenodd" />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Quick Actions Card -->
      <div class="lg:col-span-1 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div class="flex items-center mb-6">
          <h2 class="text-xl font-bold text-gray-900">Ações Rápidas</h2>
          <svg class="w-5 h-5 text-gray-400 ml-2" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M5.293 7.707a1 1 0 010-1.414l4-4a1 1 0 111.414 1.414L7.414 6H17a1 1 0 110 2H7.414l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
          </svg>
        </div>

        <div class="space-y-3">
          <router-link to="/payments" class="flex items-center p-4 bg-blue-50 hover:bg-blue-100 rounded-lg text-blue-600 font-semibold transition border border-blue-100 hover:border-blue-200">
            <svg class="w-5 h-5 mr-3" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10.5 1.5H2a1 1 0 00-1 1v15a1 1 0 001 1h16a1 1 0 001-1V10.5" />
              <path d="M10 5h6M10 9h6M10 13h3" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
            </svg>
            Novo Pagamento
          </router-link>

          <router-link to="/accounts" class="flex items-center p-4 bg-green-50 hover:bg-green-100 rounded-lg text-green-600 font-semibold transition border border-green-100 hover:border-green-200">
            <svg class="w-5 h-5 mr-3" fill="currentColor" viewBox="0 0 20 20">
              <path d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" />
            </svg>
            Nova Conta
          </router-link>

          <router-link to="/cards" class="flex items-center p-4 bg-purple-50 hover:bg-purple-100 rounded-lg text-purple-600 font-semibold transition border border-purple-100 hover:border-purple-200">
            <svg class="w-5 h-5 mr-3" fill="currentColor" viewBox="0 0 20 20">
              <path d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a1 1 0 110 2H3a1 1 0 110-2V4z" />
            </svg>
            Novo Cartão
          </router-link>

          <router-link to="/analytics" class="flex items-center p-4 bg-indigo-50 hover:bg-indigo-100 rounded-lg text-indigo-600 font-semibold transition border border-indigo-100 hover:border-indigo-200">
            <svg class="w-5 h-5 mr-3" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd" />
            </svg>
            Ver Analytics
          </router-link>
        </div>
      </div>

      <!-- Upcoming Payments Card -->
      <div class="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center">
            <h2 class="text-xl font-bold text-gray-900">Próximos Vencimentos</h2>
            <span class="ml-3 px-3 py-1 bg-red-100 text-red-700 text-xs font-semibold rounded-full">
              {{ upcomingPayments.length }}
            </span>
          </div>
          <router-link to="/payments" class="text-blue-600 hover:text-blue-700 text-sm font-semibold">
            Ver todos →
          </router-link>
        </div>

        <div v-if="upcomingPayments.length === 0" class="text-center py-12">
          <svg class="w-12 h-12 text-gray-300 mx-auto mb-4" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v2h16V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clip-rule="evenodd" />
            <path fill-rule="evenodd" d="M4 11a1 1 0 011-1h10a1 1 0 011 1v7a1 1 0 01-1 1H5a1 1 0 01-1-1v-7z" clip-rule="evenodd" />
          </svg>
          <p class="text-gray-500 font-medium">Nenhum vencimento próximo</p>
          <p class="text-sm text-gray-400 mt-1">Você está em dia com seus pagamentos</p>
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="(payment, index) in upcomingPayments"
            :key="payment.id"
            class="flex items-center justify-between p-4 bg-gradient-to-r from-gray-50 to-white rounded-lg border border-gray-100 hover:border-gray-200 hover:shadow-sm transition"
          >
            <div class="flex items-center flex-1">
              <div class="flex items-center justify-center w-10 h-10 bg-gradient-to-br from-orange-100 to-red-100 rounded-lg mr-4">
                <span class="text-sm font-bold text-orange-600">{{ index + 1 }}</span>
              </div>
              <div class="flex-1">
                <p class="font-semibold text-gray-900">{{ payment.description }}</p>
                <p class="text-sm text-gray-500 mt-1">Vence em {{ daysUntil(payment.data) }} dias</p>
              </div>
            </div>
            <div class="text-right">
              <p class="font-bold text-gray-900 text-lg">{{ formatCurrency(Math.abs(payment.amount)) }}</p>
              <p class="text-xs text-gray-500 mt-1">{{ formatDate(payment.data) }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAccountsStore } from '@/store/accounts'
import { usePaymentsStore } from '@/store/payments'
import { useAnalyticsStore } from '@/store/analytics'
import TrendBadge from '@/components/TrendBadge.vue'

const accountsStore = useAccountsStore()
const paymentsStore = usePaymentsStore()
const analyticsStore = useAnalyticsStore()

const currentDate = computed(() => {
  return new Intl.DateTimeFormat('pt-BR', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(new Date())
})

onMounted(async () => {
  await Promise.all([
    accountsStore.fetchAccounts(),
    paymentsStore.fetchPayments(),
    analyticsStore.fetchDashboardKPIs(),
  ])
})

const monthlyIncome = computed(() => {
  const now = new Date()
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1)
  const monthEnd = new Date(now.getFullYear(), now.getMonth() + 1, 0)

  return paymentsStore.payments
    .filter((p) => {
      const paymentDate = new Date(p.data)
      return paymentDate >= monthStart && paymentDate <= monthEnd && p.amount > 0
    })
    .reduce((sum, p) => sum + p.amount, 0)
})

const monthlyExpense = computed(() => {
  const now = new Date()
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1)
  const monthEnd = new Date(now.getFullYear(), now.getMonth() + 1, 0)

  return paymentsStore.payments
    .filter((p) => {
      const paymentDate = new Date(p.data)
      return paymentDate >= monthStart && paymentDate <= monthEnd && p.amount < 0
    })
    .reduce((sum, p) => sum + Math.abs(p.amount), 0)
})

const outstandingBalance = computed(() => {
  return paymentsStore.payments
    .filter((p) => !p.is_paid && p.amount < 0)
    .reduce((sum, p) => sum + Math.abs(p.amount), 0)
})

const upcomingPayments = computed(() => {
  const now = new Date()
  const nextWeek = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000)

  return paymentsStore.payments
    .filter((p) => {
      const paymentDate = new Date(p.data)
      return !p.is_paid && paymentDate >= now && paymentDate <= nextWeek
    })
    .sort((a, b) => new Date(a.data) - new Date(b.data))
    .slice(0, 5)
})

const formatCurrency = (value) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value)
}

const formatDate = (value) => {
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
  }).format(new Date(value))
}

const daysUntil = (value) => {
  const now = new Date()
  const paymentDate = new Date(value)
  const diffTime = paymentDate - now
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  return diffDays
}
</script>
