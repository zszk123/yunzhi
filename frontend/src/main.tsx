import { App as AntdApp, ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import 'antd/dist/reset.css'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'

import App from './App'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {/* 主题色对齐 Pixso 设计稿变量 Color/Primary #2563EB */}
    <ConfigProvider locale={zhCN} theme={{ token: { colorPrimary: '#2563EB' } }}>
      <AntdApp>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </AntdApp>
    </ConfigProvider>
  </StrictMode>,
)
