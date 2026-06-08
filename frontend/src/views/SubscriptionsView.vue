<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-3xl font-bold text-gray-900">Assinaturas</h1>
      <button
        @click="openCreateModal"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
      >
        + Nova Assinatura
      </button>
    </div>

    <div v-if="subscriptionsStore.loading" class="text-center py-8">
      <p class="text-gray-500">Carregando assinaturas...</p>
    </div>

    <div v-else-if="subscriptionsStore.subscriptions.length === 0" class="text-center py-8">
      <p class="text-gray-500 mb-4">Nenhuma assinatura cadastrada</p>
      <button
        @click="openCreateModal"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
      >
        Criar Primeira Assinatura
      </button>
    </div>

    <div v-else class="space-y-4">
      <div
        v-for="subscription in subscriptionsStore.subscriptions"
        :key="subscription.id"
        class="bg-white rounded-lg shadow p-4 flex items-center justify-between hover:shadow-md transition"
      >
        <div class="flex-1">
          <div class="flex items-center gap-3">
            <div>
              <h3 class="font-semibold text-gray-900">{{ subscription.name }}</h3>
              <p class="text-sm text-gray-500">Renovação no dia {{ subscription.renewal_day }}</p>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-6">
          <div class="text-right">
            <p class="text-2xl font-bold text-gray-900">{{ formatCurrency(subscription.amount) }}</p>
            <span
              :class="[
                'text-xs font-medium px-2 py-1 rounded',
                getStatusClasses(subscription.status)
              ]"
            >
              {{ subscription.status }}
            </span>
          </div>

          <div class="flex gap-2">
            <button
              v-if="subscription.status === 'Ativa'"
              @click="pauseSubscription(subscription)"
              class="px-3 py-1 text-sm bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200 transition"
            >
              Pausar
            </button>
            <button
              v-if="subscription.status === 'Pausada'"
              @click="activateSubscription(subscription)"
              class="px-3 py-1 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200 transition"
            >
              Ativar
            </button>
            <button
              v-if="subscription.status !== 'Cancelada'"
              @click="cancelSubscription(subscription)"
              class="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 transition"
            >
              Cancelar
            </button>
            <button
              @click="openEditModal(subscription)"
              class="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition"
            >
              Editar
            </button>
            <button
              @click="deleteSubscription(subscription)"
              class="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition"
            >
              Deletar
            </button>
          </div>
        </div>
      </div>
    </div>

    <Modal
      :isOpen="showModal"
      :title="editingId ? 'Editar Assinatura' : 'Nova Assinatura'"
      submitLabel="Salvar"
      :isSubmitting="isSubmitting"
      @close="closeModal"
      @submit="saveSubscription"
    >
      <FormGroup
        label="Nome"
        v-model="form.name"
        placeholder="Ex: Netflix"
        required
        :error="errors.name"
      />

      <FormGroup
        label="Valor"
        type="number"
        v-model.number="form.amount"
        placeholder="0.00"
        step="0.01"
        required
        :error="errors.amount"
      />

      <FormGroup
        label="Categoria"
        type="select"
        v-model.number="form.category_id"
        :options="categoriesStore.categories"
        :error="errors.category_id"
      />

      <div class="mb-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <p class="text-sm font-medium text-blue-900 mb-3">Destino</p>
        <div class="space-y-2">
          <label class="flex items-center gap-2">
            <input
              v-model="form.destinationType"
              type="radio"
              value="account"
              class="rounded"
            />
            <span class="text-sm text-gray-700">Conta</span>
          </label>
          <label class="flex items-center gap-2">
            <input
              v-model="form.destinationType"
              type="radio"
              value="card"
              class="rounded"
            />
            <span class="text-sm text-gray-700">Cartão</span>
          </label>
        </div>
      </div>

      <FormGroup
        v-if="form.destinationType === 'account'"
        label="Selecionar Conta"
        type="select"
        v-model.number="form.account_id"
        :options="accountsStore.accounts"
        :error="errors.account_id"
      />

      <FormGroup
        v-if="form.destinationType === 'card'"
        label="Selecionar Cartão"
        type="select"
        v-model.number="form.card_id"
        :options="cardsStore.cards"
        :error="errors.card_id"
      />

      <FormGroup
        label="Dia de Renovação"
        type="number"
        v-model.number="form.renewal_day"
        placeholder="15"
        min="1"
        max="31"
        required
        :error="errors.renewal_day"
      />

      <FormGroup
        v-if="!editingId"
        label="Data de Início"
        type="date"
        v-model="form.start_date"
        required
        :error="errors.start_date"
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
import { useSubscriptionsStore } from '@/store/subscriptions'
import { useAccountsStore } from '@/store/accounts'
import { useCardsStore } from '@/store/cards'
import { useCategoriesStore } from '@/store/categories'
import Modal from '@/components/Modal.vue'
import FormGroup from '@/components/FormGroup.vue'
import Alert from '@/components/Alert.vue'

const subscriptionsStore = useSubscriptionsStore()
const accountsStore = useAccountsStore()
const cardsStore = useCardsStore()
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
  amount: 0,
  category_id: null,
  account_id: null,
  card_id: null,
  destinationType: 'account',
  renewal_day: 15,
  start_date: new Date().toISOString().split('T')[0],
})

