<template>
  <div
    class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-bold"
    :class="badgeClass"
  >
    <span class="text-lg">{{ arrow }}</span>
    <span>{{ percentChange }}%</span>
    <span v-if="period" class="text-xs opacity-75">vs {{ period }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  current: {
    type: Number,
    required: true,
  },
  previous: {
    type: Number,
    required: true,
  },
  isPositiveGood: {
    type: Boolean,
    default: true, // True if increase is good (e.g., income), false if increase is bad (e.g., expense)
  },
  period: {
    type: String,
    default: 'período anterior',
  },
})

const percentChange = computed(() => {
  if (props.previous === 0) {
    return props.current === 0 ? '0' : '∞'
  }
  const change = ((props.current - props.previous) / Math.abs(props.previous)) * 100
  return Math.abs(change).toFixed(0)
})

const isPositive = computed(() => props.current > props.previous)

const arrow = computed(() => (isPositive.value ? '↑' : '↓'))

const isGood = computed(() => {
  const positive = isPositive.value
  return props.isPositiveGood ? positive : !positive
})

const badgeClass = computed(() => {
  if (isGood.value) {
    return 'bg-green-100 text-green-800'
  }
  return 'bg-red-100 text-red-800'
})
</script>
