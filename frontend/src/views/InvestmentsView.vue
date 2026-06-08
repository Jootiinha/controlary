<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-3xl font-bold text-gray-900">Investimentos</h1>
      <button
        @click="showMessage"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
      >
        + Novo Investimento
      </button>
    </div>

    <div class="bg-white rounded-lg shadow p-6">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div class="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-6">
          <p class="text-gray-600 text-sm font-medium">Total Investido</p>
          <p class="text-3xl font-bold text-blue-600 mt-2">R$ 0,00</p>
        </div>
        <div class="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-6">
          <p class="text-gray-600 text-sm font-medium">Rendimento</p>
          <p class="text-3xl font-bold text-green-600 mt-2">R$ 0,00</p>
        </div>
        <div class="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-6">
          <p class="text-gray-600 text-sm font-medium">Valor Total</p>
          <p class="text-3xl font-bold text-purple-600 mt-2">R$ 0,00</p>
        </div>
      </div>

      <div class="text-center py-8 text-gray-500">
        <p>Nenhum investimento registrado</p>
        <p class="text-sm mt-2">Registre seus investimentos para acompanhar o desempenho</p>
      </div>
    </div>

    <Alert
      ref="alertRef"
      type="info"
      title="Funcionalidade em desenvolvimento"
      message="O módulo de investimentos estará disponível em breve"
      :duration="3000"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Alert from '@/components/Alert.vue'

const alertRef = ref(null)

const showMessage = () => {
  alertRef.value?.show()
}
</script>
