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
  const contentType = response.headers.get('content-type') || ''

  if (response.status !== 204) {
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

export function getKnowledgeFiles() {
  return request('/knowledge/files')
}

export function uploadKnowledgeFile(file) {
  const formData = new FormData()
  formData.append('file', file)

  return request('/knowledge/upload', {
    method: 'POST',
    body: formData,
  })
}

export function deleteKnowledgeFile(fileId) {
  return request(
    `/knowledge/files/${encodeURIComponent(fileId)}`,
    {
      method: 'DELETE',
    },
  )
}