<template>
  <div class="mb-4">
    <label v-if="label" class="block text-sm font-medium text-gray-700 mb-1">
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>
    <select
      v-if="type === 'select'"
      v-model="localValue"
      @input="$emit('update:modelValue', localValue)"
      :required="required"
      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
    >
      <option value="">{{ placeholder || 'Selecione...' }}</option>
      <option v-for="opt in options" :key="opt.id || opt.value" :value="opt.id || opt.value">
        {{ opt.name || opt.label }}
      </option>
    </select>
    <textarea
      v-else-if="type === 'textarea'"
      v-model="localValue"
      @input="$emit('update:modelValue', localValue)"
      :placeholder="placeholder"
      :required="required"
      rows="4"
      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
    ></textarea>
    <input
      v-else
      v-model="localValue"
      @input="$emit('update:modelValue', localValue)"
      :type="type"
      :placeholder="placeholder"
      :required="required"
      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
    />
    <p v-if="error" class="text-red-500 text-sm mt-1">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  label: String,
  type: {
    type: String,
    default: 'text',
  },
  modelValue: {
    required: true,
  },
  placeholder: String,
  required: Boolean,
  error: String,
  options: Array,
})

defineEmits(['update:modelValue'])

const localValue = ref(props.modelValue)

watch(
  () => props.modelValue,
  (newVal) => {
    localValue.value = newVal
  }
)
</script>
