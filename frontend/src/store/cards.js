import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const useCardsStore = defineStore('cards', () => {
  const cards = ref([])
  const total = ref(0)
  const skip = ref(0)
  const limit = ref(25)
  const loading = ref(false)
  const error = ref(null)

  const fetchCards = async () => {
    loading.value = true
    error.value = null

    try {
      const params = {
        skip: skip.value,
        limit: limit.value,
      }
      const response = await api.get('/cards', { params })
      // Backend pode retornar array ou objeto com items/total
      if (Array.isArray(response.data)) {
        cards.value = response.data
      } else {
        cards.value = response.data.items || response.data
        total.value = response.data.total || 0
      }
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao carregar cartões'
      return false
    } finally {
      loading.value = false
    }
  }

  const createCard = async (name, finalDigits, limit, dayClose, dayDue) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.post('/cards', {
        name,
        final_digits: finalDigits,
        limit,
        day_close: dayClose,
        day_due: dayDue,
      })
      cards.value.push(response.data)
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao criar cartão'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  const updateCard = async (cardId, updates) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.put(`/cards/${cardId}`, updates)
      const index = cards.value.findIndex(c => c.id === cardId)
      if (index >= 0) {
        cards.value[index] = response.data
      }
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao atualizar cartão'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  const deleteCard = async (cardId) => {
    loading.value = true
    error.value = null

    try {
      await api.delete(`/cards/${cardId}`)
      cards.value = cards.value.filter(c => c.id !== cardId)
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao deletar cartão'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  return {
    cards,
    total,
    skip,
    limit,
    loading,
    error,
    fetchCards,
    createCard,
    updateCard,
    deleteCard,
  }
})
