/**
 * 站点初始化接口封装（PRD A16 / backend routers/admin_init）。
 */

import { api } from './client'
import type { User } from './types'

export interface InitStatus {
  initialized: boolean
  email_verify_enabled: boolean
  has_site_icon: boolean
}

export interface InitPayload {
  username: string
  email: string
  password: string
  site_icon_base64?: string
  email_verify_enabled: boolean
  smtp_host?: string
  smtp_port?: number
  smtp_user?: string
  smtp_password?: string
}

/** 查询初始化状态（无鉴权；initialized 由后端按 admin 是否存在推导）。 */
export async function getInitStatus(): Promise<InitStatus> {
  const { data } = await api.get<InitStatus>('/admin/init/status')
  return data
}

/** 执行初始化：创建博主账户 + 站点配置（仅未初始化时可调用，否则 409）。 */
export async function initialize(payload: InitPayload): Promise<{ message: string; admin: User }> {
  const { data } = await api.post<{ message: string; admin: User }>('/admin/init', payload)
  return data
}
