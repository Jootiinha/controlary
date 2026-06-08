import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const usePaymentsStore = defineStore('payments', () => {
  const payments = ref([])
  const total = ref(0)
  const skip = ref(0)
  const limit = ref(25)
  const loading = ref(false)
  const error = ref(null)

  const fetchPayments = async (isPaid = null) => {
    loading.value = true
    error.value = null

    try {
      const params = {
        skip: skip.value,
        limit: limit.value,
      }
      if (isPaid !== null) {
        params.is_paid = isPaid
      }
      const response = await api.get('/payments', { params })
      // Backend pode retornar array ou objeto com items/total
      if (Array.isArray(response.data)) {
        payments.value = response.data
      } else {
        payments.value = response.data.items || response.data
        total.value = response.data.total || 0
      }
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao carregar pagamentos'
      return false
    } finally {
      loading.value = false
    }
  }

  const createPayment = async (description, amount, accountId, cardId, categoryId, data) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.post('/payments', {
        description,
        amount,
        account_id: accountId,
        card_id: cardId,
        category_id: categoryId,
        data,
      })
      payments.value.push(response.data)
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao criar pagamento'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  const updatePayment = async (paymentId, updates) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.put(`/payments/${paymentId}`, updates)
      const index = payments.value.findIndex(p => p.id === paymentId)
      if (index >= 0) {
        payments.value[index] = response.data
      }
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao atualizar pagamento'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  const markPaid = async (paymentId) => {
    try {
      const response = await api.patch(`/payments/${paymentId}/mark-paid`)
      const index = payments.value.findIndex(p => p.id === paymentId)
      if (index >= 0) {
        payments.value[index] = response.data
      }
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao marcar como pago'
      throw new Error(error.value)
    }
  }

  const deletePayment = async (paymentId) => {
    try {
      await api.delete(`/payments/${paymentId}`)
      payments.value = payments.value.filter(p => p.id !== paymentId)
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao deletar pagamento'
      throw new Error(error.value)
    }
  }

  return {
    payments,
    total,
    skip,
    limit,
    loading,
    error,
    fetchPayments,
    createPayment,
    updatePayment,
    markPaid,
    deletePayment,
  }
})
