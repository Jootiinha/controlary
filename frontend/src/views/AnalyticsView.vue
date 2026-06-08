<template>
  <div>
    <h1 class="text-3xl font-bold text-gray-900 mb-8">Análises</h1>

    <!-- Filters -->
    <div class="mb-6 flex gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Períodos (Renda vs Despesa)</label>
        <select
          v-model.number="incomeExpenseMonths"
          @change="refreshIncomeVsExpense"
          class="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option :value="3">3 meses</option>
          <option :value="6">6 meses</option>
          <option :value="12">12 meses</option>
        </select>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Períodos (Despesa por Categoria)</label>
        <select
          v-model.number="categoryMonths"
          @change="refreshExpensesByCategory"
          class="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option :value="1">1 mês</option>
          <option :value="3">3 meses</option>
          <option :value="6">6 meses</option>
        </select>
      </div>
    </div>

    <div v-if="analyticsStore.loading" class="text-center py-12">
      <p class="text-gray-500">Carregando dados de análises...</p>
    </div>

    <div v-else class="space-y-6">
      <!-- First Row: Original Charts -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Income vs Expense -->
        <BarChart
          title="Renda vs Despesa"
          :data="incomeVsExpenseData"
          :options="chartOptions"
        />

        <!-- Expenses by Category (Doughnut) -->
        <DoughnutChart
          title="Despesa por Categoria"
          :data="expensesByCategoryData"
          :options="chartOptions"
        />

        <!-- Balance Evolution -->
        <LineChart
          title="Evolução de Saldo"
          :data="balanceEvolutionData"
          :options="chartOptions"
        />

        <!-- Payment Status -->
        <div class="bg-white rounded-lg shadow p-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">Status de Pagamentos</h3>
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-gray-700">Pagamentos Pendentes</span>
              <span class="text-2xl font-bold text-orange-600">
                {{ pendingCount }}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-gray-700">Pagamentos em Dia</span>
              <span class="text-2xl font-bold text-green-600">
                {{ paidCount }}
              </span>
            </div>
            <div class="flex items-center justify-between pt-3 border-t">
              <span class="text-gray-700 font-semibold">Total</span>
              <span class="text-2xl font-bold text-gray-900">
                {{ totalCount }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Second Row: New Charts -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Expenses by Category (Pie) -->
        <PieChart
          title="Distribuição de Despesas"
          :data="expensesByCategoryData"
          :options="chartOptions"
        />

        <!-- Category Comparison (Radar) -->
        <RadarChart
          title="Comparação por Categoria"
          :data="categoryComparisonData"
          :options="chartOptions"
        />

        <!-- Cash Flow (Waterfall/Stacked Bar) -->
        <WaterfallChart
          title="Fluxo de Caixa"
          :data="cashFlowData"
          :options="chartOptions"
        />

        <!-- Expense Correlation (Scatter) -->
        <ScatterChart
          title="Despesas por Dia da Semana"
          :data="expenseCorrelationData"
          :options="chartOptions"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAnalyticsStore } from '@/store/analytics'
import { usePaymentsStore } from '@/store/payments'
import BarChart from '@/components/BarChart.vue'
import DoughnutChart from '@/components/DoughnutChart.vue'
import LineChart from '@/components/LineChart.vue'
import PieChart from '@/components/PieChart.vue'
import RadarChart from '@/components/RadarChart.vue'
import WaterfallChart from '@/components/WaterfallChart.vue'
import ScatterChart from '@/components/ScatterChart.vue'

const analyticsStore = useAnalyticsStore()
const paymentsStore = usePaymentsStore()

const incomeExpenseMonths = ref(6)
const categoryMonths = ref(1)

const chartOptions = {
  responsive: true,
  maintainAspectRatio: true,
}

const incomeVsExpenseData = computed(() => {
  if (!analyticsStore.incomeVsExpense.length) {
    return { labels: [], datasets: [] }
  }

  const labels = analyticsStore.incomeVsExpense.map((d) => d.month)
  const incomeData = analyticsStore.incomeVsExpense.map((d) => d.income)
  const expenseData = analyticsStore.incomeVsExpense.map((d) => d.expense)

  return {
    labels,
    datasets: [
      {
        label: 'Renda',
        data: incomeData,
        backgroundColor: '#10B981',
        borderColor: '#059669',
        borderWidth: 1,
      },
      {
        label: 'Despesa',
        data: expenseData,
        backgroundColor: '#EF4444',
        borderColor: '#DC2626',
        borderWidth: 1,
      },
    ],
  }
})

