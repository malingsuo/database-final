<script setup lang="ts">
import { Check, Brush } from '@element-plus/icons-vue'
import { themeOptions, useThemeStore, type ThemeName } from '@/stores/theme'

const theme = useThemeStore()

function selectTheme(name: ThemeName) {
  theme.applyTheme(name)
}
</script>

<template>
  <el-popover placement="top-end" trigger="click" :width="220" popper-class="theme-popover">
    <template #reference>
      <el-button
        circle
        size="large"
        class="theme-trigger"
        :aria-label="`切換頁面顏色，目前為${theme.activeOption.label}`"
      >
        <el-icon><Brush /></el-icon>
      </el-button>
    </template>

    <div class="theme-panel">
      <div class="theme-title">頁面顏色</div>
      <button
        v-for="option in themeOptions"
        :key="option.name"
        type="button"
        class="theme-option"
        :class="{ active: option.name === theme.current }"
        @click="selectTheme(option.name)"
      >
        <span class="swatch" :style="{ backgroundColor: option.color }" />
        <span>{{ option.label }}</span>
        <el-icon v-if="option.name === theme.current" class="check-icon"><Check /></el-icon>
      </button>
    </div>
  </el-popover>
</template>

<style scoped>
.theme-trigger {
  position: fixed;
  right: 22px;
  bottom: 22px;
  z-index: 30;
  color: #fff;
  border: none;
  background: var(--app-primary);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.18);
}

.theme-trigger:hover,
.theme-trigger:focus {
  color: #fff;
  background: var(--app-primary-dark);
}

.theme-panel {
  display: grid;
  gap: 8px;
}

.theme-title {
  padding: 0 2px 4px;
  color: var(--app-text-muted);
  font-size: 13px;
  font-weight: 600;
}

.theme-option {
  width: 100%;
  min-height: 38px;
  display: grid;
  grid-template-columns: 18px 1fr 18px;
  gap: 10px;
  align-items: center;
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
  color: var(--app-text);
  cursor: pointer;
  font: inherit;
  padding: 8px 10px;
  text-align: left;
}

.theme-option:hover,
.theme-option.active {
  border-color: var(--app-primary-soft);
  background: var(--app-primary-tint);
}

.swatch {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  box-shadow: inset 0 0 0 1px rgba(15, 23, 42, 0.12);
}

.check-icon {
  color: var(--app-primary);
}
</style>
