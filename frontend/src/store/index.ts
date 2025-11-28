/**
 * Zustand 全局状态管理
 */
import { create } from 'zustand'

interface AppState {
  // 当前用户 (简化版，实际项目可扩展)
  currentUser: string
  setCurrentUser: (user: string) => void

  // 侧边栏折叠状态
  collapsed: boolean
  toggleCollapsed: () => void
}

export const useAppStore = create<AppState>((set) => ({
  currentUser: 'QA Engineer',
  setCurrentUser: (user) => set({ currentUser: user }),

  collapsed: false,
  toggleCollapsed: () => set((state) => ({ collapsed: !state.collapsed }))
}))

