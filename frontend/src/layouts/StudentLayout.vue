<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { DataLine, List, UploadFilled, SwitchButton } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useCheckStore } from '@/stores/check'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const check = useCheckStore()

const activeMenu = computed(() => route.name as string)
const displayName = computed(() => auth.user?.account ?? '使用者')

async function handleLogout() {
  try {
    await ElMessageBox.confirm('確定要登出嗎？', '登出', {
      confirmButtonText: '登出',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  await auth.logout()
  check.reset()
  router.replace({ name: 'login' })
}
</script>

<template>
  <el-container class="layout">
    <el-aside width="236px" class="aside">
      <div class="brand">
        <div class="brand-icon">
          <el-icon :size="21"><DataLine /></el-icon>
        </div>
        <div>
          <span class="brand-text">畢業學分審核</span>
          <span class="brand-sub">Credit Compass</span>
        </div>
      </div>
      <el-menu :default-active="activeMenu" router class="menu">
        <el-menu-item index="overview" :route="{ name: 'overview' }">
          <el-icon><DataLine /></el-icon>
          <span>進度總覽</span>
        </el-menu-item>
        <el-menu-item index="inventory" :route="{ name: 'inventory' }">
          <el-icon><List /></el-icon>
          <span>學分盤點</span>
        </el-menu-item>
        <el-menu-item index="upload" :route="{ name: 'upload' }">
          <el-icon><UploadFilled /></el-icon>
          <span>上傳資料</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div>
          <div class="header-title">學生畢業學分審核器</div>
          <div class="header-subtitle">追蹤學分、缺修與畢業狀態</div>
        </div>
        <div class="header-right">
          <el-tag class="role-tag" type="info" effect="plain">學生</el-tag>
          <span class="account">{{ displayName }}</span>
          <el-button text :icon="SwitchButton" @click="handleLogout">登出</el-button>
        </div>
      </el-header>

      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout {
  height: 100vh;
  background: transparent;
}

.aside {
  margin: 14px 0 14px 14px;
  border: 1px solid color-mix(in srgb, var(--app-border) 78%, transparent);
  border-radius: 8px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.88), rgba(255, 255, 255, 0.66)),
    var(--app-surface);
  box-shadow: var(--app-shadow);
  backdrop-filter: blur(18px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.brand {
  min-height: 76px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 18px;
  color: var(--app-text-strong);
  border-bottom: 1px solid color-mix(in srgb, var(--app-border) 72%, transparent);
}

.brand-icon {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  color: #fff;
  background:
    linear-gradient(135deg, var(--app-primary), var(--app-accent));
  box-shadow: 0 12px 26px color-mix(in srgb, var(--app-primary) 28%, transparent);
}

.brand-text {
  display: block;
  font-size: 16px;
  font-weight: 800;
}

.brand-sub {
  display: block;
  margin-top: 2px;
  color: var(--app-text-muted);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

.menu {
  padding: 12px;
  border-right: none;
  flex: 1;
  background: transparent;
}

.menu :deep(.el-menu-item) {
  height: 44px;
  margin-bottom: 8px;
  border-radius: 8px;
  color: var(--app-text);
  font-weight: 650;
}

.menu :deep(.el-menu-item:hover) {
  background: color-mix(in srgb, var(--app-primary-tint) 82%, white);
}

.menu :deep(.el-menu-item.is-active) {
  color: var(--app-primary);
  background:
    linear-gradient(90deg, color-mix(in srgb, var(--app-primary) 14%, white), rgba(255, 255, 255, 0.76));
  box-shadow: inset 3px 0 0 var(--app-primary);
}

.header {
  height: 76px;
  margin: 14px 14px 0;
  border: 1px solid color-mix(in srgb, var(--app-border) 78%, transparent);
  border-radius: 8px;
  background: var(--app-surface-glass);
  box-shadow: var(--app-shadow-soft);
  backdrop-filter: blur(18px);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-title {
  font-size: 18px;
  font-weight: 800;
  color: var(--app-text-strong);
}

.header-subtitle {
  margin-top: 3px;
  color: var(--app-text-muted);
  font-size: 13px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.account {
  font-weight: 500;
}

.role-tag {
  border-color: color-mix(in srgb, var(--app-primary) 26%, transparent);
  color: var(--app-primary);
  background: color-mix(in srgb, var(--app-primary-tint) 76%, white);
}

.main {
  padding: 20px 14px 28px 20px;
  overflow-y: auto;
  background: transparent;
}

@media (max-width: 820px) {
  .layout {
    height: auto;
    min-height: 100vh;
    display: block;
  }

  .aside {
    width: auto !important;
    margin: 10px;
  }

  .menu {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
  }

  .menu :deep(.el-menu-item) {
    margin: 0;
  }

  .header {
    height: auto;
    min-height: 72px;
    margin: 10px;
    padding: 12px 14px;
  }

  .header-right {
    flex-wrap: wrap;
    justify-content: flex-end;
  }

  .main {
    padding: 10px;
  }
}
</style>
