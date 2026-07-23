import { app, BrowserWindow, ipcMain, dialog, shell } from 'electron'
import { spawn, ChildProcess } from 'child_process'
import path from 'path'
import fs from 'fs'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// vite-plugin-electron 注入的 dev server URL
const VITE_DEV_SERVER_URL = process.env.VITE_DEV_SERVER_URL
const isDev = !!VITE_DEV_SERVER_URL || !app.isPackaged

let mainWindow: BrowserWindow | null = null
let pythonProcess: ChildProcess | null = null

const BACKEND_PORT = 8000
const BACKEND_URL = `http://localhost:${BACKEND_PORT}`

console.log(`[Electron] isDev=${isDev}, VITE_DEV_SERVER_URL=${VITE_DEV_SERVER_URL}`)

function getPythonExe(): string {
  if (isDev) {
    return 'python'
  }
  const ext = process.platform === 'win32' ? '.exe' : ''
  return path.join(process.resourcesPath, `ccb-backend${ext}`)
}

function getBackendDataDir(): string {
  const userData = app.getPath('userData')
  const dataDir = path.join(userData, 'data')
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true })
  }
  return dataDir
}

function startPythonBackend(): void {
  if (pythonProcess) return

  const cwd = isDev
    ? path.resolve(__dirname, '..', '..', 'backend')
    : process.resourcesPath

  const dataDir = getBackendDataDir()
  const env = {
    ...process.env,
    DATA_DIR: dataDir,
  }

  const args = ['-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', String(BACKEND_PORT)]

  console.log(`[Electron] Starting Python: cwd=${cwd}, args=${args.join(' ')}`)

  pythonProcess = spawn(getPythonExe(), args, { cwd, env, stdio: ['ignore', 'pipe', 'pipe'] })

  pythonProcess.stdout?.on('data', (data: Buffer) => {
    console.log(`[Python] ${data.toString().trim()}`)
  })

  pythonProcess.stderr?.on('data', (data: Buffer) => {
    console.error(`[Python ERR] ${data.toString().trim()}`)
  })

  pythonProcess.on('exit', (code) => {
    console.log(`[Python] exited code=${code}`)
    pythonProcess = null
    if (!isDev && code !== 0) {
      setTimeout(startPythonBackend, 2000)
    }
  })
}

function stopPythonBackend(): void {
  if (pythonProcess) {
    pythonProcess.kill('SIGTERM')
    pythonProcess = null
  }
}

async function waitForBackend(maxRetries = 20): Promise<boolean> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const res = await fetch(`${BACKEND_URL}/docs`)
      if (res.ok) {
        console.log(`[Electron] Backend ready after ${i + 1}s`)
        return true
      }
    } catch {
      // not ready yet
    }
    await new Promise(r => setTimeout(r, 1000))
  }
  console.error('[Electron] Backend failed to start')
  return false
}

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    show: false,
  })

  if (isDev && VITE_DEV_SERVER_URL) {
    console.log(`[Electron] Loading dev URL: ${VITE_DEV_SERVER_URL}`)
    mainWindow.loadURL(VITE_DEV_SERVER_URL)
    mainWindow.webContents.openDevTools()
  } else {
    const distIndex = path.join(__dirname, '..', 'dist', 'index.html')
    console.log(`[Electron] Loading production file: ${distIndex}`)
    mainWindow.loadFile(distIndex)
  }

  mainWindow.once('ready-to-show', () => {
    console.log('[Electron] Window ready-to-show')
    mainWindow?.show()
  })

  mainWindow.webContents.on('did-fail-load', (_event, code, desc) => {
    console.error(`[Electron] Failed to load: code=${code}, desc=${desc}`)
  })

  mainWindow.webContents.on('console-message', (_event, level, message) => {
    console.log(`[Renderer] ${message}`)
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

// ── IPC Handlers ──

ipcMain.handle('dialog:openFile', async (_event, options) => {
  if (!mainWindow) return null
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile', 'multiSelections'],
    filters: options?.filters ?? [
      { name: '文档', extensions: ['doc', 'docx', 'xls', 'xlsx', 'pdf', 'txt', 'md'] },
      { name: '所有文件', extensions: ['*'] },
    ],
  })
  return result.canceled ? null : result.filePaths
})

ipcMain.handle('dialog:saveFile', async (_event, options) => {
  if (!mainWindow) return null
  const result = await dialog.showSaveDialog(mainWindow, {
    filters: options?.filters ?? [{ name: '所有文件', extensions: ['*'] }],
  })
  return result.canceled ? null : result.filePath
})

ipcMain.handle('shell:openPath', async (_event, filePath: string) => {
  return shell.openPath(filePath)
})

ipcMain.handle('app:getPath', (_event, name: Parameters<typeof app.getPath>[0]) => {
  return app.getPath(name)
})

ipcMain.handle('app:getBackendUrl', () => {
  return BACKEND_URL
})

// ── App Lifecycle ──

app.whenReady().then(async () => {
  // dev 模式：concurrently 已启动后端
  // prod 模式：Electron 自启 Python sidecar
  if (!isDev) {
    startPythonBackend()
  }

  const backendReady = await waitForBackend()
  if (!backendReady) {
    console.error('[Electron] Starting window anyway despite backend failure')
  }

  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('before-quit', () => {
  stopPythonBackend()
})
