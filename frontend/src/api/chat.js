const API_BASE_URL = 'http://127.0.0.1:8000/api'

function getErrorMessage(data, statusCode) {
  if (typeof data === 'string' && data) {
    return data
  }

  if (typeof data?.detail === 'string') {
    return data.detail
  }

  if (Array.isArray(data?.detail)) {
    return data.detail
      .map((item) => item.msg || '请求参数错误')
      .join('；')
  }

  return `请求失败，状态码：${statusCode}`
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options)

  let data = null

  if (response.status !== 204) {
    const contentType = response.headers.get('content-type') || ''

    if (contentType.includes('application/json')) {
      data = await response.json()
    } else {
      data = await response.text()
    }
  }

  if (!response.ok) {
    throw new Error(getErrorMessage(data, response.status))
  }

  return data
}

function createJsonOptions(method, body) {
  return {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  }
}

export function createChatSession(userId, title = '新对话') {
  return request(
    '/chat/sessions',
    createJsonOptions('POST', {
      user_id: userId,
      title,
    }),
  )
}

export function getChatSessions(userId) {
  const query = new URLSearchParams({
    user_id: String(userId),
  })

  return request(`/chat/sessions?${query.toString()}`)
}

export function getChatMessages(sessionId, userId) {
  const query = new URLSearchParams({
    user_id: String(userId),
  })

  return request(
    `/chat/sessions/${sessionId}/messages?${query.toString()}`,
  )
}

export function sendChatMessage(sessionId, userId, content) {
  return request(
    `/chat/sessions/${sessionId}/chat`,
    createJsonOptions('POST', {
      user_id: userId,
      content,
    }),
  )
}

export function updateChatSessionTitle(sessionId, userId, title) {
  const query = new URLSearchParams({
    user_id: String(userId),
  })

  return request(
    `/chat/sessions/${sessionId}?${query.toString()}`,
    createJsonOptions('PATCH', {
      title,
    }),
  )
}

export function deleteChatSession(sessionId, userId) {
  const query = new URLSearchParams({
    user_id: String(userId),
  })

  return request(`/chat/sessions/${sessionId}?${query.toString()}`, {
    method: 'DELETE',
  })
}