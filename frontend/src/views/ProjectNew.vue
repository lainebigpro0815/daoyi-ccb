<template>
  <div style="max-width: 700px; margin: 0 auto;">
    <div class="page-header">
      <h1>新建项目</h1>
    </div>

    <el-form :model="form" label-width="100px" v-loading="submitting">
      <el-form-item label="项目名称" required>
        <el-input v-model="form.name" placeholder="请输入项目名称" />
      </el-form-item>

      <el-form-item label="客户名称">
        <el-input v-model="form.customer_name" placeholder="请输入客户名称" />
      </el-form-item>

      <el-form-item label="项目阶段" required>
        <el-select v-model="form.stage" style="width: 100%">
          <el-option label="售前" value="presale" />
          <el-option label="已签约" value="signed" />
          <el-option label="执行中" value="executing" />
          <el-option label="已交付" value="delivered" />
          <el-option label="已归档" value="archived" />
        </el-select>
      </el-form-item>

      <el-form-item label="启动日期" required>
        <el-date-picker v-model="form.start_date" type="date" placeholder="选择日期"
                        value-format="YYYY-MM-DD" style="width: 100%" />
      </el-form-item>

      <el-form-item label="产品组合" required>
        <el-checkbox-group v-model="form.product_ids">
          <div v-for="p in products" :key="p.id" style="margin-bottom: 8px;">
            <el-checkbox :label="p.id" :value="p.id">
              <span style="font-weight: 500;">{{ p.name }}</span>
              <span style="color: #999; font-size: 12px; margin-left: 8px;">{{ p.description }}</span>
            </el-checkbox>
          </div>
        </el-checkbox-group>
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="handleSubmit" :disabled="!isValid">
          {{ submitting ? '创建中...' : '创建项目 & 生成计划' }}
        </el-button>
        <el-button @click="$router.push('/')">取消</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchProducts, type Product } from '@/api/products'
import { createProject } from '@/api/projects'

const router = useRouter()
const products = ref<Product[]>([])
const submitting = ref(false)

const form = ref({
  name: '',
  customer_name: '',
  stage: 'signed',
  start_date: '',
  product_ids: [] as number[],
})

const isValid = computed(() => form.value.name && form.value.start_date && form.value.product_ids.length > 0)

onMounted(async () => {
  try {
    products.value = await fetchProducts()
  } catch {
    ElMessage.error('加载产品列表失败')
  }
})

async function handleSubmit() {
  if (!isValid.value) return
  submitting.value = true
  try {
    const project = await createProject({
      name: form.value.name,
      customer_name: form.value.customer_name,
      stage: form.value.stage,
      start_date: form.value.start_date,
      product_ids: form.value.product_ids,
    })
    ElMessage.success('项目创建成功，计划已生成！')
    router.push(`/projects/${project.id}`)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '创建失败')
  } finally {
    submitting.value = false
  }
}
</script>
