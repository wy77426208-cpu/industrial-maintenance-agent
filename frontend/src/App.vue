<script setup>
import {
  computed,
  nextTick,
  onMounted,
  ref,
} from 'vue'

import {
  createChatSession,
  deleteChatSession,
  getChatMessages,
  getChatSessions,
  sendChatMessage,
  updateChatSessionTitle,
} from './api/chat'

import {
  deleteKnowledgeFile,
  getKnowledgeFiles,
  uploadKnowledgeFile,
} from './api/knowledge'

const USER_ID = 1

const activePage = ref('chat')

const sessions = ref([])
const messages = ref([])
const currentSessionId = ref(null)

const inputMessage = ref('')
const errorMessage = ref('')

const isBackendOnline = ref(false)
const isLoadingSessions = ref(false)
const isLoadingMessages = ref(false)
const isCreatingSession = ref(false)
const isSending = ref(false)
const deletingSessionId = ref(null)

const messageContainer = ref(null)
const messageInput = ref(null)
const titleInput = ref(null)

const isEditingTitle = ref(false)
const titleDraft = ref('')

const knowledgeFiles = ref([])
const selectedFile = ref(null)
const fileInput = ref(null)

const isLoadingKnowledge = ref(false)
const isUploadingFile = ref(false)
const deletingFileId = ref(null)

const knowledgeMessage = ref('')
const knowledgeMessageType = ref('success')
const knowledgeLoaded = ref(false)

const currentSession = computed(() => {
  return (
    sessions.value.find(
      (session) => session.id === currentSessionId.value,
    ) || null
  )
})

const isCurrentSessionEmpty = computed(() => {
  return Boolean(
    currentSession.value &&
      !isLoadingMessages.value &&
      messages.value.length === 0,
  )
})

const newSessionDisabled = computed(() => {
  return (
    isCreatingSession.value ||
    isLoadingMessages.value ||
    isSending.value ||
    isCurrentSessionEmpty.value
  )
})

function sortSessions(sessionList) {
  return [...sessionList].sort((left, right) => {
    const leftTime = Date.parse(
      left.updated_at || left.created_at || '',
    )

    const rightTime = Date.parse(
      right.updated_at || right.created_at || '',
    )

    return (rightTime || 0) - (leftTime || 0)
  })
}

function replaceSession(updatedSession) {
  const index = sessions.value.findIndex(
    (session) => session.id === updatedSession.id,
  )

  if (index === -1) {
    sessions.value = sortSessions([
      updatedSession,
      ...sessions.value,
    ])
    return
  }

  const newSessions = [...sessions.value]
  newSessions[index] = updatedSession
  sessions.value = sortSessions(newSessions)
}

function formatTime(value) {
  if (!value) {
    return ''
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return value
  }

  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')

  return `${year}-${month}-${day} ${hour}:${minute}`
}

function createAutomaticTitle(content) {
  const normalized = content.replace(/\s+/g, ' ').trim()
  const characters = [...normalized]
  const maximumLength = 22

  if (characters.length <= maximumLength) {
    return normalized
  }

  return `${characters.slice(0, maximumLength).join('')}...`
}

function shortFileId(fileId) {
  if (!fileId || fileId.length <= 16) {
    return fileId
  }

  return `${fileId.slice(0, 8)}...${fileId.slice(-6)}`
}

async function scrollToBottom() {
  await nextTick()

  if (messageContainer.value) {
    messageContainer.value.scrollTop =
      messageContainer.value.scrollHeight
  }
}

async function focusMessageInput() {
  await nextTick()
  messageInput.value?.focus()
}

async function checkBackend() {
  try {
    const response = await fetch(
      'http://127.0.0.1:8000/health',
    )

    isBackendOnline.value = response.ok
  } catch {
    isBackendOnline.value = false
  }
}

async function loadSessions() {
  isLoadingSessions.value = true
  errorMessage.value = ''

  try {
    const result = await getChatSessions(USER_ID)
    sessions.value = sortSessions(result)

    if (sessions.value.length === 0) {
      currentSessionId.value = null
      messages.value = []
      return
    }

    const selectedSession =
      sessions.value.find(
        (session) =>
          session.id === currentSessionId.value,
      ) || sessions.value[0]

    await selectSession(selectedSession)
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    isLoadingSessions.value = false
  }
}

