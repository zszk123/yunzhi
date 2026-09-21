import { Result } from 'antd'

/** 迭代 1 占位：登录 mock 后的跳转目标。真正的 Agent 创建页在迭代 5 接入。 */
export default function AgentsPlaceholder() {
  return (
    <Result
      status="success"
      title="登录成功（mock）"
      subTitle="这里是 Agent 创建页占位 —— 真实页面将在迭代 5 接入（见 docs/开发计划.md 任务 5.3）"
    />
  )
}
