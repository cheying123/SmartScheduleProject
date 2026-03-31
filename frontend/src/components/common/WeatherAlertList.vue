<script setup>
import { Umbrella, Sun, Snowflake, Wind, Droplet, AlertTriangle, AlertCircle, CheckCircle, Leaf, Smile, Thermometer, Cloud, CloudRain, CloudLightning, ChevronDown, ChevronUp } from 'lucide-vue-next'
import { ref, computed } from 'vue'

const props = defineProps({
  alerts: {
    type: Array,
    default: () => []
  },
  compact: {
    type: Boolean,
    default: false
  },
  maxVisible: {
    type: Number,
    default: 1
  }
})

const isExpanded = ref(false)

const visibleAlerts = computed(() => {
  if (isExpanded.value) {
    return props.alerts
  }
  return props.alerts.slice(0, props.maxVisible)
})

const hasMore = computed(() => {
  return props.alerts.length > props.maxVisible
})

function toggleExpand() {
  isExpanded.value = !isExpanded.value
}

const iconMap = {
  umbrella: Umbrella,
  sun: Sun,
  snowflake: Snowflake,
  wind: Wind,
  droplet: Droplet,
  'alert-triangle': AlertTriangle,
  'alert-circle': AlertCircle,
  'check-circle': CheckCircle,
  leaf: Leaf,
  smile: Smile,
  thermometer: Thermometer,
  cloud: Cloud,
  thunderstorm: CloudLightning,
  rain: CloudRain,
  storm: CloudLightning,
  mask: AlertCircle,
  'alert-octagon': AlertCircle
}

const priorityStyles = {
  high: {
    bg: 'bg-red-50 border-red-500 text-red-700',
    icon: 'text-red-600'
  },
  medium: {
    bg: 'bg-yellow-50 border-yellow-500 text-yellow-700',
    icon: 'text-yellow-600'
  },
  low: {
    bg: 'bg-green-50 border-green-500 text-green-700',
    icon: 'text-green-600'
  }
}

function getIconComponent(iconName) {
  return iconMap[iconName] || Cloud
}
</script>

<template>
  <div v-if="alerts && alerts.length > 0" class="weather-alerts-container">
    <div 
      v-for="(alert, index) in visibleAlerts" 
      :key="index"
      class="weather-alert-item"
      :class="[
        priorityStyles[alert.priority]?.bg || 'bg-gray-50',
        { 'compact': compact }
      ]"
    >
      <component 
        :is="getIconComponent(alert.icon)" 
        :size="compact ? 16 : 20"
        :class="priorityStyles[alert.priority]?.icon || 'text-gray-600'"
      />
      <span class="alert-message">{{ alert.message }}</span>
    </div>
    
    <button 
      v-if="hasMore"
      class="expand-btn"
      @click="toggleExpand"
    >
      <ChevronDown v-if="!isExpanded" :size="16" />
      <ChevronUp v-else :size="16" />
      <span>{{ isExpanded ? '收起' : `还有${alerts.length - maxVisible}条提醒` }}</span>
    </button>
  </div>
</template>

<style scoped>
.weather-alerts-container {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 0.75rem;
}

.weather-alert-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.9rem;
  line-height: 1.5;
  transition: all 0.3s ease;
}

.weather-alert-item:hover {
  transform: translateX(4px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.weather-alert-item.compact {
  padding: 0.5rem 0.75rem;
  font-size: 0.85rem;
}

.alert-message {
  flex: 1;
  color: inherit;
}

.expand-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  width: 100%;
  padding: 0.5rem 0.75rem;
  background-color: #f8f9fa;
  border: 1px dashed #dee2e6;
  border-radius: 8px;
  color: #6c757d;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
}

.expand-btn:hover {
  background-color: #e9ecef;
  color: #495057;
}

.expand-btn span {
  font-weight: 500;
}
</style>