async function selectSession(session) {
  if (isSending.value || !session) {
    return
  }

  activePage.value = 'chat'
  currentSessionId.value = session.id
  isEditingTitle.value = false
  errorMessage.value = ''
  isLoadingMessages.value = true

  const requestedSessionId = session.id

  try {
    const result = await getChatMessages(
      requestedSessionId,
      USER_ID,
    )

    if (currentSessionId.value === requestedSessionId) {
      messages.value = result
      await scrollToBottom()
    }
  } catch (error) {
    if (currentSessionId.value === requestedSessionId) {
      messages.value = []
      errorMessage.value = error.message
    }
  } finally {
    if (currentSessionId.value === requestedSessionId) {
      isLoadingMessages.value = false
    }
  }
}

async function createAndSelectSession() {
  isCreatingSession.value = true
  errorMessage.value = ''

  try {
    const session = await createChatSession(
      USER_ID,
      '新对话',
    )

    sessions.value = sortSessions([
      session,
      ...sessions.value,
    ])

    currentSessionId.value = session.id
    messages.value = []
    activePage.value = 'chat'

    await focusMessageInput()

    return session
  } catch (error) {
    errorMessage.value = error.message
    return null
  } finally {
    isCreatingSession.value = false
  }
}

async function handleNewSession() {
  if (newSessionDisabled.value) {
    await focusMessageInput()
    return
  }

  await createAndSelectSession()
}

async function handleSendMessage() {
  const content = inputMessage.value.trim()

  if (!content || isSending.value) {
    return
  }

  errorMessage.value = ''

  let session = currentSession.value

  if (!session) {
    session = await createAndSelectSession()

    if (!session) {
      return
    }
  }

  const originalSession = session
  const temporaryId = `temporary-${Date.now()}`

  const temporaryMessage = {
    id: temporaryId,
    session_id: session.id,
    role: 'user',
    content,
    created_at: new Date().toISOString(),
  }

  inputMessage.value = ''
  messages.value.push(temporaryMessage)
  isSending.value = true

  await scrollToBottom()

  let chatResult = null

  try {
    chatResult = await sendChatMessage(
      session.id,
      USER_ID,
      content,
    )
  } catch (error) {
    messages.value = messages.value.filter(
      (message) => message.id !== temporaryId,
    )

    inputMessage.value = content
    errorMessage.value = error.message
    isSending.value = false

    await focusMessageInput()
    return
  }

  const temporaryIndex = messages.value.findIndex(
    (message) => message.id === temporaryId,
  )

  if (temporaryIndex !== -1) {
    messages.value.splice(
      temporaryIndex,
      1,
      chatResult.user_message,
    )
  } else {
    messages.value.push(chatResult.user_message)
  }

  messages.value.push(chatResult.assistant_message)

  const locallyUpdatedSession = {
    ...originalSession,
    updated_at:
      chatResult.assistant_message.created_at ||
      new Date().toISOString(),
  }

  replaceSession(locallyUpdatedSession)

  if (originalSession.title === '新对话') {
    const automaticTitle =
      createAutomaticTitle(content)

    try {
      const updatedSession =
        await updateChatSessionTitle(
          originalSession.id,
          USER_ID,
          automaticTitle,
        )

      replaceSession(updatedSession)
    } catch (error) {
      errorMessage.value =
        `回答已经生成，但自动更新标题失败：${error.message}`
    }
  }

  isSending.value = false
  await scrollToBottom()
  await focusMessageInput()
}

function handleInputKeydown(event) {
  if (event.shiftKey) {
    return
  }

  event.preventDefault()
  handleSendMessage()
}

function startTitleEdit() {
  if (!currentSession.value || isSending.value) {
    return
  }

  titleDraft.value = currentSession.value.title
  isEditingTitle.value = true

  nextTick(() => {
    titleInput.value?.focus()
    titleInput.value?.select()
  })
}

function cancelTitleEdit() {
  isEditingTitle.value = false
  titleDraft.value = ''
}

async function saveTitle() {
  if (!isEditingTitle.value || !currentSession.value) {
    return
  }

  const newTitle = titleDraft.value.trim()
  const session = currentSession.value

  if (!newTitle) {
    errorMessage.value = '会话标题不能为空'
    return
  }

  if (newTitle === session.title) {
    cancelTitleEdit()
    return
  }

  try {
    const updatedSession =
      await updateChatSessionTitle(
        session.id,
        USER_ID,
        newTitle,
      )

    replaceSession(updatedSession)
    cancelTitleEdit()
  } catch (error) {
    errorMessage.value = error.message
  }
}

