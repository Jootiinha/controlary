<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-3xl font-bold text-gray-900">Pagamentos</h1>
      <button
        @click="openCreateModal"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
      >
        + Novo Pagamento
      </button>
    </div>

    <div class="mb-4 flex gap-4">
      <label class="flex items-center gap-2">
        <input
          v-model="filterPaid"
          type="checkbox"
          class="rounded"
        />
        <span class="text-sm text-gray-600">Mostrar apenas pagos</span>
      </label>
    </div>

    <div v-if="paymentsStore.loading" class="text-center py-8">
      <p class="text-gray-500">Carregando pagamentos...</p>
    </div>

    <div v-else-if="filteredPayments.length === 0" class="text-center py-8">
      <p class="text-gray-500 mb-4">Nenhum pagamento registrado</p>
      <button
        @click="openCreateModal"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
      >
        Registrar Primeiro Pagamento
      </button>
    </div>

    <div v-else>
      <DataTable
        :data="filteredPayments"
        :columns="tableColumns"
        @edit="openEditModal"
        @delete="deletePayment"
      />

      <div class="mt-6">
        <Pagination
          :skip="paymentsStore.skip"
          :limit="paymentsStore.limit"
          :total="paymentsStore.total || filteredPayments.length"
          @update:skip="(val) => { paymentsStore.skip = val; paymentsStore.fetchPayments(filterPaid.value ? true : null) }"
          @update:limit="(val) => { paymentsStore.limit = val; paymentsStore.skip = 0; paymentsStore.fetchPayments(filterPaid.value ? true : null) }"
        />
      </div>
    </div>

    <Modal
      :isOpen="showModal"
      :title="editingId ? 'Editar Pagamento' : 'Novo Pagamento'"
      submitLabel="Salvar"
      :isSubmitting="isSubmitting"
      @close="closeModal"
      @submit="savePayment"
    >
      <FormGroup
        label="Descrição"
        v-model="form.description"
        placeholder="Ex: Supermercado"
        required
        :error="errors.description"
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
        label="Data"
        type="date"
        v-model="form.data"
        required
        :error="errors.data"
      />

      <FormGroup
        label="Categoria"
        type="select"
        v-model.number="form.category_id"
        :options="categoriesStore.categories"
        :error="errors.category_id"
      />

      <div class="mb-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <p class="text-sm font-medium text-blue-900 mb-3">Destino do Pagamento</p>
        <div class="space-y-2">
          <label class="flex items-center gap-2">
            <input
              v-model="form.paymentType"
              type="radio"
              value="account"
              class="rounded"
            />
            <span class="text-sm text-gray-700">Conta</span>
          </label>
          <label class="flex items-center gap-2">
            <input
              v-model="form.paymentType"
              type="radio"
              value="card"
              class="rounded"
            />
            <span class="text-sm text-gray-700">Cartão</span>
          </label>
        </div>
      </div>

      <FormGroup
        v-if="form.paymentType === 'account'"
        label="Selecionar Conta"
        type="select"
        v-model.number="form.account_id"
        :options="accountsStore.accounts"
        :error="errors.account_id"
      />

      <FormGroup
        v-if="form.paymentType === 'card'"
        label="Selecionar Cartão"
        type="select"
        v-model.number="form.card_id"
        :options="cardsStore.cards"
        :error="errors.card_id"
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
import { ref, onMounted, computed } from 'vue'
import { usePaymentsStore } from '@/store/payments'
import { useAccountsStore } from '@/store/accounts'
import { useCardsStore } from '@/store/cards'
import { useCategoriesStore } from '@/store/categories'
import Modal from '@/components/Modal.vue'
import DataTable from '@/components/DataTable.vue'
import FormGroup from '@/components/FormGroup.vue'
import Alert from '@/components/Alert.vue'
import Pagination from '@/components/Pagination.vue'

const paymentsStore = usePaymentsStore()
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
const filterPaid = ref(false)

