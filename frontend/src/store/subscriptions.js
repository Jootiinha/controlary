import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const useSubscriptionsStore = defineStore('subscriptions', () => {
  const subscriptions = ref([])
  const total = ref(0)
  const skip = ref(0)
  const limit = ref(25)
  const loading = ref(false)
  const error = ref(null)

  const fetchSubscriptions = async () => {
    loading.value = true
    error.value = null

    try {
      const params = {
        skip: skip.value,
        limit: limit.value,
      }
      const response = await api.get('/subscriptions', { params })
      // Backend pode retornar array ou objeto com items/total
      if (Array.isArray(response.data)) {
        subscriptions.value = response.data
      } else {
        subscriptions.value = response.data.items || response.data
        total.value = response.data.total || 0
      }
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao carregar assinaturas'
      return false
    } finally {
      loading.value = false
    }
  }

  const createSubscription = async (name, amount, accountId, cardId, categoryId, startDate, renewalDay) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.post('/subscriptions', {
        name,
        amount,
        account_id: accountId,
        card_id: cardId,
        category_id: categoryId,
        start_date: startDate,
        renewal_day: renewalDay,
      })
      subscriptions.value.push(response.data)
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao criar assinatura'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  const updateSubscription = async (subscriptionId, updates) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.put(`/subscriptions/${subscriptionId}`, updates)
      const index = subscriptions.value.findIndex(s => s.id === subscriptionId)
      if (index >= 0) {
        subscriptions.value[index] = response.data
      }
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao atualizar assinatura'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  const pauseSubscription = async (subscriptionId) => {
    try {
      const response = await api.patch(`/subscriptions/${subscriptionId}/pause`)
      const index = subscriptions.value.findIndex(s => s.id === subscriptionId)
      if (index >= 0) {
        subscriptions.value[index] = response.data
      }
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao pausar assinatura'
      throw new Error(error.value)
    }
  }

  const activateSubscription = async (subscriptionId) => {
    try {
      const response = await api.patch(`/subscriptions/${subscriptionId}/activate`)
      const index = subscriptions.value.findIndex(s => s.id === subscriptionId)
      if (index >= 0) {
        subscriptions.value[index] = response.data
      }
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao ativar assinatura'
      throw new Error(error.value)
    }
  }

  const cancelSubscription = async (subscriptionId) => {
    try {
      const response = await api.patch(`/subscriptions/${subscriptionId}/cancel`)
      const index = subscriptions.value.findIndex(s => s.id === subscriptionId)
      if (index >= 0) {
        subscriptions.value[index] = response.data
      }
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao cancelar assinatura'
      throw new Error(error.value)
    }
  }

  const deleteSubscription = async (subscriptionId) => {
    try {
      await api.delete(`/subscriptions/${subscriptionId}`)
      subscriptions.value = subscriptions.value.filter(s => s.id !== subscriptionId)
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao deletar assinatura'
      throw new Error(error.value)
    }
  }

  return {
    subscriptions,
    total,
    skip,
    limit,
    loading,
    error,
    fetchSubscriptions,
    createSubscription,
    updateSubscription,
    pauseSubscription,
    activateSubscription,
    cancelSubscription,
    deleteSubscription,
  }
})
