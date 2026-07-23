import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('electronAPI', {
  openFileDialog: (options?: any) =>
    ipcRenderer.invoke('dialog:openFile', options),

  saveFileDialog: (options?: any) =>
    ipcRenderer.invoke('dialog:saveFile', options),

  openPath: (filePath: string) =>
    ipcRenderer.invoke('shell:openPath', filePath),

  getPath: (name: string) =>
    ipcRenderer.invoke('app:getPath', name),

  getBackendUrl: () =>
    ipcRenderer.invoke('app:getBackendUrl'),
})
