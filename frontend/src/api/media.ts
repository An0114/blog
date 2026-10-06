/**
 * 媒体上传接口封装（对应 backend routers/media）。
 */

import { api } from './client'
import type { MediaOut, MediaType } from './types'

/** 上传图片/视频，返回媒体记录（仅博主可调用，后端 403 拦截）。 */
export async function uploadMedia(file: File, type: MediaType): Promise<MediaOut> {
  const form = new FormData()
  form.append('type', type)
  form.append('file', file)
  const { data } = await api.post<MediaOut>('/upload', form)
  return data
}
