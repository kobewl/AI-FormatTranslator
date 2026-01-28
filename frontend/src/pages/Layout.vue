<template>
  <a-layout class="layout-container">
    <!-- 顶部导航栏 -->
    <a-layout-header class="layout-header">
      <div class="header-content">
        <div class="logo">
          <router-link to="/">
            <FileTextOutlined style="font-size: 24px;" />
            <span class="logo-text">DocTranslator</span>
          </router-link>
        </div>

        <a-menu
          v-model:selectedKeys="selectedKeys"
          mode="horizontal"
          class="header-menu"
        >
          <a-menu-item key="1" @click="$router.push('/')">
            <TranslationOutlined />
            翻译
          </a-menu-item>
          <a-menu-item key="2" @click="$router.push('/history')">
            <HistoryOutlined />
            历史记录
          </a-menu-item>
        </a-menu>

        <div class="header-right">
          <!-- 存储空间显示 -->
          <a-popover placement="bottomRight">
            <template #content>
              <div class="storage-info">
                <p>已使用：{{ formatSize(userStore.userInfo?.used_space || 0) }}</p>
                <p>总空间：{{ formatSize(userStore.userInfo?.max_space || 0) }}</p>
                <a-progress :percent="userStore.spacePercent" size="small" />
              </div>
            </template>
            <a-button type="text" class="storage-btn">
              <CloudServerOutlined />
              {{ userStore.spacePercent }}%
            </a-button>
          </a-popover>

          <!-- 用户菜单 -->
          <a-dropdown>
            <a-button type="text" class="user-btn">
              <UserOutlined />
              {{ userStore.username }}
              <DownOutlined />
            </a-button>
            <template #overlay>
              <a-menu>
                <a-menu-item @click="$router.push('/prompts')">
                  <BulbOutlined />
                  提示词管理
                </a-menu-item>
                <a-menu-item @click="$router.push('/comparisons')">
                  <BookOutlined />
                  术语对照表
                </a-menu-item>
                <a-menu-divider />
                <a-menu-item @click="handleLogout">
                  <LogoutOutlined />
                  退出登录
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </div>
    </a-layout-header>

    <!-- 主要内容区域 -->
    <a-layout-content class="layout-content">
      <router-view />
    </a-layout-content>

    <!-- 页脚 -->
    <a-layout-footer class="layout-footer">
      <div class="footer-content">
        <p>DocTranslator © 2024 - 基于 AI 的智能文档翻译系统</p>
      </div>
    </a-layout-footer>
  </a-layout>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  FileTextOutlined,
  TranslationOutlined,
  HistoryOutlined,
  UserOutlined,
  DownOutlined,
  LogoutOutlined,
  CloudServerOutlined,
  BulbOutlined,
  BookOutlined
} from '@ant-design/icons-vue'
import { useUserStore } from '@/store'
import { Modal } from 'ant-design-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const selectedKeys = ref<string[]>([])

// 根据路由更新选中菜单
watch(
  () => route.path,
  (path) => {
    if (path === '/') {
      selectedKeys.value = ['1']
    } else if (path === '/history') {
      selectedKeys.value = ['2']
    } else {
      selectedKeys.value = []
    }
  },
  { immediate: true }
)

// 格式化文件大小
const formatSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

// 退出登录
const handleLogout = () => {
  Modal.confirm({
    title: '确认退出',
    content: '您确定要退出登录吗？',
    onOk: () => {
      userStore.logout()
    }
  })
}

// 初始化用户信息
onMounted(async () => {
  // 只有在没有用户信息时才获取
  if (userStore.isLoggedIn && !userStore.userInfo) {
    try {
      await userStore.fetchUserInfo()
    } catch (error) {
      // 如果获取失败，不强制登出，可能是因为已经有用户信息了
      console.error('获取用户信息失败，但不影响使用:', error)
    }
  }
})
</script>

<style scoped>
.layout-container {
  min-height: 100vh;
}

.layout-header {
  background: #fff;
  padding: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  position: sticky;
  top: 0;
  z-index: 999;
}

.header-content {
  display: flex;
  align-items: center;
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
}

.logo {
  display: flex;
  align-items: center;
  margin-right: 48px;
}

.logo a {
  display: flex;
  align-items: center;
  text-decoration: none;
  color: #1890ff;
  font-size: 20px;
  font-weight: 600;
}

.logo-text {
  margin-left: 8px;
}

.header-menu {
  flex: 1;
  border: none;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.storage-btn,
.user-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 40px;
  padding: 0 16px;
  border-radius: 4px;
  transition: all 0.3s;
}

.storage-btn:hover,
.user-btn:hover {
  background: #f0f0f0;
}

.storage-info {
  min-width: 200px;
}

.storage-info p {
  margin: 4px 0;
}

.layout-content {
  background: #f0f2f5;
  min-height: calc(100vh - 128px);
  padding: 24px;
}

.layout-footer {
  text-align: center;
  background: #fff;
  border-top: 1px solid #f0f0f0;
}

.footer-content p {
  margin: 0;
  color: #8c8c8c;
}
</style>
