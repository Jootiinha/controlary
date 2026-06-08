<template>
  <div class="bg-white rounded-lg shadow p-6">
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-xl font-bold text-gray-900">
        {{ monthName }} de {{ currentYear }}
      </h2>
      <div class="flex gap-2">
        <button
          @click="previousMonth"
          class="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition"
        >
          ← Anterior
        </button>
        <button
          @click="nextMonth"
          class="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition"
        >
          Próxima →
        </button>
      </div>
    </div>

    <!-- Cabeçalho com dias da semana -->
    <div class="grid grid-cols-7 gap-2 mb-2">
      <div v-for="day in dayLabels" :key="day" class="text-center font-bold text-gray-600 text-sm py-2">
        {{ day }}
      </div>
    </div>

    <!-- Calendário -->
    <div class="grid grid-cols-7 gap-2">
      <div
        v-for="(day, index) in calendarDays"
        :key="index"
        class="border rounded p-2 h-24 overflow-y-auto transition hover:shadow-md"
        :class="day ? 'bg-gray-50 hover:bg-blue-50' : 'bg-gray-100'"
      >
        <!-- Day number -->
        <div v-if="day" class="font-bold text-sm text-gray-700 mb-1">{{ day }}</div>

        <!-- Payments for this day -->
        <div v-for="payment in getPaymentsForDay(day)" :key="payment.id" class="mb-1">
          <button
            @click="selectPayment(payment)"
            class="w-full px-2 py-1 rounded text-white text-xs cursor-pointer transition hover:opacity-80"
            :class="getPaymentStatusClass(payment)"
            :title="`${payment.description} - R$ ${formatCurrency(payment.amount)}`"
          >
            <span class="truncate block">{{ payment.description.substring(0, 10) }}...</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Legend -->
    <div class="mt-6 flex flex-wrap gap-6 justify-center text-sm">
      <div class="flex items-center gap-2">
        <div class="w-4 h-4 rounded bg-green-500"></div>
        <span class="text-gray-700">Pago</span>
      </div>
      <div class="flex items-center gap-2">
        <div class="w-4 h-4 rounded bg-yellow-500"></div>
        <span class="text-gray-700">Pendente</span>
      </div>
      <div class="flex items-center gap-2">
        <div class="w-4 h-4 rounded bg-red-500"></div>
        <span class="text-gray-700">Atrasado</span>
      </div>
      <div class="flex items-center gap-2">
        <div class="w-4 h-4 rounded bg-gray-300"></div>
        <span class="text-gray-700">Sem Pagamento</span>
      </div>
    </div>

    <!-- Modal para detalhes do pagamento -->
    <Teleport to="body">
      <div
        v-if="selectedPaymentData"
        class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        @click="selectedPaymentData = null"
      >
        <div
          class="bg-white rounded-lg shadow-lg p-6 max-w-md w-full mx-4"
          @click.stop
        >
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-bold text-gray-900">{{ selectedPaymentData.description }}</h3>
            <button
              @click="selectedPaymentData = null"
              class="text-gray-500 hover:text-gray-700 text-2xl font-bold"
            >
              ×
            </button>
          </div>

          <div class="space-y-3 mb-6">
            <div class="flex justify-between">
              <span class="text-gray-600">Valor:</span>
              <span class="font-bold text-gray-900">R$ {{ formatCurrency(selectedPaymentData.amount) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">Data:</span>
              <span class="font-bold text-gray-900">{{ formatDate(selectedPaymentData.data) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">Status:</span>
              <span
                class="px-3 py-1 rounded-full text-sm font-bold"
                :class="getPaymentStatusBadgeClass(selectedPaymentData)"
              >
                {{ getPaymentStatusLabel(selectedPaymentData) }}
              </span>
            </div>
            <div v-if="selectedPaymentData.category" class="flex justify-between">
              <span class="text-gray-600">Categoria:</span>
              <span class="font-bold text-gray-900">{{ selectedPaymentData.category }}</span>
            </div>
          </div>

          <div class="flex gap-2">
            <button
              @click="selectedPaymentData = null"
              class="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition font-medium"
            >
              Fechar
            </button>
            <button
              v-if="!selectedPaymentData.is_paid"
              @click="markAsPaid"
              class="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium"
            >
              Marcar Pago
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  payments: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['payment-marked-paid'])

const currentDate = ref(new Date())
const selectedPaymentData = ref(null)
const dayLabels = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab']
const monthNames = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
]

const monthName = computed(() => monthNames[currentDate.value.getMonth()])
const currentYear = computed(() => currentDate.value.getFullYear())

const daysInMonth = computed(() => {
  return new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() + 1, 0).getDate()
})

const firstDayOfMonth = computed(() => {
  return new Date(currentDate.value.getFullYear(), currentDate.value.getMonth(), 1).getDay()
})

const calendarDays = computed(() => {
  const days = []
  // Empty cells before first day
  for (let i = 0; i < firstDayOfMonth.value; i++) {
    days.push(null)
  }
  // Days of month
  for (let i = 1; i <= daysInMonth.value; i++) {
    days.push(i)
  }
  return days
})

const getPaymentsForDay = (day) => {
  if (!day) return []
  return props.payments.filter((p) => {
    const date = new Date(p.data)
    return (
      date.getDate() === day &&
      date.getMonth() === currentDate.value.getMonth() &&
      date.getFullYear() === currentDate.value.getFullYear()
    )
  })
}

const isPastDue = (payment) => {
  const now = new Date()
  const paymentDate = new Date(payment.data)
  return !payment.is_paid && paymentDate < now
}

const getPaymentStatusClass = (payment) => {
  if (payment.is_paid) return 'bg-green-500 hover:bg-green-600'
  if (isPastDue(payment)) return 'bg-red-500 hover:bg-red-600'
  return 'bg-yellow-500 hover:bg-yellow-600'
}

const getPaymentStatusBadgeClass = (payment) => {
  if (payment.is_paid) return 'bg-green-100 text-green-800'
  if (isPastDue(payment)) return 'bg-red-100 text-red-800'
  return 'bg-yellow-100 text-yellow-800'
}

const getPaymentStatusLabel = (payment) => {
  if (payment.is_paid) return 'Pago'
  if (isPastDue(payment)) return 'Atrasado'
  return 'Pendente'
}

const formatCurrency = (value) => {
  return parseFloat(value).toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

const formatDate = (date) => {
  return new Date(date).toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

const previousMonth = () => {
  currentDate.value = new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() - 1)
}

const nextMonth = () => {
  currentDate.value = new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() + 1)
}

const selectPayment = (payment) => {
  selectedPaymentData.value = { ...payment }
}

const markAsPaid = async () => {
  emit('payment-marked-paid', selectedPaymentData.value.id)
  selectedPaymentData.value = null
}
</script>
