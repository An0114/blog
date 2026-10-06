/**
 * 媒体上传接口封装（对应 backend routers/media）。
 */

import { api } from './client'
import type { MediaOut, MediaType } from './types'

/** 上传图片/视频，返回媒体记录（仅博主可调用，后端 403 拦截）。
 *  onProgress 每帧回调 0-100 的实时进度百分比（三期功能，PRD A12）。 */
export async function uploadMedia(
  file: File,
  type: MediaType,
  onProgress?: (percent: number) => void,
): Promise<MediaOut> {
  const form = new FormData()
  form.append('type', type)
  form.append('file', file)
  const { data } = await api.post<MediaOut>('/upload', form, {
    onUploadProgress: (event) => {
      if (!onProgress) return
      const total = event.total ?? 0
      const percent = total > 0 ? Math.min(100, Math.round((event.loaded / total) * 100)) : 0
      onProgress(percent)
    },
  })
  return data
}
