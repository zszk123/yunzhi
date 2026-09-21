import { Navigate, Route, Routes } from 'react-router-dom'

import LoginPage from './pages/login/LoginPage'
import AgentsPlaceholder from './pages/agents/AgentsPlaceholder'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      {/* 登录成功后的落地页：Agent 创建页在迭代 5 接入，先占位 */}
      <Route path="/agents" element={<AgentsPlaceholder />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}
