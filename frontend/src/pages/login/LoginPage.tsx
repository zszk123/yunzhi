import { LockOutlined, MailOutlined, SafetyCertificateOutlined } from '@ant-design/icons'
import { App, Button, Checkbox, Divider, Form, Input } from 'antd'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import './LoginPage.css'

interface LoginFormValues {
  email: string
  password: string
  agreement: boolean
}

/**
 * 登录页静态版（对齐 Pixso 设计稿 10:1127：居中卡片 420px，Logo/邮箱/密码/SSO/协议）。
 * 迭代 1 只做视觉与表单校验，提交走 mock；真实认证（JWT）在迭代 4 接入。
 */
export default function LoginPage() {
  const { message } = App.useApp()
  const navigate = useNavigate()
  const [form] = Form.useForm<LoginFormValues>()
  const [submitting, setSubmitting] = useState(false)

  const onFinish = (values: LoginFormValues) => {
    if (!values.agreement) {
      message.warning('请先阅读并勾选用户协议与隐私政策')
      return
    }
    setSubmitting(true)
    // mock：不接后端，打印并跳转占位页
    console.log('[mock login]', values)
    window.setTimeout(() => {
      message.success('登录成功（mock）')
      navigate('/agents')
    }, 300)
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-brand">
          <div className="login-logo">云</div>
          <div className="login-brand-text">
            <div className="login-title">云知 yunzhi</div>
            <div className="login-subtitle">知识库 + LangGraph Agent 平台</div>
          </div>
        </div>

        <Form<LoginFormValues>
          form={form}
          layout="vertical"
          requiredMark={false}
          onFinish={onFinish}
          initialValues={{ agreement: false }}
        >
          <Form.Item
            name="email"
            label="邮箱"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '邮箱格式不正确' },
            ]}
          >
            <Input size="large" prefix={<MailOutlined />} placeholder="name@example.com" />
          </Form.Item>

          <Form.Item
            name="password"
            label="密码"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password size="large" prefix={<LockOutlined />} placeholder="请输入密码" />
          </Form.Item>

          <Form.Item name="agreement" valuePropName="checked" className="login-agreement">
            <Checkbox>
              我已阅读并同意<a>《用户协议》</a>与<a>《隐私政策》</a>
            </Checkbox>
          </Form.Item>

          <Form.Item className="login-submit">
            <Button type="primary" htmlType="submit" size="large" block loading={submitting}>
              登 录
            </Button>
          </Form.Item>
        </Form>

        <Divider plain className="login-divider">
          其他登录方式
        </Divider>
        <Button size="large" block icon={<SafetyCertificateOutlined />}>
          SSO 单点登录
        </Button>
      </div>
    </div>
  )
}
