<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-3xl font-bold text-gray-900">Categorias</h1>
      <button
        @click="openCreateModal"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
      >
        + Nova Categoria
      </button>
    </div>

    <div v-if="categoriesStore.loading" class="text-center py-8">
      <p class="text-gray-500">Carregando categorias...</p>
    </div>

    <div v-else-if="categoriesStore.categories.length === 0" class="text-center py-8">
      <p class="text-gray-500 mb-4">Nenhuma categoria cadastrada</p>
      <button
        @click="openCreateModal"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
      >
        Criar Primeira Categoria
      </button>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="category in categoriesStore.categories"
        :key="category.id"
        class="bg-white rounded-lg shadow p-4 flex items-center justify-between hover:shadow-md transition"
      >
        <div class="flex items-center gap-3">
          <div
            class="w-10 h-10 rounded-full flex items-center justify-center"
            :style="{ backgroundColor: category.color || '#3B82F6' }"
          >
            <span class="text-xl">{{ category.icon || '📦' }}</span>
          </div>
          <div>
            <p class="font-semibold text-gray-900">{{ category.name }}</p>
            <p v-if="category.description" class="text-sm text-gray-500">{{ category.description }}</p>
          </div>
        </div>
        <div class="flex gap-2">
          <button
            @click="openEditModal(category)"
            class="text-blue-600 hover:text-blue-900 transition"
          >
            Editar
          </button>
          <button
            @click="deleteCategory(category)"
            class="text-red-600 hover:text-red-900 transition"
          >
            Deletar
          </button>
        </div>
      </div>
    </div>

    <Modal
      :isOpen="showModal"
      :title="editingId ? 'Editar Categoria' : 'Nova Categoria'"
      submitLabel="Salvar"
      :isSubmitting="isSubmitting"
      @close="closeModal"
      @submit="saveCategory"
    >
      <FormGroup
        label="Nome"
        v-model="form.name"
        placeholder="Ex: Alimentação"
        required
        :error="errors.name"
      />

      <FormGroup
        label="Cor"
        type="color"
        v-model="form.color"
        :error="errors.color"
      />

      <FormGroup
        label="Ícone (emoji)"
        v-model="form.icon"
        placeholder="🍔"
        :error="errors.icon"
      />

      <FormGroup
        label="Descrição"
        type="textarea"
        v-model="form.description"
        placeholder="Descrição da categoria (opcional)"
        :error="errors.description"
      />
    </Modal>

    <Alert
      ref="alertRef"
      :type="alertType"
      :title="alertTitle"
      :message="alertMessage"
      :duration="3000"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useCategoriesStore } from '@/store/categories'
import Modal from '@/components/Modal.vue'
import FormGroup from '@/components/FormGroup.vue'
import Alert from '@/components/Alert.vue'

const categoriesStore = useCategoriesStore()
const alertRef = ref(null)

const showModal = ref(false)
const isSubmitting = ref(false)
const editingId = ref(null)
const alertType = ref('info')
const alertTitle = ref('')
const alertMessage = ref('')

const form = ref({
  name: '',
  color: '#3B82F6',
  icon: '📦',
  description: '',
})

const errors = ref({})

onMounted(() => {
  categoriesStore.fetchCategories()
})

const openCreateModal = () => {
  editingId.value = null
  form.value = { name: '', color: '#3B82F6', icon: '📦', description: '' }
  errors.value = {}
  showModal.value = true
}

const openEditModal = (category) => {
  editingId.value = category.id
  form.value = {
    name: category.name,
    color: category.color || '#3B82F6',
    icon: category.icon || '📦',
    description: category.description || '',
  }
  errors.value = {}
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  form.value = { name: '', color: '#3B82F6', icon: '📦', description: '' }
  errors.value = {}
}

const saveCategory = async () => {
  errors.value = {}

  if (!form.value.name.trim()) {
    errors.value.name = 'Nome é obrigatório'
    return
  }

  isSubmitting.value = true

  try {
    if (editingId.value) {
      await categoriesStore.updateCategory(editingId.value, form.value)
      showAlert('success', 'Sucesso', 'Categoria atualizada com sucesso')
    } else {
      await categoriesStore.createCategory(
        form.value.name,
        form.value.color,
        form.value.icon,
        form.value.description
      )
      showAlert('success', 'Sucesso', 'Categoria criada com sucesso')
    }

    closeModal()
  } catch (error) {
    showAlert('error', 'Erro', error.message || 'Erro ao salvar categoria')
  } finally {
    isSubmitting.value = false
  }
}

const deleteCategory = async (category) => {
  if (!confirm(`Deseja deletar a categoria "${category.name}"?`)) {
    return
  }

  try {
    await categoriesStore.deleteCategory(category.id)
    showAlert('success', 'Sucesso', 'Categoria deletada com sucesso')
  } catch (error) {
    showAlert('error', 'Erro', error.message || 'Erro ao deletar categoria')
  }
}

const showAlert = (type, title, message) => {
  alertType.value = type
  alertTitle.value = title
  alertMessage.value = message
  alertRef.value?.show()
}
</script>
