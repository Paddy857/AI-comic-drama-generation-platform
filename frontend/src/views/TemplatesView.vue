<template>
  <div class="fade-in-up">
    <div class="page-header">
      <div>
        <h1 class="page-title">模板中心</h1>
        <p style="font-size:13px;color:var(--color-text-secondary);margin-top:4px">
          100+ 精品爆款模板，填空改字即可量产
        </p>
      </div>
    </div>

    <!-- Beginner Banner -->
    <div class="beginner-banner">
      <div class="banner-left">
        <div class="banner-icon">🎬</div>
        <div>
          <div class="banner-title">新人任务：完成 3 条量产，解锁全部高级模板</div>
          <div class="banner-sub">选一个新手推荐模板开始，30分钟即可完成</div>
        </div>
      </div>
      <el-progress :percentage="0" :stroke-width="10" style="width:200px" />
    </div>

    <!-- Category Tabs + Search -->
    <div class="filter-bar">
      <div class="cat-tabs">
        <div v-for="cat in categories" :key="cat"
          class="cat-tab" :class="{ active: selectedCat === cat }"
          @click="selectCat(cat)">
          {{ cat }}
        </div>
      </div>
      <div style="display:flex;gap:10px;align-items:center">
        <el-input v-model="keyword" placeholder="搜索模板..." prefix-icon="Search"
          style="width:200px" @keyup.enter="loadTemplates" clearable @clear="loadTemplates" />
        <el-select v-model="sortBy" style="width:140px" @change="loadTemplates">
          <el-option label="综合推荐" value="recommend" />
          <el-option label="最新上线" value="newest" />
          <el-option label="变量最少" value="var_count" />
        </el-select>
      </div>
    </div>

    <!-- Templates Grid -->
    <div v-if="loading" class="grid-4" style="margin-top:16px">
      <el-skeleton v-for="n in 8" :key="n" animated>
        <template #template>
          <el-skeleton-item variant="image" style="height:140px;border-radius:12px" />
          <el-skeleton-item variant="text" style="margin-top:10px" />
          <el-skeleton-item variant="text" style="width:60%" />
        </template>
      </el-skeleton>
    </div>

    <div class="grid-4" style="margin-top:16px" v-else-if="templates.length">
      <div class="template-card" v-for="t in templates" :key="t.id">
        <!-- Cover -->
        <div class="template-cover" :style="{ background: coverGradient(t) }">
          <span class="template-cover-text">{{ t.name.slice(0, 6) }}</span>
          <div class="fav-btn" @click.stop="toggleFav(t)">
            <el-icon :color="t.is_favorited ? '#f59e0b' : 'rgba(255,255,255,0.6)'">
              <Star />
            </el-icon>
          </div>
          <div v-if="t.is_beginner_friendly" class="beginner-badge">⭐ 新手友好</div>
        </div>
        <!-- Body -->
        <div class="template-body">
          <div class="template-name">{{ t.name }}</div>
          <div class="template-tags">
            <span v-if="t.is_beginner_friendly" class="tag beginner">新手友好</span>
            <span v-for="tag in (t.tags || []).slice(0,2)" :key="tag" class="tag">{{ tag }}</span>
          </div>
          <div class="template-stats">
            <span>📊 {{ t.avg_play || '--' }}</span>
            <span>⏱️ {{ Math.floor(t.total_duration_sec / 60) }}分钟</span>
            <span>🎭 {{ t.total_shots }}镜</span>
            <span>📝 {{ t.required_var_count }}个必填</span>
          </div>
        </div>
        <!-- Use button -->
        <div class="template-footer">
          <el-button type="primary" size="small" style="width:100%;border-radius:8px"
            @click="useTemplate(t)">使用此模板</el-button>
        </div>
      </div>
    </div>

    <div v-else class="empty-state" style="margin-top:40px">
      <div class="empty-icon">🔍</div>
      <div class="empty-text">没有找到匹配的模板</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { templatesApi } from '@/api'
import { ElMessage } from 'element-plus'
import { Star } from '@element-plus/icons-vue'

const router = useRouter()
const templates = ref([])
const categories = ref(['全部', '新手推荐', '热门爆款', '都市', '古风', '甜宠', '悬疑', '玄幻', '校园', '末世'])
const selectedCat = ref('新手推荐')
const keyword = ref('')
const sortBy = ref('recommend')
const loading = ref(false)

const GRADIENTS = [
  'linear-gradient(135deg,#667eea,#764ba2)',
  'linear-gradient(135deg,#f093fb,#f5576c)',
  'linear-gradient(135deg,#4facfe,#00f2fe)',
  'linear-gradient(135deg,#43e97b,#38f9d7)',
  'linear-gradient(135deg,#fa709a,#fee140)',
  'linear-gradient(135deg,#a18cd1,#fbc2eb)',
  'linear-gradient(135deg,#ffecd2,#fcb69f)',
  'linear-gradient(135deg,#a1c4fd,#c2e9fb)',
]
function coverGradient(t) { return GRADIENTS[t.id % GRADIENTS.length] }

function selectCat(cat) {
  selectedCat.value = cat
  loadTemplates()
}

async function loadTemplates() {
  loading.value = true
  try {
    templates.value = await templatesApi.list({
      category: selectedCat.value,
      keyword: keyword.value || undefined,
      sort_by: sortBy.value,
    })
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

async function toggleFav(t) {
  try {
    const res = await templatesApi.toggleFavorite(t.id)
    t.is_favorited = res.is_favorited
    ElMessage.success(res.message)
  } catch (e) {
    ElMessage.error(e.message)
  }
}

function useTemplate(t) {
  router.push(`/templates/${t.id}/workspace`)
}

onMounted(loadTemplates)
</script>

<style scoped>
.beginner-banner {
  background: linear-gradient(135deg,#6366f1,#4f46e5);
  border-radius: var(--radius-md);
  padding: 18px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  color: #fff;
}

.banner-left { display: flex; align-items: center; gap: 16px; }
.banner-icon { font-size: 32px; }
.banner-title { font-size: 15px; font-weight: 700; margin-bottom: 4px; }
.banner-sub { font-size: 12px; opacity: 0.8; }

.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.cat-tabs { display: flex; gap: 4px; flex-wrap: wrap; }
.cat-tab {
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
  cursor: pointer;
  color: var(--color-text-secondary);
  transition: all 0.2s;
  font-weight: 500;
}
.cat-tab.active {
  background: var(--color-primary);
  color: #fff;
  font-weight: 600;
}
.cat-tab:hover:not(.active) { background: #f1f3f9; color: var(--color-text-primary); }

.fav-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(0,0,0,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  backdrop-filter: blur(4px);
  transition: all 0.2s;
}
.fav-btn:hover { background: rgba(0,0,0,0.35); transform: scale(1.1); }

.beginner-badge {
  position: absolute;
  bottom: 8px;
  left: 8px;
  background: rgba(16,185,129,0.9);
  color: #fff;
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 20px;
  font-weight: 600;
}

.template-footer {
  padding: 0 14px 14px;
}
</style>
