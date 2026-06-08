import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useAccountsStore = defineStore('accounts', () => {
  const accounts = ref([])
  const total = ref(0)
  const skip = ref(0)
  const limit = ref(25)
  const selectedAccount = ref(null)
  const loading = ref(false)
  const error = ref(null)

  const totalBalance = computed(() => {
    return accounts.value.reduce((sum, acc) => sum + (acc.current_balance || 0), 0)
  })

  const fetchAccounts = async () => {
    loading.value = true
    error.value = null

    try {
      const params = {
        skip: skip.value,
        limit: limit.value,
      }
      const response = await api.get('/accounts', { params })
      // Backend pode retornar array ou objeto com items/total
      if (Array.isArray(response.data)) {
        accounts.value = response.data
      } else {
        accounts.value = response.data.items || response.data
        total.value = response.data.total || 0
      }
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao carregar contas'
      return false
    } finally {
      loading.value = false
    }
  }

  const createAccount = async (name, description, initialBalance) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.post('/accounts', {
        name,
        description,
        initial_balance: initialBalance,
      })
      accounts.value.push(response.data)
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao criar conta'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  const updateAccount = async (accountId, updates) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.put(`/accounts/${accountId}`, updates)
      const index = accounts.value.findIndex(a => a.id === accountId)
      if (index >= 0) {
        accounts.value[index] = response.data
      }
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao atualizar conta'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  const deleteAccount = async (accountId) => {
    loading.value = true
    error.value = null

    try {
      await api.delete(`/accounts/${accountId}`)
      accounts.value = accounts.value.filter(a => a.id !== accountId)
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao deletar conta'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  const getAccountBalance = async (accountId) => {
    try {
      const response = await api.get(`/accounts/${accountId}/balance`)
      return response.data.balance
    } catch (err) {
      return 0
    }
  }

  return {
    accounts,
    total,
    skip,
    limit,
    selectedAccount,
    loading,
    error,
    totalBalance,
    fetchAccounts,
    createAccount,
    updateAccount,
    deleteAccount,
    getAccountBalance,
  }
})
