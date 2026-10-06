import { useParams } from 'react-router-dom'

export function PostDetailPage() {
  const { id } = useParams<{ id: string }>()
  return <div className="page">动态详情 #{id}（单元 12 实现）</div>
}
