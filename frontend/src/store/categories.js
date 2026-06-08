import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const useCategoriesStore = defineStore('categories', () => {
  const categories = ref([])
  const total = ref(0)
  const skip = ref(0)
  const limit = ref(25)
  const loading = ref(false)
  const error = ref(null)

  const fetchCategories = async () => {
    loading.value = true
    error.value = null

    try {
      const params = {
        skip: skip.value,
        limit: limit.value,
      }
      const response = await api.get('/categories/all', { params })
      // Backend pode retornar array ou objeto com items/total
      if (Array.isArray(response.data)) {
        categories.value = response.data
      } else {
        categories.value = response.data.items || response.data
        total.value = response.data.total || 0
      }
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao carregar categorias'
      return false
    } finally {
      loading.value = false
    }
  }

  const createCategory = async (name, color, icon, description) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.post('/categories', {
        name,
        color,
        icon,
        description,
      })
      categories.value.push(response.data)
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao criar categoria'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  const updateCategory = async (categoryId, updates) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.put(`/categories/${categoryId}`, updates)
      const index = categories.value.findIndex(c => c.id === categoryId)
      if (index >= 0) {
        categories.value[index] = response.data
      }
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao atualizar categoria'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  const deleteCategory = async (categoryId) => {
    loading.value = true
    error.value = null

    try {
      await api.delete(`/categories/${categoryId}`)
      categories.value = categories.value.filter(c => c.id !== categoryId)
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao deletar categoria'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  return {
    categories,
    total,
    skip,
    limit,
    loading,
    error,
    fetchCategories,
    createCategory,
    updateCategory,
    deleteCategory,
  }
})
