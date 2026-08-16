<script setup>
import { ref } from 'vue'

const inputMessage = ref('')
const localMessages = ref([])

function sendLocalMessage() {
  const content = inputMessage.value.trim()

  if (!content) {
    return
  }

  localMessages.value.push({
    id: Date.now(),
    role: 'user',
    content: content,
  })

  inputMessage.value = ''
}

function handleEnter(event) {
  if (event.shiftKey) {
    return
  }

  event.preventDefault()
  sendLocalMessage()
}
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div>
        <div class="brand">
          <div class="brand-icon">M</div>

          <div>
            <h1>MaintAI</h1>
            <p>工业设备智能运维助手</p>
          </div>
        </div>

        <button class="new-chat-button">
          <span>＋</span>
          新建对话
        </button>

        <div class="sidebar-section">
          <p class="section-title">最近对话</p>

          <button class="session-item active">
            <span class="session-icon">▣</span>

            <span class="session-text">
              <strong>设备故障诊断</strong>
              <small>ATV320 变频器故障排查</small>
            </span>
          </button>
        </div>
      </div>

      <div class="sidebar-footer">
        <button class="knowledge-button">
          <span>▤</span>
          知识库管理
        </button>

        <div class="user-card">
          <div class="avatar">A</div>

          <div>
            <strong>当前用户</strong>
            <small>用户 ID：1</small>
          </div>
        </div>
      </div>
    </aside>

    <main class="chat-panel">
      <header class="chat-header">
        <div>
          <h2>设备故障诊断</h2>
          <p>结合设备手册与知识库进行分析</p>
        </div>

        <div class="service-status">
          <span class="status-dot"></span>
          服务已连接
        </div>
      </header>

      <section class="message-area">
        <div v-if="localMessages.length === 0" class="welcome-card">
          <div class="welcome-icon">AI</div>

          <h2>你好，我是 MaintAI</h2>

          <p>
            我可以结合工业设备手册和知识库，协助你进行故障诊断、维护建议和操作说明查询。
          </p>

          <div class="example-grid">
            <button>ATV320 出现 OCF 故障是什么意思？</button>
            <button>电机温度过高应该检查哪些项目？</button>
            <button>如何查询设备说明书中的参数？</button>
          </div>
        </div>

        <div
          v-for="item in localMessages"
          :key="item.id"
          class="message-row user-message"
        >
          <div class="message-bubble">
            {{ item.content }}
          </div>

          <div class="message-avatar">我</div>
        </div>
      </section>

      <footer class="input-area">
        <div class="input-box">
          <textarea
            v-model="inputMessage"
            placeholder="请输入设备故障、型号或维护问题……"
            rows="1"
            @keydown.enter="handleEnter"
          ></textarea>

          <button
            class="send-button"
            :disabled="!inputMessage.trim()"
            @click="sendLocalMessage"
          >
            ↑
          </button>
        </div>

        <p class="input-hint">
          当前仅测试前端页面交互，下一步接入 FastAPI 和真实 Agent。
        </p>
      </footer>
    </main>
  </div>
</template>