import { app, ipcMain, shell, BrowserWindow, dialog } from "electron";
import { spawn } from "child_process";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";
const __filename$1 = fileURLToPath(import.meta.url);
const __dirname$1 = path.dirname(__filename$1);
const VITE_DEV_SERVER_URL = process.env.VITE_DEV_SERVER_URL;
const isDev = !!VITE_DEV_SERVER_URL || !app.isPackaged;
let mainWindow = null;
let pythonProcess = null;
const BACKEND_PORT = 8e3;
const BACKEND_URL = `http://localhost:${BACKEND_PORT}`;
console.log(`[Electron] isDev=${isDev}, VITE_DEV_SERVER_URL=${VITE_DEV_SERVER_URL}`);
function getPythonExe() {
  if (isDev) {
    return "python";
  }
  const ext = process.platform === "win32" ? ".exe" : "";
  return path.join(process.resourcesPath, `ccb-backend${ext}`);
}
function getBackendDataDir() {
  const userData = app.getPath("userData");
  const dataDir = path.join(userData, "data");
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }
  return dataDir;
}
function startPythonBackend() {
  var _a, _b;
  if (pythonProcess) return;
  const cwd = isDev ? path.resolve(__dirname$1, "..", "..", "backend") : process.resourcesPath;
  const dataDir = getBackendDataDir();
  const env = {
    ...process.env,
    DATA_DIR: dataDir
  };
  const args = ["-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", String(BACKEND_PORT)];
  console.log(`[Electron] Starting Python: cwd=${cwd}, args=${args.join(" ")}`);
  pythonProcess = spawn(getPythonExe(), args, { cwd, env, stdio: ["ignore", "pipe", "pipe"] });
  (_a = pythonProcess.stdout) == null ? void 0 : _a.on("data", (data) => {
    console.log(`[Python] ${data.toString().trim()}`);
  });
  (_b = pythonProcess.stderr) == null ? void 0 : _b.on("data", (data) => {
    console.error(`[Python ERR] ${data.toString().trim()}`);
  });
  pythonProcess.on("exit", (code) => {
    console.log(`[Python] exited code=${code}`);
    pythonProcess = null;
    if (!isDev && code !== 0) {
      setTimeout(startPythonBackend, 2e3);
    }
  });
}
function stopPythonBackend() {
  if (pythonProcess) {
    pythonProcess.kill("SIGTERM");
    pythonProcess = null;
  }
}
async function waitForBackend(maxRetries = 20) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const res = await fetch(`${BACKEND_URL}/docs`);
      if (res.ok) {
        console.log(`[Electron] Backend ready after ${i + 1}s`);
        return true;
      }
    } catch {
    }
    await new Promise((r) => setTimeout(r, 1e3));
  }
  console.error("[Electron] Backend failed to start");
  return false;
}
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    webPreferences: {
      preload: path.join(__dirname$1, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false
    },
    show: false
  });
  if (isDev && VITE_DEV_SERVER_URL) {
    console.log(`[Electron] Loading dev URL: ${VITE_DEV_SERVER_URL}`);
    mainWindow.loadURL(VITE_DEV_SERVER_URL);
    mainWindow.webContents.openDevTools();
  } else {
    const distIndex = path.join(__dirname$1, "..", "dist", "index.html");
    console.log(`[Electron] Loading production file: ${distIndex}`);
    mainWindow.loadFile(distIndex);
  }
  mainWindow.once("ready-to-show", () => {
    console.log("[Electron] Window ready-to-show");
    mainWindow == null ? void 0 : mainWindow.show();
  });
  mainWindow.webContents.on("did-fail-load", (_event, code, desc) => {
    console.error(`[Electron] Failed to load: code=${code}, desc=${desc}`);
  });
  mainWindow.webContents.on("console-message", (_event, level, message) => {
    console.log(`[Renderer] ${message}`);
  });
  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}
ipcMain.handle("dialog:openFile", async (_event, options) => {
  if (!mainWindow) return null;
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ["openFile", "multiSelections"],
    filters: (options == null ? void 0 : options.filters) ?? [
      { name: "文档", extensions: ["doc", "docx", "xls", "xlsx", "pdf", "txt", "md"] },
      { name: "所有文件", extensions: ["*"] }
    ]
  });
  return result.canceled ? null : result.filePaths;
});
ipcMain.handle("dialog:saveFile", async (_event, options) => {
  if (!mainWindow) return null;
  const result = await dialog.showSaveDialog(mainWindow, {
    filters: (options == null ? void 0 : options.filters) ?? [{ name: "所有文件", extensions: ["*"] }]
  });
  return result.canceled ? null : result.filePath;
});
ipcMain.handle("shell:openPath", async (_event, filePath) => {
  return shell.openPath(filePath);
});
ipcMain.handle("app:getPath", (_event, name) => {
  return app.getPath(name);
});
ipcMain.handle("app:getBackendUrl", () => {
  return BACKEND_URL;
});
app.whenReady().then(async () => {
  if (!isDev) {
    startPythonBackend();
  }
  const backendReady = await waitForBackend();
  if (!backendReady) {
    console.error("[Electron] Starting window anyway despite backend failure");
  }
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});
app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
app.on("before-quit", () => {
  stopPythonBackend();
});