const form = ref({
  description: '',
  amount: 0,
  data: new Date().toISOString().split('T')[0],
  category_id: null,
  account_id: null,
  card_id: null,
  paymentType: 'account',
})

const errors = ref({})

const tableColumns = [
  { key: 'description', label: 'Descrição' },
  { key: 'amount', label: 'Valor', type: 'currency' },
  { key: 'data', label: 'Data', type: 'date' },
  { key: 'is_paid', label: 'Status', type: 'badge' },
]

const filteredPayments = computed(() => {
  if (filterPaid.value) {
    return paymentsStore.payments.filter((p) => p.is_paid)
  }
  return paymentsStore.payments
})

onMounted(async () => {
  await Promise.all([
    paymentsStore.fetchPayments(),
    accountsStore.fetchAccounts(),
    cardsStore.fetchCards(),
    categoriesStore.fetchCategories(),
  ])
})

const openCreateModal = () => {
  editingId.value = null
  form.value = {
    description: '',
    amount: 0,
    data: new Date().toISOString().split('T')[0],
    category_id: null,
    account_id: null,
    card_id: null,
    paymentType: 'account',
  }
  errors.value = {}
  showModal.value = true
}

const openEditModal = (payment) => {
  editingId.value = payment.id
  form.value = {
    description: payment.description,
    amount: payment.amount,
    data: payment.data,
    category_id: payment.category_id,
    account_id: payment.account_id,
    card_id: payment.card_id,
    paymentType: payment.account_id ? 'account' : 'card',
  }
  errors.value = {}
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  form.value = {
    description: '',
    amount: 0,
    data: new Date().toISOString().split('T')[0],
    category_id: null,
    account_id: null,
    card_id: null,
    paymentType: 'account',
  }
  errors.value = {}
}

const savePayment = async () => {
  errors.value = {}

  if (!form.value.description.trim()) {
    errors.value.description = 'Descrição é obrigatória'
    return
  }

  if (form.value.amount <= 0) {
    errors.value.amount = 'Valor deve ser maior que 0'
    return
  }

  if (form.value.paymentType === 'account' && !form.value.account_id) {
    errors.value.account_id = 'Selecione uma conta'
    return
  }

  if (form.value.paymentType === 'card' && !form.value.card_id) {
    errors.value.card_id = 'Selecione um cartão'
    return
  }

  isSubmitting.value = true

  try {
    if (editingId.value) {
      await paymentsStore.updatePayment(editingId.value, {
        description: form.value.description,
        amount: form.value.amount,
        data: form.value.data,
        category_id: form.value.category_id,
        account_id: form.value.paymentType === 'account' ? form.value.account_id : null,
        card_id: form.value.paymentType === 'card' ? form.value.card_id : null,
      })
      showAlert('success', 'Sucesso', 'Pagamento atualizado com sucesso')
    } else {
      await paymentsStore.createPayment(
        form.value.description,
        form.value.amount,
        form.value.paymentType === 'account' ? form.value.account_id : null,
        form.value.paymentType === 'card' ? form.value.card_id : null,
        form.value.category_id,
        form.value.data
      )
      showAlert('success', 'Sucesso', 'Pagamento registrado com sucesso')
    }

    closeModal()
  } catch (error) {
    showAlert('error', 'Erro', error.message || 'Erro ao salvar pagamento')
  } finally {
    isSubmitting.value = false
  }
}

const deletePayment = async (payment) => {
  if (!confirm(`Deseja deletar o pagamento "${payment.description}"?`)) {
    return
  }

  try {
    await paymentsStore.deletePayment(payment.id)
    showAlert('success', 'Sucesso', 'Pagamento deletado com sucesso')
  } catch (error) {
    showAlert('error', 'Erro', error.message || 'Erro ao deletar pagamento')
  }
}

const showAlert = (type, title, message) => {
  alertType.value = type
  alertTitle.value = title
  alertMessage.value = message
  alertRef.value?.show()
}
</script>