const errors = ref({})

onMounted(async () => {
  await Promise.all([
    subscriptionsStore.fetchSubscriptions(),
    accountsStore.fetchAccounts(),
    cardsStore.fetchCards(),
    categoriesStore.fetchCategories(),
  ])
})

const openCreateModal = () => {
  editingId.value = null
  form.value = {
    name: '',
    amount: 0,
    category_id: null,
    account_id: null,
    card_id: null,
    destinationType: 'account',
    renewal_day: 15,
    start_date: new Date().toISOString().split('T')[0],
  }
  errors.value = {}
  showModal.value = true
}

const openEditModal = (subscription) => {
  editingId.value = subscription.id
  form.value = {
    name: subscription.name,
    amount: subscription.amount,
    category_id: subscription.category_id,
    account_id: subscription.account_id,
    card_id: subscription.card_id,
    destinationType: subscription.account_id ? 'account' : 'card',
    renewal_day: subscription.renewal_day,
    start_date: subscription.start_date,
  }
  errors.value = {}
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  form.value = {
    name: '',
    amount: 0,
    category_id: null,
    account_id: null,
    card_id: null,
    destinationType: 'account',
    renewal_day: 15,
    start_date: new Date().toISOString().split('T')[0],
  }
  errors.value = {}
}

const saveSubscription = async () => {
  errors.value = {}

  if (!form.value.name.trim()) {
    errors.value.name = 'Nome é obrigatório'
    return
  }

  if (form.value.amount <= 0) {
    errors.value.amount = 'Valor deve ser maior que 0'
    return
  }

  if (form.value.destinationType === 'account' && !form.value.account_id) {
    errors.value.account_id = 'Selecione uma conta'
    return
  }

  if (form.value.destinationType === 'card' && !form.value.card_id) {
    errors.value.card_id = 'Selecione um cartão'
    return
  }

  isSubmitting.value = true

  try {
    if (editingId.value) {
      await subscriptionsStore.updateSubscription(editingId.value, {
        name: form.value.name,
        amount: form.value.amount,
        category_id: form.value.category_id,
        account_id: form.value.destinationType === 'account' ? form.value.account_id : null,
        card_id: form.value.destinationType === 'card' ? form.value.card_id : null,
        renewal_day: form.value.renewal_day,
      })
      showAlert('success', 'Sucesso', 'Assinatura atualizada com sucesso')
    } else {
      await subscriptionsStore.createSubscription(
        form.value.name,
        form.value.amount,
        form.value.destinationType === 'account' ? form.value.account_id : null,
        form.value.destinationType === 'card' ? form.value.card_id : null,
        form.value.category_id,
        form.value.start_date,
        form.value.renewal_day
      )
      showAlert('success', 'Sucesso', 'Assinatura criada com sucesso')
    }

    closeModal()
  } catch (error) {
    showAlert('error', 'Erro', error.message || 'Erro ao salvar assinatura')
  } finally {
    isSubmitting.value = false
  }
}

const pauseSubscription = async (subscription) => {
  try {
    await subscriptionsStore.pauseSubscription(subscription.id)
    showAlert('success', 'Sucesso', 'Assinatura pausada com sucesso')
  } catch (error) {
    showAlert('error', 'Erro', error.message || 'Erro ao pausar assinatura')
  }
}

const activateSubscription = async (subscription) => {
  try {
    await subscriptionsStore.activateSubscription(subscription.id)
    showAlert('success', 'Sucesso', 'Assinatura ativada com sucesso')
  } catch (error) {
    showAlert('error', 'Erro', error.message || 'Erro ao ativar assinatura')
  }
}

const cancelSubscription = async (subscription) => {
  if (!confirm(`Deseja cancelar a assinatura "${subscription.name}"?`)) {
    return
  }

  try {
    await subscriptionsStore.cancelSubscription(subscription.id)
    showAlert('success', 'Sucesso', 'Assinatura cancelada com sucesso')
  } catch (error) {
    showAlert('error', 'Erro', error.message || 'Erro ao cancelar assinatura')
  }
}

const deleteSubscription = async (subscription) => {
  if (!confirm(`Deseja deletar a assinatura "${subscription.name}"?`)) {
    return
  }

  try {
    await subscriptionsStore.deleteSubscription(subscription.id)
    showAlert('success', 'Sucesso', 'Assinatura deletada com sucesso')
  } catch (error) {
    showAlert('error', 'Erro', error.message || 'Erro ao deletar assinatura')
  }
}

const formatCurrency = (value) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value)
}

const getStatusClasses = (status) => {
  const classes = {
    'Ativa': 'bg-green-100 text-green-800',
    'Pausada': 'bg-yellow-100 text-yellow-800',
    'Cancelada': 'bg-red-100 text-red-800',
  }
  return classes[status] || 'bg-gray-100 text-gray-800'
}

const showAlert = (type, title, message) => {
  alertType.value = type
  alertTitle.value = title
  alertMessage.value = message
  alertRef.value?.show()
}
</script>