async function handleDeleteSession(session) {
  if (
    !session ||
    isSending.value ||
    deletingSessionId.value !== null
  ) {
    return
  }

  const confirmed = window.confirm(
    `确定删除会话“${session.title}”吗？\n该会话中的聊天消息也会一起删除。`,
  )

  if (!confirmed) {
    return
  }

  deletingSessionId.value = session.id
  errorMessage.value = ''

  try {
    await deleteChatSession(session.id, USER_ID)

    sessions.value = sessions.value.filter(
      (item) => item.id !== session.id,
    )

    if (currentSessionId.value === session.id) {
      currentSessionId.value = null
      messages.value = []

      if (sessions.value.length > 0) {
        await selectSession(sessions.value[0])
      }
    }
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    deletingSessionId.value = null
  }
}

async function openKnowledgePage() {
  activePage.value = 'knowledge'
  errorMessage.value = ''

  if (!knowledgeLoaded.value) {
    await loadKnowledgeFiles()
  }
}

function openChatPage() {
  activePage.value = 'chat'
}

async function loadKnowledgeFiles() {
  isLoadingKnowledge.value = true
  knowledgeMessage.value = ''

  try {
    knowledgeFiles.value =
      await getKnowledgeFiles()

    knowledgeLoaded.value = true
  } catch (error) {
    knowledgeMessageType.value = 'error'
    knowledgeMessage.value = error.message
  } finally {
    isLoadingKnowledge.value = false
  }
}

function openFileSelector() {
  if (!isUploadingFile.value) {
    fileInput.value?.click()
  }
}

function handleFileSelected(event) {
  selectedFile.value = event.target.files?.[0] || null
  knowledgeMessage.value = ''
}

async function handleUploadFile() {
  if (!selectedFile.value || isUploadingFile.value) {
    return
  }

  isUploadingFile.value = true
  knowledgeMessage.value = ''

  try {
    const result = await uploadKnowledgeFile(
      selectedFile.value,
    )

    if (result.status === 'duplicate') {
      knowledgeMessageType.value = 'info'
      knowledgeMessage.value =
        `文件“${result.filename}”已经存在，没有重复写入。`
    } else {
      knowledgeMessageType.value = 'success'
      knowledgeMessage.value =
        `文件“${result.filename}”上传成功，共写入 ${result.chunk_count} 个文档切片。`
    }

    selectedFile.value = null

    if (fileInput.value) {
      fileInput.value.value = ''
    }

    await loadKnowledgeFiles()
  } catch (error) {
    knowledgeMessageType.value = 'error'
    knowledgeMessage.value = error.message
  } finally {
    isUploadingFile.value = false
  }
}

async function handleDeleteKnowledgeFile(file) {
  if (!file || deletingFileId.value !== null) {
    return
  }

  const confirmed = window.confirm(
    `确定删除知识库文件“${file.filename}”吗？\n本地文件和对应向量数据都会被删除。`,
  )

  if (!confirmed) {
    return
  }

  deletingFileId.value = file.file_id
  knowledgeMessage.value = ''

  try {
    const result = await deleteKnowledgeFile(
      file.file_id,
    )

    knowledgeFiles.value =
      knowledgeFiles.value.filter(
        (item) => item.file_id !== file.file_id,
      )

    knowledgeMessageType.value = 'success'
    knowledgeMessage.value =
      `文件“${result.filename}”已删除，共删除 ${result.deleted_chunk_count} 个文档切片。`
  } catch (error) {
    knowledgeMessageType.value = 'error'
    knowledgeMessage.value = error.message
  } finally {
    deletingFileId.value = null
  }
}

