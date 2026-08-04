<template>
  <div class="fade-in-up">
    <div class="page-header">
      <h1 class="page-title">角色库</h1>
      <div style="display:flex;gap:10px">
        <el-input v-model="keyword" placeholder="搜索角色..." prefix-icon="Search"
          style="width:220px" @keyup.enter="loadCharacters" clearable @clear="loadCharacters" />
        <el-button type="primary" :icon="Plus" @click="createDialogVisible=true">添加角色</el-button>
      </div>
    </div>

    <div class="grid-5" v-if="characters.length">
      <!-- Characters -->
      <div class="character-card" v-for="c in characters" :key="c.id"
        @click="editCharacter(c)">
        <div class="character-avatar">{{ c.name[0] }}</div>
        <div class="character-name">{{ c.name }}</div>
        <div class="character-role">{{ c.role_label || roleLabel(c.role_type) }} · {{ c.project_name || '全局' }}</div>
        <div v-if="c.appearance" class="character-appearance">{{ c.appearance }}</div>
        <div class="char-actions">
          <el-button text size="small" type="danger" :icon="Delete"
            @click.stop="deleteCharacter(c)"></el-button>
        </div>
      </div>

      <!-- Add new card -->
      <div class="character-card add-char-card" @click="createDialogVisible=true">
        <div class="character-avatar" style="background:linear-gradient(135deg,#e2e8f0,#cbd5e1);color:#64748b">
          +
        </div>
        <div class="character-name" style="color:var(--color-text-secondary)">添加新角色</div>
        <div class="character-role">点击创建</div>
      </div>
    </div>

    <div v-else class="empty-state">
      <div class="empty-icon">👤</div>
      <div class="empty-text">角色库为空，创建你的第一个角色</div>
      <el-button type="primary" :icon="Plus" @click="createDialogVisible=true">添加角色</el-button>
    </div>

    <!-- Create/Edit Dialog -->
    <el-dialog v-model="createDialogVisible"
      :title="editingChar ? '编辑角色' : '添加新角色'"
      width="500px">
      <el-form :model="charForm" label-position="top">
        <el-form-item label="角色名字 *">
          <el-input v-model="charForm.name" placeholder="如：李星河、苏小沫" maxlength="30" />
        </el-form-item>
        <el-form-item label="角色类型">
          <el-radio-group v-model="charForm.role_type">
            <el-radio-button value="main">主角</el-radio-button>
            <el-radio-button value="female_main">女主角</el-radio-button>
            <el-radio-button value="villain">反派</el-radio-button>
            <el-radio-button value="supporting">配角</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="所属项目">
          <el-input v-model="charForm.project_name" placeholder="如：赛博江湖（可选）" />
        </el-form-item>
        <el-form-item label="外貌描述">
          <el-input v-model="charForm.appearance" type="textarea" :rows="3"
            placeholder="如：剑眉星目，气宇轩昂，身着青色长袍..." maxlength="300" show-word-limit />
        </el-form-item>
        <el-form-item label="性格特点">
          <el-input v-model="charForm.personality" type="textarea" :rows="2"
            placeholder="如：外冷内热，重情重义..." maxlength="200" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible=false; editingChar=null">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveCharacter">
          {{ editingChar ? '保存修改' : '创建角色' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { charactersApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'

const characters = ref([])
const keyword = ref('')
const createDialogVisible = ref(false)
const saving = ref(false)
const editingChar = ref(null)

const defaultForm = () => ({
  name: '', role_type: 'main', role_label: '', project_name: '', appearance: '', personality: ''
})
const charForm = ref(defaultForm())

const ROLE_LABELS = { main: '主角', female_main: '女主角', villain: '反派', supporting: '配角' }
function roleLabel(type) { return ROLE_LABELS[type] || type }

async function loadCharacters() {
  try {
    characters.value = await charactersApi.list({ keyword: keyword.value || undefined })
  } catch (e) { ElMessage.error(e.message) }
}

function editCharacter(c) {
  editingChar.value = c
  charForm.value = {
    name: c.name, role_type: c.role_type, role_label: c.role_label || '',
    project_name: c.project_name || '', appearance: c.appearance || '', personality: c.personality || '',
  }
  createDialogVisible.value = true
}

async function saveCharacter() {
  if (!charForm.value.name.trim()) {
    ElMessage.warning('请输入角色名字')
    return
  }
  saving.value = true
  try {
    if (editingChar.value) {
      await charactersApi.update(editingChar.value.id, charForm.value)
      ElMessage.success('角色已更新')
    } else {
      await charactersApi.create(charForm.value)
      ElMessage.success('角色已创建')
    }
    createDialogVisible.value = false
    editingChar.value = null
    charForm.value = defaultForm()
    await loadCharacters()
  } catch (e) {
    ElMessage.error(e.message)
  } finally { saving.value = false }
}

async function deleteCharacter(c) {
  try {
    await ElMessageBox.confirm(`确定删除角色"${c.name}"吗？`, '删除确认', {
      type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消'
    })
    await charactersApi.delete(c.id)
    ElMessage.success('角色已删除')
    await loadCharacters()
  } catch {}
}

onMounted(loadCharacters)
</script>

<style scoped>
.character-appearance {
  font-size: 11px;
  color: var(--color-text-secondary);
  margin-top: 4px;
  line-height: 1.4;
  max-height: 36px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.char-actions {
  margin-top: 8px;
  opacity: 0;
  transition: opacity 0.2s;
}

.character-card:hover .char-actions { opacity: 1; }

.add-char-card { border: 2px dashed var(--color-border); }
.add-char-card:hover { border-color: var(--color-primary); }
</style>
