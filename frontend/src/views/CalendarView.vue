<template>
  <div>
    <div class="flex items-center justify-between mb-8">
      <h1 class="text-3xl font-bold text-gray-900">Calendário de Pagamentos</h1>
      <div class="flex gap-2">
        <button
          @click="showUpcomingOnly = !showUpcomingOnly"
          class="px-4 py-2 rounded-lg font-medium transition"
          :class="showUpcomingOnly ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'"
        >
          {{ showUpcomingOnly ? 'Mostrando: Próximos' : 'Mostrando: Todos' }}
        </button>
      </div>
    </div>

    <div v-if="paymentsStore.loading" class="text-center py-12">
      <p class="text-gray-500">Carregando pagamentos...</p>
    </div>

    <div v-else>
      <PaymentCalendar
        :payments="filteredPayments"
        @payment-marked-paid="markPaymentAsPaid"
      />

      <!-- Summary Stats -->
      <div class="mt-8 grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="bg-white rounded-lg shadow p-4">
          <p class="text-sm text-gray-600 mb-1">Total de Pagamentos</p>
          <p class="text-2xl font-bold text-gray-900">{{ filteredPayments.length }}</p>
        </div>
        <div class="bg-white rounded-lg shadow p-4">
          <p class="text-sm text-gray-600 mb-1">Pagos</p>
          <p class="text-2xl font-bold text-green-600">{{ paidCount }}</p>
        </div>
        <div class="bg-white rounded-lg shadow p-4">
          <p class="text-sm text-gray-600 mb-1">Pendentes</p>
          <p class="text-2xl font-bold text-yellow-600">{{ pendingCount }}</p>
        </div>
        <div class="bg-white rounded-lg shadow p-4">
          <p class="text-sm text-gray-600 mb-1">Atrasados</p>
          <p class="text-2xl font-bold text-red-600">{{ overdueCount }}</p>
        </div>
      </div>

      <!-- Alert for overdue payments -->
      <div v-if="overdueCount > 0" class="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
        <p class="text-red-800 font-semibold">
          ⚠️ Você tem {{ overdueCount }} pagamento(s) atrasado(s). Clique em um pagamento para marcá-lo como pago.
        </p>
      </div>
    </div>

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
import { ref, computed, onMounted } from 'vue'
import { usePaymentsStore } from '@/store/payments'
import PaymentCalendar from '@/components/PaymentCalendar.vue'
import Alert from '@/components/Alert.vue'

const paymentsStore = usePaymentsStore()
const alertRef = ref(null)
const showUpcomingOnly = ref(false)

const alertType = ref('info')
const alertTitle = ref('')
const alertMessage = ref('')

const filteredPayments = computed(() => {
  if (!showUpcomingOnly.value) {
    return paymentsStore.payments
  }

  const now = new Date()
  const futureDate = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000) // 30 days from now
  const pastDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000) // 30 days ago

  return paymentsStore.payments.filter((p) => {
    const paymentDate = new Date(p.data)
    return paymentDate >= pastDate && paymentDate <= futureDate
  })
})

const paidCount = computed(() => {
  return filteredPayments.value.filter((p) => p.is_paid).length
})

const pendingCount = computed(() => {
  const now = new Date()
  return filteredPayments.value.filter((p) => !p.is_paid && new Date(p.data) >= now).length
})

const overdueCount = computed(() => {
  const now = new Date()
  return filteredPayments.value.filter((p) => !p.is_paid && new Date(p.data) < now).length
})

onMounted(async () => {
  // Fetch payments with a large limit to get all upcoming payments
  // Since we don't know the exact count, fetch with skip=0 and a large limit
  paymentsStore.limit = 1000
  paymentsStore.skip = 0
  await paymentsStore.fetchPayments()
})

const markPaymentAsPaid = async (paymentId) => {
  try {
    await paymentsStore.markPaid(paymentId)
    showAlert('success', 'Sucesso', 'Pagamento marcado como pago com sucesso')
    // Refresh the calendar
    await paymentsStore.fetchPayments()
  } catch (error) {
    showAlert('error', 'Erro', error.message || 'Erro ao marcar pagamento como pago')
  }
}

const showAlert = (type, title, message) => {
  alertType.value = type
  alertTitle.value = title
  alertMessage.value = message
  alertRef.value?.show()
}
</script>
