<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-3xl font-bold text-gray-900">Contas</h1>
      <button
        @click="openCreateModal"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
      >
        + Nova Conta
      </button>
    </div>

    <div v-if="accountsStore.loading" class="text-center py-8">
      <p class="text-gray-500">Carregando contas...</p>
    </div>

    <div v-else-if="accountsStore.accounts.length === 0" class="text-center py-8">
      <p class="text-gray-500 mb-4">Nenhuma conta cadastrada</p>
      <button
        @click="openCreateModal"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
      >
        Criar Primeira Conta
      </button>
    </div>

    <div v-else>
      <DataTable
        :data="accountsStore.accounts"
        :columns="tableColumns"
        @edit="openEditModal"
        @delete="deleteAccount"
      />

      <div class="mt-6">
        <Pagination
          :skip="accountsStore.skip"
          :limit="accountsStore.limit"
          :total="accountsStore.total || accountsStore.accounts.length"
          @update:skip="(val) => { accountsStore.skip = val; accountsStore.fetchAccounts() }"
          @update:limit="(val) => { accountsStore.limit = val; accountsStore.skip = 0; accountsStore.fetchAccounts() }"
        />
      </div>
    </div>

    <Modal
      :isOpen="showModal"
      :title="editingId ? 'Editar Conta' : 'Nova Conta'"
      submitLabel="Salvar"
      :isSubmitting="isSubmitting"
      @close="closeModal"
      @submit="saveAccount"
    >
      <FormGroup
        label="Nome"
        v-model="form.name"
        placeholder="Ex: Conta Corrente"
        required
        :error="errors.name"
      />
      <FormGroup
        label="Descrição"
        type="textarea"
        v-model="form.description"
        placeholder="Descrição da conta (opcional)"
        :error="errors.description"
      />
      <FormGroup
        v-if="!editingId"
        label="Saldo Inicial"
        type="number"
        v-model.number="form.initialBalance"
        placeholder="0.00"
        step="0.01"
        :error="errors.initialBalance"
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
import { useAccountsStore } from '@/store/accounts'
import Modal from '@/components/Modal.vue'
import DataTable from '@/components/DataTable.vue'
import FormGroup from '@/components/FormGroup.vue'
import Alert from '@/components/Alert.vue'
import Pagination from '@/components/Pagination.vue'

const accountsStore = useAccountsStore()
const alertRef = ref(null)

const showModal = ref(false)
const isSubmitting = ref(false)
const editingId = ref(null)
const alertType = ref('info')
const alertTitle = ref('')
const alertMessage = ref('')

const form = ref({
  name: '',
  description: '',
  initialBalance: 0,
})

const errors = ref({})

const tableColumns = [
  { key: 'name', label: 'Nome' },
  { key: 'description', label: 'Descrição' },
  { key: 'current_balance', label: 'Saldo', type: 'currency' },
]

onMounted(() => {
  accountsStore.fetchAccounts()
})

const openCreateModal = () => {
  editingId.value = null
  form.value = { name: '', description: '', initialBalance: 0 }
  errors.value = {}
  showModal.value = true
}

const openEditModal = (account) => {
  editingId.value = account.id
  form.value = {
    name: account.name,
    description: account.description || '',
  }
  errors.value = {}
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  form.value = { name: '', description: '', initialBalance: 0 }
  errors.value = {}
}

const saveAccount = async () => {
  errors.value = {}

  if (!form.value.name.trim()) {
    errors.value.name = 'Nome é obrigatório'
    return
  }

  isSubmitting.value = true

  try {
    if (editingId.value) {
      await accountsStore.updateAccount(editingId.value, {
        name: form.value.name,
        description: form.value.description,
      })
      showAlert('success', 'Sucesso', 'Conta atualizada com sucesso')
    } else {
      await accountsStore.createAccount(
        form.value.name,
        form.value.description,
        form.value.initialBalance
      )
      showAlert('success', 'Sucesso', 'Conta criada com sucesso')
    }

    closeModal()
  } catch (error) {
    showAlert('error', 'Erro', error.message || 'Erro ao salvar conta')
  } finally {
    isSubmitting.value = false
  }
}

const deleteAccount = async (account) => {
  if (!confirm(`Deseja deletar a conta "${account.name}"?`)) {
    return
  }

  try {
    await accountsStore.deleteAccount(account.id)
    showAlert('success', 'Sucesso', 'Conta deletada com sucesso')
  } catch (error) {
    showAlert('error', 'Erro', error.message || 'Erro ao deletar conta')
  }
}

const showAlert = (type, title, message) => {
  alertType.value = type
  alertTitle.value = title
  alertMessage.value = message
  alertRef.value?.show()
}
</script>
