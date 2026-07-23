const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  openFileDialog: (options) => ipcRenderer.invoke('dialog:openFile', options),
  saveFileDialog: (options) => ipcRenderer.invoke('dialog:saveFile', options),
  openPath: (filePath) => ipcRenderer.invoke('shell:openPath', filePath),
  getPath: (name) => ipcRenderer.invoke('app:getPath', name),
  getBackendUrl: () => ipcRenderer.invoke('app:getBackendUrl'),
})
