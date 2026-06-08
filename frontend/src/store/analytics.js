import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const useAnalyticsStore = defineStore('analytics', () => {
  const kpis = ref({
    monthly_income: 0,
    monthly_expense: 0,
    outstanding_balance: 0,
    net_balance: 0,
  })
  const incomeVsExpense = ref([])
  const expensesByCategory = ref([])
  const balanceEvolution = ref([])
  const paymentTimeline = ref([])
  const cashFlow = ref([])
  const categoryComparison = ref([])
  const expenseCorrelation = ref([])
  const loading = ref(false)
  const error = ref(null)

  const fetchDashboardKPIs = async () => {
    loading.value = true
    error.value = null

    try {
      const response = await api.get('/analytics/dashboard-kpis')
      kpis.value = response.data
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao carregar KPIs'
      return false
    } finally {
      loading.value = false
    }
  }

  const fetchIncomeVsExpense = async (months = 6) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.get('/analytics/income-vs-expense', { params: { months } })
      incomeVsExpense.value = response.data
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao carregar dados de renda vs despesa'
      return false
    } finally {
      loading.value = false
    }
  }

  const fetchExpensesByCategory = async (months = 1) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.get('/analytics/expenses-by-category', { params: { months } })
      expensesByCategory.value = response.data
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao carregar despesas por categoria'
      return false
    } finally {
      loading.value = false
    }
  }

  const fetchBalanceEvolution = async (days = 30) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.get('/analytics/balance-evolution', { params: { days } })
      balanceEvolution.value = response.data
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao carregar evolução de saldo'
      return false
    } finally {
      loading.value = false
    }
  }

  const fetchPaymentTimeline = async (days = 30) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.get('/analytics/payment-timeline', { params: { days } })
      paymentTimeline.value = response.data
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao carregar timeline de pagamentos'
      return false
    } finally {
      loading.value = false
    }
  }

  const fetchCashFlow = async (months = 3) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.get('/analytics/cash-flow', { params: { months } })
      cashFlow.value = response.data
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao carregar fluxo de caixa'
      return false
    } finally {
      loading.value = false
    }
  }

  const fetchCategoryComparison = async (months = 3) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.get('/analytics/category-comparison', { params: { months } })
      categoryComparison.value = response.data
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao carregar comparação de categorias'
      return false
    } finally {
      loading.value = false
    }
  }

  const fetchExpenseCorrelation = async (days = 90) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.get('/analytics/expense-correlation', { params: { days } })
      expenseCorrelation.value = response.data
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao carregar correlação de despesas'
      return false
    } finally {
      loading.value = false
    }
  }

  return {
    kpis,
    incomeVsExpense,
    expensesByCategory,
    balanceEvolution,
    paymentTimeline,
    cashFlow,
    categoryComparison,
    expenseCorrelation,
    loading,
    error,
    fetchDashboardKPIs,
    fetchIncomeVsExpense,
    fetchExpensesByCategory,
    fetchBalanceEvolution,
    fetchPaymentTimeline,
    fetchCashFlow,
    fetchCategoryComparison,
    fetchExpenseCorrelation,
  }
})
