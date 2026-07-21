export interface Product {
  id: number
  name: string
  code: string
  description: string
  sort_order: number
}

import api from './index'

export async function fetchProducts(): Promise<Product[]> {
  const res = await api.get('/products')
  return res.data.items
}
