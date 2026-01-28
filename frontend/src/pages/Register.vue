<template>
  <div class="register-container">
    <div class="register-box">
      <div class="register-header">
        <h1>注册账号</h1>
        <p>加入 DocTranslator，开始智能翻译之旅</p>
      </div>

      <a-form
        :model="formData"
        @finish="handleRegister"
        autocomplete="off"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 18 }"
      >
        <a-form-item label="用户名" name="username" :rules="[
          { required: true, message: '请输入用户名' },
          { min: 3, message: '用户名至少3个字符' }
        ]">
          <a-input
            v-model:value="formData.username"
            placeholder="请输入用户名"
          />
        </a-form-item>

        <a-form-item label="密码" name="password" :rules="[
          { required: true, message: '请输入密码' },
          { min: 6, message: '密码至少6个字符' }
        ]">
          <a-input-password
            v-model:value="formData.password"
            placeholder="请输入密码"
          />
        </a-form-item>

        <a-form-item label="确认密码" name="confirmPassword" :rules="[
          { required: true, message: '请确认密码' },
          { validator: validatePassword }
        ]">
          <a-input-password
            v-model:value="formData.confirmPassword"
            placeholder="请再次输入密码"
          />
        </a-form-item>

        <a-form-item label="邮箱" name="email">
          <a-input
            v-model:value="formData.email"
            placeholder="请输入邮箱（可选）"
          />
        </a-form-item>

        <a-form-item label="手机号" name="phone">
          <a-input
            v-model:value="formData.phone"
            placeholder="请输入手机号（可选）"
          />
        </a-form-item>

        <a-form-item :wrapper-col="{ offset: 6, span: 18 }">
          <a-button
            type="primary"
            html-type="submit"
            size="large"
            block
            :loading="loading"
          >
            注册
          </a-button>
        </a-form-item>

        <div class="register-footer" :wrapper-col="{ offset: 6, span: 18 }">
          已有账号？<router-link to="/login">立即登录</router-link>
        </div>
      </a-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store'

const router = useRouter()
const userStore = useUserStore()

const formData = ref({
  username: '',
  password: '',
  confirmPassword: '',
  email: '',
  phone: ''
})

const loading = ref(false)

// 验证密码
const validatePassword = (_rule: any, value: string) => {
  if (value !== formData.value.password) {
    return Promise.reject('两次输入的密码不一致')
  }
  return Promise.resolve()
}

// 注册
const handleRegister = async () => {
  loading.value = true
  try {
    await userStore.register(
      formData.value.username,
      formData.value.password,
      formData.value.email || undefined,
      formData.value.phone || undefined
    )
    // 注册成功后跳转到登录页
    setTimeout(() => {
      router.push('/login')
    }, 1500)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.register-box {
  width: 500px;
  padding: 40px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
}

.register-header {
  text-align: center;
  margin-bottom: 32px;
}

.register-header h1 {
  font-size: 28px;
  color: #1f2937;
  margin-bottom: 8px;
}

.register-header p {
  color: #6b7280;
  font-size: 14px;
}

.register-footer {
  text-align: center;
  margin-top: 24px;
  color: #6b7280;
}

.register-footer a {
  color: #667eea;
  text-decoration: none;
}

.register-footer a:hover {
  text-decoration: underline;
}
</style>
