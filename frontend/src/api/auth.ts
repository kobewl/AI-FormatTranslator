/**
 * 认证相关 API
 */
import { http } from './index'

export interface LoginRequest {
  username: string
  password: string
  user_type?: 'customer' | 'admin'
}

export interface RegisterRequest {
  username: string
  password: string
  email?: string
  phone?: string
}

export interface UserInfo {
  id: number
  username: string
  email?: string
  phone?: string
  max_space: number
  used_space: number
  space_percent: number
  status: string
  vip_level: string
  created_at: string
  last_login_at?: string
}

export interface LoginResponse {
  token: string
  token_type: string
  user_type: string
  user: UserInfo
}

export interface ApiResponse<T> {
  success: boolean
  message: string
  data: T
}

/**
 * 用户登录
 */
export const login = (data: LoginRequest) => {
  return http.post<ApiResponse<LoginResponse>>('/auth/login', data)
}

/**
 * 用户注册
 */
export const register = (data: RegisterRequest) => {
  return http.post<ApiResponse<UserInfo>>('/auth/register', data)
}

/**
 * 获取当前用户信息
 */
export const getCurrentUser = () => {
  return http.get<ApiResponse<UserInfo>>('/auth/me')
}
