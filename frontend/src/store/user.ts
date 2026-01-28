/**
 * 用户状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, register as registerApi, getCurrentUser, type UserInfo } from '@/api/auth'
import { message } from 'ant-design-vue'
import router from '@/router'

export const useUserStore = defineStore('user', () => {
  // 状态
  const token = ref<string>(localStorage.getItem('token') || '')
  const userInfo = ref<UserInfo | null>(null)

  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => userInfo.value?.username || '')
  const spacePercent = computed(() => userInfo.value?.space_percent || 0)

  /**
   * 登录
   */
  const login = async (username: string, password: string) => {
    try {
      const res = await loginApi({ username, password, user_type: 'customer' })

      // 后端返回格式：{ success: true, data: { token: "...", user: {...} } }
      token.value = res.data.token
      userInfo.value = res.data.user

      // 保存 token 到 localStorage
      localStorage.setItem('token', res.data.token)

      message.success('登录成功')

      // 跳转到首页
      router.push('/')
    } catch (error) {
      console.error('登录失败:', error)
      throw error
    }
  }

  /**
   * 注册
   */
  const register = async (username: string, password: string, email?: string, phone?: string) => {
    try {
      const res = await registerApi({ username, password, email, phone })
      message.success('注册成功，请登录')
      return res.data
    } catch (error) {
      console.error('注册失败:', error)
      throw error
    }
  }

  /**
   * 获取用户信息
   */
  const fetchUserInfo = async () => {
    try {
      const res = await getCurrentUser()
      userInfo.value = res.data
    } catch (error: any) {
      console.error('获取用户信息失败:', error)
      // 只有在认证失败（401）时才清除登录状态
      if (error.response?.status === 401) {
        logout()
      } else {
        // 其他错误不清除登录状态，只是更新失败
        throw error
      }
    }
  }

  /**
   * 登出
   */
  const logout = () => {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
    router.push('/login')
    message.success('已登出')
  }

  /**
   * 设置 Token
   */
  const setToken = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  /**
   * 设置用户信息
   */
  const setUserInfo = (info: UserInfo) => {
    userInfo.value = info
  }

  return {
    // 状态
    token,
    userInfo,
    // 计算属性
    isLoggedIn,
    username,
    spacePercent,
    // 方法
    login,
    register,
    fetchUserInfo,
    logout,
    setToken,
    setUserInfo
  }
})
