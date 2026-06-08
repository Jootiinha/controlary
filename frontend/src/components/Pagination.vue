<template>
  <div class="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
    <div class="flex flex-col sm:flex-row items-center justify-between gap-4">
      <!-- Left side: Page size selector and info -->
      <div class="flex items-center gap-4">
        <div class="flex items-center gap-2">
          <label for="pageSize" class="text-sm text-gray-600 font-medium">Items por página:</label>
          <select
            id="pageSize"
            v-model.number="selectedPageSize"
            @change="handlePageSizeChange"
            class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option :value="10">10</option>
            <option :value="25">25</option>
            <option :value="50">50</option>
          </select>
        </div>

        <div class="text-sm text-gray-600">
          Mostrando <span class="font-medium">{{ startRecord }}</span>-<span class="font-medium">{{ endRecord }}</span>
          de <span class="font-medium">{{ total }}</span>
        </div>
      </div>

      <!-- Right side: Navigation buttons -->
      <div class="flex items-center gap-2">
        <button
          @click="previousPage"
          :disabled="skip === 0"
          class="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          ← Anterior
        </button>

        <div class="text-sm text-gray-600 px-2">
          Página <span class="font-medium">{{ currentPage }}</span> de <span class="font-medium">{{ totalPages }}</span>
        </div>

        <button
          @click="nextPage"
          :disabled="skip + limit >= total"
          class="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          Próxima →
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  skip: {
    type: Number,
    required: true,
  },
  limit: {
    type: Number,
    required: true,
  },
  total: {
    type: Number,
    required: true,
  },
})

const emit = defineEmits(['update:skip', 'update:limit'])

const selectedPageSize = ref(props.limit)

const currentPage = computed(() => {
  if (props.limit === 0) return 1
  return Math.floor(props.skip / props.limit) + 1
})

const totalPages = computed(() => {
  if (props.limit === 0) return 1
  return Math.ceil(props.total / props.limit)
})

const startRecord = computed(() => {
  if (props.total === 0) return 0
  return props.skip + 1
})

const endRecord = computed(() => {
  const end = props.skip + props.limit
  return Math.min(end, props.total)
})

const previousPage = () => {
  if (props.skip > 0) {
    emit('update:skip', Math.max(0, props.skip - props.limit))
  }
}

const nextPage = () => {
  if (props.skip + props.limit < props.total) {
    emit('update:skip', props.skip + props.limit)
  }
}

const handlePageSizeChange = () => {
  emit('update:limit', selectedPageSize.value)
  emit('update:skip', 0) // Reset to first page when changing page size
}
</script>
