<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-3xl font-bold text-gray-900">Cartões</h1>
      <button
        @click="openCreateModal"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
      >
        + Novo Cartão
      </button>
    </div>

    <div v-if="cardsStore.loading" class="text-center py-8">
      <p class="text-gray-500">Carregando cartões...</p>
    </div>

    <div v-else-if="cardsStore.cards.length === 0" class="text-center py-8">
      <p class="text-gray-500 mb-4">Nenhum cartão cadastrado</p>
      <button
        @click="openCreateModal"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
      >
        Registrar Primeiro Cartão
      </button>
    </div>

    <div v-else>
      <DataTable
        :data="cardsStore.cards"
        :columns="tableColumns"
        @edit="openEditModal"
        @delete="deleteCard"
      />

      <div class="mt-6">
        <Pagination
          :skip="cardsStore.skip"
          :limit="cardsStore.limit"
          :total="cardsStore.total || cardsStore.cards.length"
          @update:skip="(val) => { cardsStore.skip = val; cardsStore.fetchCards() }"
          @update:limit="(val) => { cardsStore.limit = val; cardsStore.skip = 0; cardsStore.fetchCards() }"
        />
      </div>
    </div>

    <Modal
      :isOpen="showModal"
      :title="editingId ? 'Editar Cartão' : 'Novo Cartão'"
      submitLabel="Salvar"
      :isSubmitting="isSubmitting"
      @close="closeModal"
      @submit="saveCard"
    >
      <FormGroup
        label="Nome"
        v-model="form.name"
        placeholder="Ex: Crédito Pessoal"
        required
        :error="errors.name"
      />

      <FormGroup
        label="Últimos Dígitos"
        v-model="form.final_digits"
        placeholder="1234"
        required
        :error="errors.final_digits"
      />

      <FormGroup
        label="Limite"
        type="number"
        v-model.number="form.limit"
        placeholder="0.00"
        step="0.01"
        required
        :error="errors.limit"
      />

      <FormGroup
        label="Dia de Fechamento"
        type="number"
        v-model.number="form.day_close"
        placeholder="10"
        min="1"
        max="31"
        required
        :error="errors.day_close"
      />

      <FormGroup
        label="Dia de Vencimento"
        type="number"
        v-model.number="form.day_due"
        placeholder="15"
        min="1"
        max="31"
        required
        :error="errors.day_due"
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
import { useCardsStore } from '@/store/cards'
import Modal from '@/components/Modal.vue'
import DataTable from '@/components/DataTable.vue'
import FormGroup from '@/components/FormGroup.vue'
import Alert from '@/components/Alert.vue'
import Pagination from '@/components/Pagination.vue'

const cardsStore = useCardsStore()
const alertRef = ref(null)

const showModal = ref(false)
const isSubmitting = ref(false)
const editingId = ref(null)
const alertType = ref('info')
const alertTitle = ref('')
const alertMessage = ref('')

const form = ref({
  name: '',
  final_digits: '',
  limit: 0,
  day_close: 10,
  day_due: 15,
})

const errors = ref({})

const tableColumns = [
  { key: 'name', label: 'Nome' },
  { key: 'final_digits', label: 'Últimos Dígitos' },
  { key: 'limit', label: 'Limite', type: 'currency' },
  { key: 'day_close', label: 'Fechamento' },
  { key: 'day_due', label: 'Vencimento' },
]

onMounted(() => {
  cardsStore.fetchCards()
})

const openCreateModal = () => {
  editingId.value = null
  form.value = { name: '', final_digits: '', limit: 0, day_close: 10, day_due: 15 }
  errors.value = {}
  showModal.value = true
}

const openEditModal = (card) => {
  editingId.value = card.id
  form.value = {
    name: card.name,
    final_digits: card.final_digits,
    limit: card.limit,
    day_close: card.day_close,
    day_due: card.day_due,
  }
  errors.value = {}
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  form.value = { name: '', final_digits: '', limit: 0, day_close: 10, day_due: 15 }
  errors.value = {}
}

const saveCard = async () => {
  errors.value = {}

  if (!form.value.name.trim()) {
    errors.value.name = 'Nome é obrigatório'
    return
  }

  if (!form.value.final_digits.trim()) {
    errors.value.final_digits = 'Últimos dígitos são obrigatórios'
    return
  }

  if (form.value.limit <= 0) {
    errors.value.limit = 'Limite deve ser maior que 0'
    return
  }

  if (!form.value.day_close || form.value.day_close < 1 || form.value.day_close > 31) {
    errors.value.day_close = 'Dia deve estar entre 1 e 31'
    return
  }

  if (!form.value.day_due || form.value.day_due < 1 || form.value.day_due > 31) {
    errors.value.day_due = 'Dia deve estar entre 1 e 31'
    return
  }

  isSubmitting.value = true

  try {
    if (editingId.value) {
      await cardsStore.updateCard(editingId.value, form.value)
      showAlert('success', 'Sucesso', 'Cartão atualizado com sucesso')
    } else {
      await cardsStore.createCard(
        form.value.name,
        form.value.final_digits,
        form.value.limit,
        form.value.day_close,
        form.value.day_due
      )
      showAlert('success', 'Sucesso', 'Cartão criado com sucesso')
    }

    closeModal()
  } catch (error) {
    showAlert('error', 'Erro', error.message || 'Erro ao salvar cartão')
  } finally {
    isSubmitting.value = false
  }
}

const deleteCard = async (card) => {
  if (!confirm(`Deseja deletar o cartão "${card.name}"?`)) {
    return
  }

  try {
    await cardsStore.deleteCard(card.id)
    showAlert('success', 'Sucesso', 'Cartão deletado com sucesso')
  } catch (error) {
    showAlert('error', 'Erro', error.message || 'Erro ao deletar cartão')
  }
}

const showAlert = (type, title, message) => {
  alertType.value = type
  alertTitle.value = title
  alertMessage.value = message
  alertRef.value?.show()
}
</script>