const expensesByCategoryData = computed(() => {
  if (!analyticsStore.expensesByCategory.length) {
    return { labels: [], datasets: [] }
  }

  const labels = analyticsStore.expensesByCategory.map((d) => d.category)
  const amounts = analyticsStore.expensesByCategory.map((d) => d.amount)

  const backgroundColors = [
    '#3B82F6',
    '#8B5CF6',
    '#EC4899',
    '#F59E0B',
    '#10B981',
    '#06B6D4',
    '#6366F1',
    '#F97316',
  ]

  return {
    labels,
    datasets: [
      {
        data: amounts,
        backgroundColor: backgroundColors.slice(0, labels.length),
        borderColor: '#FFFFFF',
        borderWidth: 2,
      },
    ],
  }
})

const balanceEvolutionData = computed(() => {
  if (!analyticsStore.balanceEvolution.length) {
    return { labels: [], datasets: [] }
  }

  const labels = analyticsStore.balanceEvolution.map((d) => d.date)
  const balances = analyticsStore.balanceEvolution.map((d) => d.balance)

  return {
    labels,
    datasets: [
      {
        label: 'Saldo da Conta',
        data: balances,
        borderColor: '#3B82F6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        tension: 0.4,
        fill: true,
      },
    ],
  }
})

const cashFlowData = computed(() => {
  if (!analyticsStore.cashFlow.length) {
    return { labels: [], datasets: [] }
  }

  const labels = analyticsStore.cashFlow.map((d) => d.month)
  const opening = analyticsStore.cashFlow.map((d) => d.opening)
  const income = analyticsStore.cashFlow.map((d) => d.income)
  const expense = analyticsStore.cashFlow.map((d) => d.expense)
  const closing = analyticsStore.cashFlow.map((d) => d.closing)

  return {
    labels,
    datasets: [
      {
        label: 'Saldo Inicial',
        data: opening,
        backgroundColor: '#9CA3AF',
      },
      {
        label: 'Receita',
        data: income,
        backgroundColor: '#10B981',
      },
      {
        label: 'Despesa',
        data: expense.map((e) => -e),
        backgroundColor: '#EF4444',
      },
      {
        label: 'Saldo Final',
        data: closing,
        backgroundColor: '#3B82F6',
      },
    ],
  }
})

const categoryComparisonData = computed(() => {
  if (!analyticsStore.categoryComparison.length) {
    return { labels: [], datasets: [] }
  }

  const labels = analyticsStore.categoryComparison.map((d) => d.category)
  const incomeData = analyticsStore.categoryComparison.map((d) => d.income_total)
  const expenseData = analyticsStore.categoryComparison.map((d) => d.expense_total)

  return {
    labels,
    datasets: [
      {
        label: 'Receita',
        data: incomeData,
        borderColor: '#10B981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
      },
      {
        label: 'Despesa',
        data: expenseData,
        borderColor: '#EF4444',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
      },
    ],
  }
})

const expenseCorrelationData = computed(() => {
  if (!analyticsStore.expenseCorrelation.length) {
    return { labels: [], datasets: [] }
  }

  const labels = analyticsStore.expenseCorrelation.map((d) => d.day)
  const expenses = analyticsStore.expenseCorrelation.map((d) => d.total_expense)

  return {
    labels,
    datasets: [
      {
        label: 'Despesa Total (R$)',
        data: expenses,
        borderColor: '#EF4444',
        backgroundColor: 'rgba(239, 68, 68, 0.5)',
        borderWidth: 2,
        pointRadius: 5,
        pointBackgroundColor: '#EF4444',
      },
    ],
  }
})

const pendingCount = computed(() => {
  return paymentsStore.payments.filter((p) => !p.is_paid).length
})

const paidCount = computed(() => {
  return paymentsStore.payments.filter((p) => p.is_paid).length
})

const totalCount = computed(() => {
  return paymentsStore.payments.length
})

onMounted(async () => {
  await Promise.all([
    analyticsStore.fetchIncomeVsExpense(incomeExpenseMonths.value),
    analyticsStore.fetchExpensesByCategory(categoryMonths.value),
    analyticsStore.fetchBalanceEvolution(30),
    analyticsStore.fetchCashFlow(3),
    analyticsStore.fetchCategoryComparison(3),
    analyticsStore.fetchExpenseCorrelation(90),
    paymentsStore.fetchPayments(),
  ])
})

const refreshIncomeVsExpense = async () => {
  await analyticsStore.fetchIncomeVsExpense(incomeExpenseMonths.value)
}

const refreshExpensesByCategory = async () => {
  await analyticsStore.fetchExpensesByCategory(categoryMonths.value)
}
</script>
