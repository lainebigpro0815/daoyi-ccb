interface ElectronAPI {
  openFileDialog: (options?: any) => Promise<string[] | null>
  saveFileDialog: (options?: any) => Promise<string | null>
  openPath: (filePath: string) => Promise<string>
  getPath: (name: string) => Promise<string>
  getBackendUrl: () => Promise<string>
}

interface Window {
  electronAPI?: ElectronAPI
}
