<template>
  <div class="overflow-x-auto">
    <table class="min-w-full divide-y divide-gray-200">
      <thead class="bg-gray-50">
        <tr>
          <th
            v-for="column in columns"
            :key="column.key"
            class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
            @click="toggleSort(column.key)"
          >
            <div class="flex items-center gap-2">
              {{ column.label }}
              <svg
                v-if="sortKey === column.key"
                class="w-4 h-4"
                :class="{ 'transform rotate-180': sortOrder === 'desc' }"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path d="M3 3a1 1 0 000 2h11a1 1 0 100-2H3zM3 7a1 1 0 000 2h5a1 1 0 000-2H3zM3 11a1 1 0 100 2h4a1 1 0 100-2H3z"></path>
              </svg>
            </div>
          </th>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            Ações
          </th>
        </tr>
      </thead>
      <tbody class="bg-white divide-y divide-gray-200">
        <tr v-for="row in sortedData" :key="row.id" class="hover:bg-gray-50">
          <td
            v-for="column in columns"
            :key="column.key"
            class="px-6 py-4 whitespace-nowrap text-sm text-gray-900"
          >
            <template v-if="column.type === 'currency'">
              {{ formatCurrency(row[column.key]) }}
            </template>
            <template v-else-if="column.type === 'date'">
              {{ formatDate(row[column.key]) }}
            </template>
            <template v-else-if="column.type === 'badge'">
              <span
                :class="[
                  'px-3 py-1 text-xs font-medium rounded-full',
                  getBadgeClasses(row[column.key])
                ]"
              >
                {{ row[column.key] }}
              </span>
            </template>
            <template v-else>
              {{ row[column.key] }}
            </template>
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
            <button
              @click="$emit('edit', row)"
              class="text-blue-600 hover:text-blue-900 mr-4"
            >
              Editar
            </button>
            <button
              @click="$emit('delete', row)"
              class="text-red-600 hover:text-red-900"
            >
              Deletar
            </button>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="data.length === 0" class="text-center py-8 text-gray-500">
      Nenhum registro encontrado
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  data: {
    type: Array,
    required: true,
  },
  columns: {
    type: Array,
    required: true,
  },
})

defineEmits(['edit', 'delete'])

const sortKey = ref(null)
const sortOrder = ref('asc')

const sortedData = computed(() => {
  if (!sortKey.value) return props.data

  return [...props.data].sort((a, b) => {
    const aVal = a[sortKey.value]
    const bVal = b[sortKey.value]

    if (typeof aVal === 'string') {
      return sortOrder.value === 'asc'
        ? aVal.localeCompare(bVal)
        : bVal.localeCompare(aVal)
    }

    return sortOrder.value === 'asc' ? aVal - bVal : bVal - aVal
  })
})

const toggleSort = (key) => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortOrder.value = 'asc'
  }
}

const formatCurrency = (value) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value)
}

const formatDate = (value) => {
  return new Intl.DateTimeFormat('pt-BR').format(new Date(value))
}

const getBadgeClasses = (value) => {
  const statusClasses = {
    'Ativa': 'bg-green-100 text-green-800',
    'Pausada': 'bg-yellow-100 text-yellow-800',
    'Cancelada': 'bg-red-100 text-red-800',
    'Recebida': 'bg-green-100 text-green-800',
    'Paga': 'bg-green-100 text-green-800',
    'Pendente': 'bg-yellow-100 text-yellow-800',
  }
  return statusClasses[value] || 'bg-gray-100 text-gray-800'
}
</script>