onMounted(async () => {
  await Promise.all([
    checkBackend(),
    loadSessions(),
  ])
})
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-icon">M</div>

        <div>
          <div class="brand-name">MaintAI</div>
          <div class="brand-description">
            工业设备智能运维助手
          </div>
        </div>
      </div>

      <button
        class="new-session-button"
        :disabled="newSessionDisabled"
        :title="
          isCurrentSessionEmpty
            ? '当前已经是空白新会话'
            : '创建新对话'
        "
        @click="handleNewSession"
      >
        <span>＋</span>
        <span>
          {{
            isCreatingSession
              ? '正在创建'
              : isCurrentSessionEmpty
                ? '当前为新对话'
                : '新建对话'
          }}
        </span>
      </button>

      <div class="history-heading">
        历史会话
      </div>

      <div class="session-list">
        <div
          v-if="isLoadingSessions"
          class="sidebar-state"
        >
          正在加载会话……
        </div>

        <div
          v-else-if="sessions.length === 0"
          class="sidebar-state"
        >
          暂无历史会话
        </div>

        <div
          v-for="session in sessions"
          :key="session.id"
          class="session-item"
          :class="{
            active:
              activePage === 'chat' &&
              session.id === currentSessionId,
          }"
        >
          <button
            class="session-select-button"
            @click="selectSession(session)"
          >
            <span class="session-icon">●</span>

            <span class="session-information">
              <span class="session-title">
                {{ session.title }}
              </span>

              <span class="session-time">
                {{
                  formatTime(
                    session.updated_at ||
                      session.created_at,
                  )
                }}
              </span>
            </span>
          </button>

          <button
            class="session-delete-button"
            :disabled="
              deletingSessionId === session.id ||
              isSending
            "
            title="删除会话"
            @click.stop="handleDeleteSession(session)"
          >
            {{
              deletingSessionId === session.id
                ? '…'
                : '×'
            }}
          </button>
        </div>
      </div>

      <div class="sidebar-bottom">
        <button
          class="sidebar-page-button"
          :class="{ active: activePage === 'chat' }"
          @click="openChatPage"
        >
          <span>💬</span>
          <span>智能问答</span>
        </button>

        <button
          class="sidebar-page-button"
          :class="{
            active: activePage === 'knowledge',
          }"
          @click="openKnowledgePage"
        >
          <span>📚</span>
          <span>知识库管理</span>
        </button>
      </div>
    </aside>

    <main class="main-content">
      <template v-if="activePage === 'chat'">
        <header class="topbar">
          <div class="topbar-title-area">
            <div class="title-line">
              <template v-if="isEditingTitle">
                <input
                  ref="titleInput"
                  v-model="titleDraft"
                  class="title-edit-input"
                  maxlength="200"
                  @keydown.enter.prevent="saveTitle"
                  @keydown.esc.prevent="cancelTitleEdit"
                  @blur="saveTitle"
                />
              </template>

              <template v-else>
                <h1>
                  {{
                    currentSession?.title ||
                    '新对话'
                  }}
                </h1>

                <button
                  v-if="currentSession"
                  class="edit-title-button"
                  title="修改会话标题"
                  @click="startTitleEdit"
                >
                  ✎
                </button>
              </template>
            </div>

            <p>
              基于设备知识库进行故障分析与排查
            </p>
          </div>

          <div
            class="connection-status"
            :class="{
              online: isBackendOnline,
              offline: !isBackendOnline,
            }"
          >
            <span class="status-dot"></span>

            <span>
              {{
                isBackendOnline
                  ? 'FastAPI 服务已连接'
                  : 'FastAPI 服务未连接'
              }}
            </span>
          </div>
        </header>

        <section
          ref="messageContainer"
          class="message-container"
        >
          <div
            v-if="
              !isLoadingMessages &&
              messages.length === 0
            "
            class="empty-chat"
          >
            <div class="empty-chat-icon">⚙</div>
            <h2>你好，我是 MaintAI</h2>
            <p>
              你可以咨询工业设备故障、维修步骤和设备手册中的内容。
            </p>
          </div>

          <div
            v-if="isLoadingMessages"
            class="center-loading"
          >
            正在加载聊天记录……
          </div>

          <template v-else>
            <div
              v-for="message in messages"
              :key="message.id"
              class="message-row"
              :class="
                message.role === 'user'
                  ? 'user-message'
                  : 'assistant-message'
              "
            >
              <div class="message-column">
                <div class="message-role">
                  {{
                    message.role === 'user'
                      ? '你'
                      : 'MaintAI'
                  }}
                </div>

                <div class="message-bubble">
                  {{ message.content }}
                </div>

                <div class="message-time">
                  {{ formatTime(message.created_at) }}
                </div>
              </div>
            </div>

            <div
              v-if="isSending"
              class="message-row assistant-message"
            >
              <div class="message-column">
                <div class="message-role">
                  MaintAI
                </div>

                <div class="message-bubble loading-bubble">
                  <span></span>
                  <span></span>
                  <span></span>
                  正在分析问题
                </div>
              </div>
            </div>
          </template>
        </section>

        <div
          v-if="errorMessage"
          class="chat-error"
        >
          {{ errorMessage }}
        </div>

        <footer class="composer-area">
          <div class="composer">
            <textarea
              ref="messageInput"
              v-model="inputMessage"
              rows="1"
              :disabled="isSending"
              placeholder="请输入设备故障或维修问题……"
              @keydown.enter="handleInputKeydown"
            ></textarea>

            <button
              class="send-button"
              :disabled="
                !inputMessage.trim() || isSending
              "
              title="发送消息"
              @click="handleSendMessage"
            >
              ↑
            </button>
          </div>

          <div class="composer-tip">
            Enter 发送，Shift + Enter 换行。AI
            回答仅供辅助分析。
          </div>
        </footer>
      </template>

      <template v-else>
        <header class="topbar">
          <div class="topbar-title-area">
            <div class="title-line">
              <h1>知识库管理</h1>
            </div>

            <p>
              管理工业设备手册、检修记录和故障资料
            </p>
          </div>

          <button
            class="back-chat-button"
            @click="openChatPage"
          >
            返回智能问答
          </button>
        </header>

        <section class="knowledge-page">
          <div class="knowledge-notice">
            当前项目尚未接入登录与权限系统，因此这里管理的是所有用户共享的知识库。
          </div>

          <div class="knowledge-card upload-card">
            <div class="card-heading">
              <div>
                <h2>上传知识库文件</h2>
                <p>
                  文件上传后，后端会完成保存、文本切分和向量化。
                </p>
              </div>
            </div>

            <input
              ref="fileInput"
              class="hidden-file-input"
              type="file"
              accept=".pdf,.txt"
              @change="handleFileSelected"
            />

            <div class="upload-controls">
              <button
                class="select-file-button"
                :disabled="isUploadingFile"
                @click="openFileSelector"
              >
                选择文件
              </button>

              <div class="selected-file-name">
                {{
                  selectedFile
                    ? selectedFile.name
                    : '尚未选择文件'
                }}
              </div>

              <button
                class="upload-button"
                :disabled="
                  !selectedFile ||
                  isUploadingFile
                "
                @click="handleUploadFile"
              >
                {{
                  isUploadingFile
                    ? '正在处理……'
                    : '上传并写入知识库'
                }}
              </button>
            </div>

            <div
              v-if="knowledgeMessage"
              class="knowledge-message"
              :class="knowledgeMessageType"
            >
              {{ knowledgeMessage }}
            </div>
          </div>

          <div class="knowledge-card file-list-card">
            <div class="card-heading file-list-heading">
              <div>
                <h2>知识库文件</h2>
                <p>
                  当前共
                  {{ knowledgeFiles.length }}
                  个文件
                </p>
              </div>

              <button
                class="refresh-button"
                :disabled="isLoadingKnowledge"
                @click="loadKnowledgeFiles"
              >
                {{
                  isLoadingKnowledge
                    ? '正在刷新'
                    : '刷新列表'
                }}
              </button>
            </div>

            <div
              v-if="isLoadingKnowledge"
              class="knowledge-state"
            >
              正在读取知识库文件……
            </div>

            <div
              v-else-if="knowledgeFiles.length === 0"
              class="knowledge-state"
            >
              <div class="empty-file-icon">
                📄
              </div>
              <div>知识库中还没有文件</div>
            </div>

            <div
              v-else
              class="knowledge-file-list"
            >
              <article
                v-for="file in knowledgeFiles"
                :key="file.file_id"
                class="knowledge-file-item"
              >
                <div class="file-type-icon">
                  {{
                    file.filename
                      .toLowerCase()
                      .endsWith('.pdf')
                      ? 'PDF'
                      : 'TXT'
                  }}
                </div>

                <div class="file-information">
                  <div class="file-name">
                    {{ file.filename }}
                  </div>

                  <div class="file-metadata">
                    <span>
                      上传时间：
                      {{ formatTime(file.created_at) }}
                    </span>

                    <span
                      :title="file.file_id"
                    >
                      文件ID：
                      {{ shortFileId(file.file_id) }}
                    </span>
                  </div>
                </div>

                <button
                  class="delete-file-button"
                  :disabled="
                    deletingFileId === file.file_id
                  "
                  @click="
                    handleDeleteKnowledgeFile(file)
                  "
                >
                  {{
                    deletingFileId === file.file_id
                      ? '正在删除'
                      : '删除'
                  }}
                </button>
              </article>
            </div>
          </div>
        </section>
      </template>
    </main>
  </div>
</template>